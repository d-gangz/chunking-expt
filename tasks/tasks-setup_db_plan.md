## Relevant Files

- `/3_database/db_fixed_chunks.py` - Main script for embedding generation and database insertion
- `/3_database/hybrid_search.py` - Hybrid search implementation with vector and keyword search
- `/3_database/supabase_setup.py` - Database setup script for creating tables and indexes
- `/3_database/embedding_utils.py` - Utilities for OpenAI embedding generation with retry logic
- `/3_database/enable_pgvector.sql` - SQL script to enable pgvector extension
- `/3_database/check_pgvector.py` - Script to verify pgvector extension is enabled
- `/3_database/verify_setup.py` - Database setup verification script
- `/3_database/hybrid_search_function.sql` - SQL function for hybrid search with RRF
- `/3_database/test_database_setup.py` - Comprehensive database setup testing
- `/3_database/run_embedding_pipeline.py` - Pipeline runner with safety checks and cost estimation
- `/3_database/test_hybrid_search.py` - Test suite for hybrid search functionality
- `/3_database/quick_validation.py` - Quick validation checks for data integrity
- `/.env` - Environment variables (OPENAI_API_KEY, SUPABASE_CONNECTION_STRING already present)
- `/2_chunks/fixed_chunks/chunks/all_chunks_combined.json` - Input data file with chunks

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `db_fixed_chunks.py` and `db_fixed_chunks.test.py` in the same directory).
- Use `uv run pytest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the pytest configuration.

## Key Implementation Details from Research

### OpenAI Embeddings (text-embedding-3-large)

- **Model**: `text-embedding-3-large` with configurable dimensions (we'll use 1024)
- **Max input**: 8,192 tokens per text
- **Pricing**: $0.13 per 1M tokens
- **Rate limits**: Implement exponential backoff (5, 10, 20 seconds) for error 429
- **Optimal batch size**: 100 texts per API call for best throughput

### Supabase Hybrid Search

- **Extension**: Must enable `pgvector` extension in Supabase
- **Index types**: HNSW for vector search, GIN for full-text search
- **Hybrid approach**: Use Reciprocal Rank Fusion (RRF) with k=60
- **Connection**: Use SUPABASE_CONNECTION_STRING for direct PostgreSQL access
- **Search weights**: 70% semantic, 30% keyword (configurable)

## Tasks

- [x] 1.0 Environment Setup and Dependencies
  - [x] 1.1 Install required Python packages using uv:
    ```bash
    uv pip install openai
    uv pip install psycopg2-binary
    uv pip install pgvector
    uv pip install python-dotenv
    uv pip install tqdm
    uv pip install tiktoken
    ```
  - [x] 1.2 Verify .env file contains:
    ```
    OPENAI_API_KEY=your-api-key
    SUPABASE_CONNECTION_STRING=postgresql://postgres:[password]@[host]:[port]/postgres
    ```
  - [x] 1.3 Create embedding_utils.py with OpenAI embedding utilities:
    ```python
    # Key functions to implement:
    # - create_embeddings_with_retry(): Handle rate limits with exponential backoff
    # - process_batches(): Process texts in batches of 100
    # - count_tokens(): Use tiktoken to count tokens before API calls
    # - estimate_cost(): Calculate embedding costs ($0.13/1M tokens)
    ```
- [x] 2.0 Database Schema Setup
  - [x] 2.1 Guide user to enable pgvector extension in Supabase:
    ```
    Instructions: Go to Supabase Dashboard → SQL Editor → Run:
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
  - [x] 2.2 Create supabase_setup.py with the following table schema:
    ```sql
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
    ```
  - [x] 2.3 Execute SQL to create indexes:

    ```sql
    -- HNSW index for vector search (cosine similarity)
    CREATE INDEX IF NOT EXISTS fixed_chunks_embedding_hnsw_idx
    ON fixed_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

    -- GIN index for full-text search
    CREATE INDEX IF NOT EXISTS fixed_chunks_text_gin_idx
    ON fixed_chunks
    USING GIN (to_tsvector('english', text));

    -- B-tree index on title for keyword search
    CREATE INDEX IF NOT EXISTS fixed_chunks_title_idx
    ON fixed_chunks (title);
    ```

  - [x] 2.4 Verify table and indexes using psycopg2 connection test
- [x] 3.0 Data Processing Implementation
  - [x] 3.1 Implement db_fixed_chunks.py with ChunkEmbedder class:
    ```python
    class ChunkEmbedder:
        def __init__(self):
            # Initialize OpenAI client with model="text-embedding-3-large"
            # Set dimensions=1024 for embeddings
            # Set batch_size=100 for optimal throughput
    ```
  - [x] 3.2 Add chunk loading from JSON (exclude 'chunk_id' field as specified)
  - [x] 3.3 Implement batch embedding generation:
    ```python
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Use OpenAI API: model="text-embedding-3-large", dimensions=1024
        # Process in batches of 100
        # Implement retry logic: wait 5, 10, 20 seconds on rate limit (error 429)
    ```
  - [x] 3.4 Create batch insertion with psycopg2.extras.execute_batch:
    ```python
    # Use execute_batch for efficient multi-row inserts
    # Batch size: 100 rows per transaction
    # Add proper rollback on errors
    ```
  - [x] 3.5 Add progress tracking with tqdm and checkpoint file for resume capability
