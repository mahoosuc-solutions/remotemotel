-- Create knowledge schema and tables for document storage and vector search

-- Create schema
CREATE SCHEMA IF NOT EXISTS knowledge;

-- Enable pgvector extension (if available)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table
CREATE TABLE IF NOT EXISTS knowledge.documents (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    hotel_id TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hotel_id, source)
);

-- Chunks table for document chunks
CREATE TABLE IF NOT EXISTS knowledge.chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES knowledge.documents(id) ON DELETE CASCADE,
    hotel_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Embeddings table for vector storage
CREATE TABLE IF NOT EXISTS knowledge.embeddings (
    chunk_id BIGINT PRIMARY KEY REFERENCES knowledge.chunks(id) ON DELETE CASCADE,
    embedding FLOAT8[] NOT NULL,  -- Using FLOAT8[] instead of vector type for compatibility
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_hotel_id ON knowledge.documents(hotel_id);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON knowledge.documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON knowledge.chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hotel_id ON knowledge.chunks(hotel_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON knowledge.embeddings(chunk_id);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION knowledge.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON knowledge.documents
    FOR EACH ROW EXECUTE FUNCTION knowledge.update_updated_at_column();
