import asyncio
from types import SimpleNamespace

import pytest

from packages.knowledge.service import KnowledgeDocument, KnowledgeService


class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        self.connection.in_transaction = True
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        self.connection.in_transaction = False


class FakeConnection:
    def __init__(self):
        self.fetchval_calls = []
        self.execute_calls = []
        self.in_transaction = False
        self._doc_counter = 0
        self._chunk_counter = 0

    async def fetchval(self, query, *params):
        self.fetchval_calls.append((query.strip(), params))
        if "INSERT INTO knowledge.documents" in query:
            self._doc_counter += 1
            return f"doc-{self._doc_counter}"
        if "INSERT INTO knowledge.chunks" in query:
            self._chunk_counter += 1
            return f"chunk-{self._chunk_counter}"
        return None

    async def fetch(self, query, *params):
        self.fetch_calls = getattr(self, "fetch_calls", [])
        self.fetch_calls.append((query.strip(), params))
        return [
            (
                "doc-1",
                "Welcome",
                "docs/welcome.md",
                "2025-01-01T00:00:00Z",
                ["policy", "general"],
            )
        ]

    async def execute(self, query, *params):
        self.execute_calls.append((query.strip(), params))

    def transaction(self):
        return FakeTransaction(self)

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_reingest_document_replaces_existing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = KnowledgeService(
        database_url="postgresql://user:pass@localhost/testdb",
    )

    fake_conn = FakeConnection()

    async def fake_connect():
        return fake_conn

    async def fake_embed(chunks):
        return [[0.1, 0.2]] * len(chunks)

    monkeypatch.setattr(service, "_connect", fake_connect)
    monkeypatch.setattr(service, "embed", fake_embed)

    monkeypatch.setattr(service, "chunk_text", lambda text: [text])

    await service.ingest_document(
        hotel_id="stayhive",
        source="docs/policies.md",
        title="Policies",
        body="First version",
    )

    await service.ingest_document(
        hotel_id="stayhive",
        source="docs/policies.md",
        title="Policies",
        body="Second version",
    )

    delete_calls = [
        call
        for call in fake_conn.execute_calls
        if "DELETE FROM knowledge.documents" in call[0]
    ]
    assert delete_calls, "expected knowledge ingestion to delete existing document"


@pytest.mark.asyncio
async def test_ingest_document_inserts_chunks(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = KnowledgeService(
        database_url="postgresql://user:pass@localhost/testdb",
        chunk_size=2,
    )

    fake_conn = FakeConnection()

    async def fake_connect():
        return fake_conn

    async def fake_embed(chunks):
        return [[0.1, 0.2]] * len(chunks)

    monkeypatch.setattr(service, "_connect", fake_connect)
    monkeypatch.setattr(service, "embed", fake_embed)

    chunks_captured = []

    def fake_chunk_text(text):
        chunks = text.split(".")
        chunks_captured.extend(chunks)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    monkeypatch.setattr(service, "chunk_text", fake_chunk_text)

    document_id = await service.ingest_document(
        hotel_id="stayhive",
        source="docs/policies.md",
        title="Policies",
        body="Check-in at 4 PM. Checkout by 10 AM.",
        tags=["policy"],
    )

    assert document_id == "doc-1"
    assert any(
        "INSERT INTO knowledge.documents" in call[0]
        for call in fake_conn.fetchval_calls
    )
    chunk_queries = [
        call for call in fake_conn.fetchval_calls if "knowledge.chunks" in call[0]
    ]
    trimmed_chunks = [chunk.strip() for chunk in chunks_captured if chunk.strip()]
    expected_chunk_count = len(trimmed_chunks)
    assert len(chunk_queries) == expected_chunk_count
    assert all(
        isinstance(params[3], str) and params[3] in trimmed_chunks
        for _, params in chunk_queries
    )
    assert fake_conn.execute_calls  # embeddings inserted


@pytest.mark.asyncio
async def test_list_documents_returns_models(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = KnowledgeService(
        database_url="postgresql://user:pass@localhost/testdb",
    )

    fake_conn = FakeConnection()

    async def fake_connect():
        return fake_conn

    monkeypatch.setattr(service, "_connect", fake_connect)

    documents = await service.list_documents(hotel_id="stayhive", limit=10)

    assert len(documents) == 1
    doc = documents[0]
    assert isinstance(doc, KnowledgeDocument)
    assert doc.title == "Welcome"
