"""Semantic knowledge base search powered by PostgreSQL + pgvector."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from packages.knowledge.service import DEFAULT_HOTEL_ID, KnowledgeService

RESULT_LIMIT = int(os.getenv("KNOWLEDGE_TOP_K", "5"))


async def search_kb(
    query: str,
    top_k: int = RESULT_LIMIT,
    hotel_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Perform a semantic search against the knowledge base."""

    if not query:
        return []

    hotel = hotel_id or DEFAULT_HOTEL_ID

    try:
        service = KnowledgeService()
        results = await service.semantic_search(hotel_id=hotel, query=query, top_k=top_k)
        return results
    except Exception:  # pragma: no cover - fall back to simple matching
        fallback = [
            {"title": "Pet Policy", "content": "Pets are welcome with a nightly fee."},
            {"title": "Check-in", "content": "Check-in time is after 4 PM."},
            {"title": "Checkout", "content": "Checkout time is by 10 AM."},
        ]
        lower_query = query.lower()
        return [item for item in fallback if lower_query in item["title"].lower()][:top_k]
