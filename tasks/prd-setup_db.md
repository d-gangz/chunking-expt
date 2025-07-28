# Database Setup Plan for Chunk Embeddings and Storage

## Overview

This plan outlines the implementation of `db_fixed_chunks.py` to embed transcript chunks and store them in Supabase (PostgreSQL) with hybrid search capabilities.

## Objectives

1. Generate embeddings for all chunks using OpenAI's text-embedding-3-large model with 1024 dimensions
2. Store chunks and embeddings in Supabase PostgreSQL database
3. Enable hybrid search (vector + keyword) using HNSW indexing
4. Use connection string URI for database connectivity

## Architecture

### Input

- Source: `/2_chunks/fixed_chunks/chunks/all_chunks_combined.json`
- Format: JSON array of chunk objects containing:
  - `chunk_id` (to be excluded from storage)
  - `text` (main content for embedding)
  - `title`
  - `cue_start`
  - `cue_end`
  - `chunk_index`
  - `total_chunks`

### Processing Pipeline

1. **Load chunks** from JSON file
2. **Generate embeddings** using OpenAI API
3. **Connect to Supabase** via connection string
4. **Create/update table schema**
5. **Insert data** with embeddings
6. **Configure indexes** for hybrid search

### Output

- Supabase table: `fixed_chunks`
- Columns:
  - `id` (auto-generated primary key)
  - `text` (TEXT)
  - `title` (TEXT)
  - `cue_start` (FLOAT)
  - `cue_end` (FLOAT)
  - `chunk_index` (INTEGER)
  - `total_chunks` (INTEGER)
  - `embedding` (vector(1024))

## Implementation Steps

### 1. Environment Setup

```bash
# Required packages
uv pip install openai
uv pip install supabase
uv pip install psycopg2-binary
uv pip install pgvector
uv pip install python-dotenv
uv pip install tqdm
```

### 2. Configuration

OpenAI API key and Supabase connection string is already in my .env file.

### 3. Database Schema Setup

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
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

-- Create HNSW index for vector search
CREATE INDEX IF NOT EXISTS fixed_chunks_embedding_hnsw_idx
ON fixed_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS fixed_chunks_text_gin_idx
ON fixed_chunks
USING GIN (to_tsvector('english', text));

-- Create index on title for keyword search
CREATE INDEX IF NOT EXISTS fixed_chunks_title_idx
ON fixed_chunks (title);
```

### 4. Script Structure

All scripts should be created in the `/3_database` folder.

#### 4.1 Main Script (`/3_database/db_fixed_chunks.py`)

```python
import json
import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
import time

