from types import SimpleNamespace

import pytest
import httpx
from fastapi import FastAPI

from packages.knowledge.api import router as knowledge_router


@pytest.fixture()
def test_app():
    app = FastAPI()
    app.include_router(knowledge_router)
    return app


@pytest.mark.asyncio
async def test_list_documents_endpoint(monkeypatch, test_app):
    class FakeService:
        async def list_documents(self, hotel_id: str, limit: int):
            return [
                SimpleNamespace(
                    id="doc-1",
                    title="Welcome",
                    source="docs/welcome.md",
                    updated_at="2025-01-01T00:00:00Z",
                    tags=["general"],
                )
            ]

    monkeypatch.setattr("packages.knowledge.api.KnowledgeService", lambda: FakeService())

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/knowledge/documents")

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["title"] == "Welcome"
    assert payload[0]["tags"] == ["general"]


@pytest.mark.asyncio
async def test_ingest_document_endpoint(monkeypatch, test_app):
    class FakeService:
        async def ingest_document(self, **kwargs):
            self.kwargs = kwargs
            return "doc-123"

    fake_service = FakeService()
    monkeypatch.setattr("packages.knowledge.api.KnowledgeService", lambda: fake_service)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.post(
            "/knowledge/ingest",
            json={
                "body": "Sample knowledge body",
                "title": "Policies",
                "source": "docs/policies.md",
                "hotel_id": "stayhive",
                "tags": ["policy"],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-123"
    assert fake_service.kwargs["hotel_id"] == "stayhive"
