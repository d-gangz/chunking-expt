
        -- Create table for fixed_chunks chunks
        CREATE TABLE IF NOT EXISTS fixed_chunks (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            title TEXT NOT NULL,
            cue_start FLOAT NOT NULL,
            cue_end FLOAT NOT NULL,
            embedding vector(1024) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Create HNSW index for vector similarity search
        CREATE INDEX IF NOT EXISTS idx_fixed_chunks_embedding 
        ON fixed_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);

        -- Create GIN index for full-text search
        CREATE INDEX IF NOT EXISTS idx_fixed_chunks_text_fts
        ON fixed_chunks
        USING gin(to_tsvector('english', text));

        -- Create index on title for title-based queries
        CREATE INDEX IF NOT EXISTS idx_fixed_chunks_title
        ON fixed_chunks(title);
        