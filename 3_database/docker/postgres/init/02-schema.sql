-- Create the fixed_chunks table with vector column
CREATE TABLE IF NOT EXISTS fixed_chunks (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    title TEXT NOT NULL,
    cue_start FLOAT NOT NULL,
    cue_end FLOAT NOT NULL,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for vector search (cosine similarity)
CREATE INDEX IF NOT EXISTS fixed_chunks_embedding_hnsw_idx
ON fixed_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS fixed_chunks_text_gin_idx
ON fixed_chunks
USING GIN (to_tsvector('english', text));

-- Create B-tree index on title for keyword search
CREATE INDEX IF NOT EXISTS fixed_chunks_title_idx
ON fixed_chunks (title);

-- Display table information
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'fixed_chunks'
ORDER BY ordinal_position;

-- Display index information
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'fixed_chunks';