class ChunkEmbedder:
    def __init__(self):
        load_dotenv()
        self.openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        self.batch_size = 100  # Process in batches for efficiency

    def load_chunks(self, file_path: str) -> List[Dict[str, Any]]:
        """Load chunks from JSON file"""

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API with retry logic"""

    def setup_database(self):
        """Create table and indexes if they don't exist"""

    def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Insert chunks with embeddings into database"""

    def process(self):
        """Main processing pipeline"""
```

### 5. Key Implementation Considerations

#### Embedding Generation

- Use batching to reduce API calls (OpenAI supports up to 2048 inputs per request)
- Implement retry logic with exponential backoff for API failures
- Add progress bars for long-running operations
- Cache embeddings locally to avoid re-processing on failures

#### Database Operations

- Use connection pooling for better performance
- Implement transaction batching for bulk inserts
- Use `execute_batch` for efficient multi-row inserts
- Add proper error handling and rollback mechanisms

#### Data Validation

- Verify embedding dimensions (1024)
- Validate chunk data integrity before insertion
- Check for duplicate chunks (based on text content)
- Log any skipped or failed chunks

#### 4.2 Hybrid Search Script (`/3_database/hybrid_search.py`)

```python
import os
from typing import List, Dict, Any, Tuple
import openai
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np

class HybridSearch:
    def __init__(self):
        load_dotenv()
        self.openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=query,
            dimensions=1024
        )
        return response.data[0].embedding

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and keyword matching.

        Args:
            query: Search query string
            top_k: Number of results to return (default: 10)

        Returns:
            List of matching chunks with metadata
        """
        # Generate embedding for the query
        query_embedding = self.generate_query_embedding(query)

        # Connect to database
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Hybrid search query
            hybrid_query = """
            WITH semantic_search AS (
                SELECT
                    id,
                    text,
                    title,
                    cue_start,
                    cue_end,
                    chunk_index,
                    total_chunks,
                    1 - (embedding <=> %s::vector) AS semantic_score
                FROM fixed_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT 20
            ),
            keyword_search AS (
                SELECT
                    id,
                    text,
                    title,
                    cue_start,
                    cue_end,
                    chunk_index,
                    total_chunks,
                    ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) AS keyword_score
                FROM fixed_chunks
                WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s)
                ORDER BY keyword_score DESC
                LIMIT 20
            ),
            combined AS (
                SELECT
                    COALESCE(s.id, k.id) as id,
                    COALESCE(s.text, k.text) as text,
                    COALESCE(s.title, k.title) as title,
                    COALESCE(s.cue_start, k.cue_start) as cue_start,
                    COALESCE(s.cue_end, k.cue_end) as cue_end,
                    COALESCE(s.chunk_index, k.chunk_index) as chunk_index,
                    COALESCE(s.total_chunks, k.total_chunks) as total_chunks,
                    COALESCE(s.semantic_score, 0) as semantic_score,
                    COALESCE(k.keyword_score, 0) as keyword_score,
                    -- Weighted combination: 70% semantic, 30% keyword
                    (0.7 * COALESCE(s.semantic_score, 0) + 0.3 * COALESCE(k.keyword_score, 0)) as combined_score
                FROM semantic_search s
                FULL OUTER JOIN keyword_search k ON s.id = k.id
            )
            SELECT
                id,
                text,
                title,
                cue_start,
                cue_end,
                chunk_index,
                total_chunks,
                semantic_score,
                keyword_score,
                combined_score
            FROM combined
            ORDER BY combined_score DESC
            LIMIT %s;
            """

            # Execute query
            cur.execute(hybrid_query, (query_embedding, query_embedding, query, query, top_k))
            results = cur.fetchall()

            # Convert results to list of dicts
            return [dict(row) for row in results]

        finally:
            cur.close()
            conn.close()

    def search_semantic_only(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Pure semantic search for comparison"""
        query_embedding = self.generate_query_embedding(query)

        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute("""
                SELECT
                    id, text, title, cue_start, cue_end, chunk_index, total_chunks,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM fixed_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (query_embedding, query_embedding, top_k))

            return [dict(row) for row in cur.fetchall()]

        finally:
            cur.close()
            conn.close()

    def search_keyword_only(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Pure keyword search for comparison"""
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cur.execute("""
                SELECT
                    id, text, title, cue_start, cue_end, chunk_index, total_chunks,
                    ts_rank(to_tsvector('english', text), plainto_tsquery('english', %s)) AS rank
                FROM fixed_chunks
                WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT %s;
            """, (query, query, top_k))

            return [dict(row) for row in cur.fetchall()]

        finally:
            cur.close()
            conn.close()


# Example usage
if __name__ == "__main__":
    # Initialize search
    searcher = HybridSearch()

    # Example query
    query = "AI prompting techniques for legal counsel"

    # Perform hybrid search
    print("Hybrid Search Results:")
    results = searcher.search(query, top_k=10)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']} (Chunk {result['chunk_index']}/{result['total_chunks']})")
        print(f"   Score: {result['combined_score']:.4f} (Semantic: {result['semantic_score']:.4f}, Keyword: {result['keyword_score']:.4f})")
        print(f"   Time: {result['cue_start']:.2f}s - {result['cue_end']:.2f}s")
        print(f"   Text preview: {result['text'][:200]}...")
```

### 6. Hybrid Search Implementation

The hybrid search script (`/3_database/hybrid_search.py`) provides a function-based interface for performing searches. It combines:

1. **Semantic Search**: Uses vector similarity with embeddings
2. **Keyword Search**: Uses PostgreSQL full-text search
3. **Hybrid Scoring**: Weighted combination (70% semantic, 30% keyword)

Usage example:

```python
from hybrid_search import HybridSearch

# Initialize
searcher = HybridSearch()

# Search
results = searcher.search("your query here", top_k=10)

# Results include:
# - id, text, title
# - cue_start, cue_end
# - chunk_index, total_chunks
# - semantic_score, keyword_score, combined_score
```

### 7. Error Handling and Monitoring

- Log all operations with timestamps
- Track embedding generation costs
- Monitor database connection health
- Implement checkpointing for resume capability
- Add data quality checks

### 8. Performance Optimizations

- Parallel embedding generation (respecting rate limits)
- Bulk database operations
- Connection pooling
- Efficient memory usage for large datasets
- Progress tracking and resumability

### 9. Testing Strategy

1. **Unit tests** for each component
2. **Integration tests** for database operations
3. **Embedding quality checks**
4. **Search performance benchmarks**
5. **Error recovery scenarios**

### 10. Next Steps

After successful implementation:

1. Run evaluation metrics on search quality
2. Compare hybrid search vs pure vector search
3. Optimize HNSW parameters based on performance
4. Consider implementing caching layer
5. Add monitoring and alerting

## Success Criteria

- All chunks successfully embedded and stored
- Database indexes properly configured
- Hybrid search queries return relevant results
- Script is resumable and handles errors gracefully
- Performance meets requirements (< 5s for search queries)
