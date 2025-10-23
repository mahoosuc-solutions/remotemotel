# Postgres Knowledge Base Setup

## Overview

The knowledge base uses PostgreSQL with the `pgvector` extension to store chunked hotel documents and embeddings for semantic search. This guide covers local setup for development.

## Requirements

- PostgreSQL 15+
- Extensions: `pgvector`, `citext`, optional `pg_trgm`
- Python dependencies (already in project): `asyncpg`

## Installation

### macOS (Homebrew)

```bash
brew install postgresql
brew install pgvector
brew services start postgresql
```

### Ubuntu/Debian

```bash
sudo apt-get update && sudo apt-get install postgresql postgresql-contrib
# Install pgvector (PGDG repo)
echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update && sudo apt-get install postgresql-15-pgvector
```

### Docker Compose (recommended for dev)

A ready-to-use compose file lives at [`docker-compose.postgres.yml`](../docker-compose.postgres.yml):

```bash
docker compose -f docker-compose.postgres.yml up -d
```

The container exposes Postgres on `localhost:5432` with credentials `stayhive/stayhive` and automatically persists data in `data/postgres/`.

## Database Setup

Connect to Postgres:

```bash
psql postgres://stayhive:stayhive@localhost:5432/stayhive
```

Enable extensions:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS citext;
-- Optional for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Create schema:

```sql
CREATE SCHEMA IF NOT EXISTS knowledge;

CREATE TABLE knowledge.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES knowledge.documents(id) ON DELETE CASCADE,
    hotel_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge.embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES knowledge.chunks(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON knowledge.chunks (hotel_id, chunk_index);
CREATE INDEX ON knowledge.documents USING GIN (tags);
CREATE INDEX ON knowledge.embeddings USING ivfflat (embedding vector_cosine_ops);
```

> Adjust the `vector` dimension (1536) to match the embedding model used.

## Ingestion Workflow

1. Load document (Markdown, policy, etc.)
2. Split into ~500 token chunks
3. Generate embeddings via OpenAI (or local model)
4. Insert into `documents`, `chunks`, `embeddings`

The `scripts/ingest_knowledge.py` utility now wraps this workflow end-to-end:

```bash
export DATABASE_URL="postgresql://stayhive:stayhive@localhost:5432/stayhive"
export OPENAI_API_KEY=sk-...
python scripts/ingest_knowledge.py docs/VOICE_MODULE_DESIGN.md --tags policies,voice
```

You should see `Inserted document <uuid> for hotel stayhive` once the record is stored. Subsequent ingests with the same `--source` replace the previous document automatically.

## Semantic Query

Example SQL function:

```sql
CREATE OR REPLACE FUNCTION knowledge.semantic_search(
    hotel TEXT,
    query_embedding vector(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    metadata JSONB,
    similarity DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.content,
        c.metadata,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM knowledge.embeddings e
    JOIN knowledge.chunks c ON c.id = e.chunk_id
    WHERE c.hotel_id = hotel
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

## Connection Settings

Add to `.env.local`:

```
DATABASE_URL=postgresql+asyncpg://stayhive:stayhive@localhost:5432/stayhive
KNOWLEDGE_SCHEMA=knowledge
```

## Monitoring & Maintenance

- Run `VACUUM ANALYZE knowledge.*` after large ingests
- Use `pg_stat_user_tables` to watch growth and bloat
- Reindex the ivfflat index after large deletions (`REINDEX INDEX ...`)
- Back up regularly with `pg_dump`
