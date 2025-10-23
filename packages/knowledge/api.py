"""FastAPI routes for managing knowledge base content."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from packages.knowledge.service import DEFAULT_HOTEL_ID, KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class IngestRequest(BaseModel):
    hotel_id: str = Field(default=DEFAULT_HOTEL_ID)
    source: Optional[str] = Field(default=None, description="Source identifier")
    title: Optional[str] = Field(default=None, description="Document title")
    body: str = Field(..., description="Document contents")
    tags: Optional[List[str]] = Field(default=None)


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: Optional[str]
    source: str
    updated_at: str
    tags: List[str]


@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
async def list_documents(limit: int = 20, hotel_id: str = DEFAULT_HOTEL_ID):
    try:
        service = KnowledgeService()
        documents = await service.list_documents(hotel_id=hotel_id, limit=limit)
        return [doc.__dict__ for doc in documents]
    except Exception as exc:  # pragma: no cover - DB connectivity
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ingest")
async def ingest_document(payload: IngestRequest):
    try:
        service = KnowledgeService()
        document_id = await service.ingest_document(
            hotel_id=payload.hotel_id,
            source=payload.source or "api",
            title=payload.title,
            body=payload.body,
            tags=payload.tags,
        )
        return {"document_id": document_id}
    except Exception as exc:  # pragma: no cover - external failure
        raise HTTPException(status_code=500, detail=str(exc)) from exc
