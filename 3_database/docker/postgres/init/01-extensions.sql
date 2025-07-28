-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Show installed version
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';