import asyncio

import pytest

from packages.tools import search_kb


@pytest.mark.asyncio
async def test_search_kb_fallback_no_db(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    results = await search_kb.search_kb("pet")
    assert results
    assert all("pet" in item.get("title", "").lower() for item in results)


@pytest.mark.asyncio
async def test_search_kb_returns_empty_for_blank_query():
    results = await search_kb.search_kb("")
    assert results == []
