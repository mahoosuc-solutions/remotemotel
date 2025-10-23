"""Async helpers for interacting with the knowledge base in Postgres."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import asyncpg
from openai import AsyncOpenAI

DEFAULT_CHUNK_SIZE = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "350"))
DEFAULT_EMBED_MODEL = os.getenv("KNOWLEDGE_EMBED_MODEL", "text-embedding-3-small")
DEFAULT_HOTEL_ID = os.getenv("HOTEL_ID", "stayhive")
DEFAULT_TOP_K = int(os.getenv("KNOWLEDGE_TOP_K", "5"))


@dataclass
class KnowledgeDocument:
    id: str
    title: Optional[str]
    source: str
    updated_at: str
    tags: List[str]


class KnowledgeService:
    """High-level async API for the hotel knowledge base."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        embed_model: str = DEFAULT_EMBED_MODEL,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required for knowledge operations")

        self.embed_model = embed_model
        self.chunk_size = chunk_size
        self._openai_client = AsyncOpenAI()

    async def _connect(self) -> asyncpg.Connection:
        return await asyncpg.connect(self.database_url)

    def chunk_text(self, text: str) -> List[str]:
        tokens = text.split()
        if not tokens:
            return []
        return [
            " ".join(tokens[i : i + self.chunk_size])
            for i in range(0, len(tokens), self.chunk_size)
        ]

    async def embed(self, chunks: Iterable[str]) -> List[List[float]]:
        chunk_list = list(chunks)
        if not chunk_list:
            return []
        response = await self._openai_client.embeddings.create(
            input=chunk_list,
            model=self.embed_model,
        )
        return [item.embedding for item in response.data]

    async def ingest_document(
        self,
        hotel_id: str,
        source: str,
        title: Optional[str],
        body: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        chunks = self.chunk_text(body)
        embeddings = await self.embed(chunks)

        conn = await self._connect()
        try:
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM knowledge.documents WHERE hotel_id = $1 AND source = $2",
                    hotel_id,
                    source,
                )

                document_id = await conn.fetchval(
                    """
                    INSERT INTO knowledge.documents (hotel_id, source, title, body, tags)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    hotel_id,
                    source,
                    title,
                    body,
                    tags or [],
                )

                for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = await conn.fetchval(
                        """
                        INSERT INTO knowledge.chunks (
                            document_id, hotel_id, chunk_index, content, metadata
                        )
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id
                        """,
                        document_id,
                        hotel_id,
                        index,
                        chunk,
                        metadata or {},
                    )

                    await conn.execute(
                        "INSERT INTO knowledge.embeddings (chunk_id, embedding) VALUES ($1, $2)",
                        chunk_id,
                        embedding,
                    )

            return str(document_id)
        finally:
            await conn.close()

    async def list_documents(self, hotel_id: str, limit: int = 20) -> List[KnowledgeDocument]:
        conn = await self._connect()
        try:
            rows = await conn.fetch(
                """
                SELECT id::text, title, source, updated_at::text, tags
                FROM knowledge.documents
                WHERE hotel_id = $1
                ORDER BY updated_at DESC
                LIMIT $2
                """,
                hotel_id,
                limit,
            )
            return [
                KnowledgeDocument(
                    id=row[0],
                    title=row[1],
                    source=row[2],
                    updated_at=row[3],
                    tags=row[4] or [],
                )
                for row in rows
            ]
        finally:
            await conn.close()

    async def semantic_search(
        self,
        hotel_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[Dict[str, Any]]:
        embedding = (await self.embed([query]))[0]
        conn = await self._connect()
        try:
            rows = await conn.fetch(
                """
                SELECT content, metadata, similarity
                FROM knowledge.semantic_search($1, $2::vector, $3)
                """,
                hotel_id,
                embedding,
                top_k,
            )
            return [
                {
                    "content": row[0],
                    "metadata": row[1] or {},
                    "similarity": float(row[2]),
                }
                for row in rows
            ]
        finally:
            await conn.close()


async def ingest_file(
    path: str,
    hotel_id: str = DEFAULT_HOTEL_ID,
    source: Optional[str] = None,
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    service: Optional[KnowledgeService] = None,
) -> str:
    service = service or KnowledgeService()
    text = Path(path).read_text()
    return await service.ingest_document(
        hotel_id=hotel_id,
        source=source or path,
        title=title or Path(path).name,
        body=text,
        tags=tags,
    )
