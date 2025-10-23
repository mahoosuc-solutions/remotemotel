#!/usr/bin/env python3
"""Simple ingestion script for the knowledge base using KnowledgeService."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from packages.knowledge.service import DEFAULT_HOTEL_ID, KnowledgeService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documentation into the knowledge base")
    parser.add_argument(
        "path",
        nargs="?",
        default="docs/VOICE_MODULE_DESIGN.md",
        help="Path to the document to ingest",
    )
    parser.add_argument("--hotel", default=None, help="Hotel identifier override")
    parser.add_argument("--title", default=None, help="Optional document title")
    parser.add_argument("--source", default=None, help="Optional source label")
    parser.add_argument("--tags", default=None, help="Comma separated list of tags")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL (otherwise pulled from environment)",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(path)

    hotel_id = args.hotel or DEFAULT_HOTEL_ID
    title = args.title or path.stem
    source = args.source or str(path)
    tags = [tag.strip() for tag in args.tags.split(",")] if args.tags else None

    service = KnowledgeService(database_url=args.database_url)
    document_id = await service.ingest_document(
        hotel_id=hotel_id,
        source=source,
        title=title,
        body=path.read_text(),
        tags=tags,
    )

    print(f"Inserted document {document_id} for hotel {hotel_id}")


if __name__ == "__main__":
    asyncio.run(main())
