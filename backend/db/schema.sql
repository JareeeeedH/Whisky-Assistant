CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    source      TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id           BIGSERIAL PRIMARY KEY,
    document_id  BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INT NOT NULL,
    content      TEXT NOT NULL,
    -- bge-m3 的輸出維度
    embedding    VECTOR(1024) NOT NULL,
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