- [x] 4.0 Hybrid Search Implementation
  - [x] 4.1 Create RRF-based hybrid search SQL function in Supabase:
    ```sql
    CREATE OR REPLACE FUNCTION hybrid_search_fixed_chunks(
        query_text text,
        query_embedding vector(1024),
        match_count int DEFAULT 20,
        rrf_k int DEFAULT 60
    )
    RETURNS TABLE(
        id integer,
        text text,
        title text,
        cue_start float,
        cue_end float,
        similarity_score float,
        fts_score float,
        hybrid_score float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        WITH semantic_search AS (
            SELECT
                fc.id,
                fc.text,
                fc.title,
                fc.cue_start,
                fc.cue_end,
                1 - (fc.embedding <=> query_embedding) AS similarity,
                ROW_NUMBER() OVER (ORDER BY fc.embedding <=> query_embedding) AS rank
            FROM fixed_chunks fc
            ORDER BY fc.embedding <=> query_embedding
            LIMIT match_count * 2
        ),
        fts_search AS (
            SELECT
                fc.id,
                fc.text,
                fc.title,
                fc.cue_start,
                fc.cue_end,
                ts_rank_cd(to_tsvector('english', fc.text), websearch_to_tsquery('english', query_text)) AS rank_score,
                ROW_NUMBER() OVER (
                    ORDER BY ts_rank_cd(to_tsvector('english', fc.text), websearch_to_tsquery('english', query_text)) DESC
                ) AS rank
            FROM fixed_chunks fc
            WHERE to_tsvector('english', fc.text) @@ websearch_to_tsquery('english', query_text)
            ORDER BY rank_score DESC
            LIMIT match_count * 2
        )
        SELECT
            COALESCE(s.id, f.id) AS id,
            COALESCE(s.text, f.text) AS text,
            COALESCE(s.title, f.title) AS title,
            COALESCE(s.cue_start, f.cue_start) AS cue_start,
            COALESCE(s.cue_end, f.cue_end) AS cue_end,
            COALESCE(s.similarity, 0) AS similarity_score,
            COALESCE(f.rank_score, 0) AS fts_score,
            COALESCE(1.0 / (rrf_k + s.rank), 0) +
            COALESCE(1.0 / (rrf_k + f.rank), 0) AS hybrid_score
        FROM semantic_search s
        FULL OUTER JOIN fts_search f ON s.id = f.id
        ORDER BY hybrid_score DESC
        LIMIT match_count;
    END;
    $$;
    ```
  - [x] 4.2 Implement hybrid_search.py using psycopg2 with connection string:

    ```python
    import psycopg2
    from psycopg2.extras import RealDictCursor

    class HybridSearch:
        def __init__(self):
            self.openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))
            self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")

        def generate_query_embedding(self, query: str) -> List[float]:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=query,
                dimensions=1024
            )
            return response.data[0].embedding
    ```

  - [x] 4.3 Add main search method using direct SQL function call:
    ```python
    def search(self, query: str, match_count: int = 20, rrf_k: int = 60) -> List[Dict]:
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)

        # Connect to database
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Call the hybrid search function
            cur.execute(
                "SELECT * FROM hybrid_search_fixed_chunks(%s, %s::vector, %s, %s)",
                (query, query_embedding, match_count, rrf_k)
            )
            results = cur.fetchall()
            return [dict(row) for row in results]
        finally:
            cur.close()
            conn.close()
    ```
  - [x] 4.4 Add example usage and error handling:
    ```python
    if __name__ == "__main__":
        searcher = HybridSearch()

        # Example search
        query = "AI prompting techniques for legal counsel"
        results = searcher.search(query, match_count=10)

        for result in results:
            print(f"Score: {result['hybrid_score']:.4f}")
            print(f"Title: {result['title']} ({result['cue_start']:.1f}s - {result['cue_end']:.1f}s)")
            print(f"Text preview: {result['text'][:200]}...")
    ```
- [x] 5.0 Testing and Validation
  - [x] 5.1 Verify database setup:
    - Check pgvector extension is enabled
    - Confirm fixed_chunks table exists with correct schema
    - Verify all indexes are created (HNSW, GIN, B-tree)
  - [x] 5.2 Run the full embedding pipeline:
    - Execute db_fixed_chunks.py on all_chunks_combined.json
    - Monitor for any errors during embedding generation
    - Confirm all chunks are successfully inserted into database
  - [x] 5.3 Test hybrid search functionality:
    - Run a few sample queries using hybrid_search.py
    - Verify search returns results with reasonable scores
    - Check that search completes within 5 seconds
  - [x] 5.4 Quick validation checks:
    - Query database to confirm row count matches input chunks
    - Spot check a few embeddings to ensure they have 1024 dimensions
