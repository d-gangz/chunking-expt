# Adding a New Chunking Strategy to the Database

Follow these steps when you have a new chunk strategy (e.g., `tool_chunks`, `semantic_chunks`, etc.):

## Prerequisites
- Your chunks are saved as JSON files in `2_chunks/<strategy_name>/chunks/`
- You have a Supabase project with pgvector enabled
- Environment variables are set (`.env` file with `OPENAI_API_KEY` and `SUPABASE_CONNECTION_STRING`)

## Step 1: Create Database Folder Structure

Create the following folder structure in `3_database/`:
```
3_database/
└── <strategy_name>/          # e.g., tool_chunks
    ├── scripts/
    ├── setup/
    └── tests/
```

## Step 2: Create the Database Table

1. Go to your Supabase Dashboard → SQL Editor
2. Run this SQL (replace `<strategy_name>` with your table name):

```sql
-- Create table for your chunk strategy
CREATE TABLE IF NOT EXISTS <strategy_name> (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    title TEXT,
    cue_start FLOAT,
    cue_end FLOAT,
    embedding vector(1024)
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_<strategy_name>_embedding 
ON <strategy_name> 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index for full-text search
CREATE INDEX IF NOT EXISTS idx_<strategy_name>_text_fts
ON <strategy_name>
USING gin(to_tsvector('english', text));
```

## Step 3: Generate Hybrid Search Function

```bash
# Navigate to the project root
cd /path/to/chunking-expt

# Generate the SQL function for your table
uv run python 3_database/common/setup/create_hybrid_search_function.py <strategy_name>

# This creates: 3_database/common/setup/hybrid_search_<strategy_name>.sql
```

Copy the generated SQL and run it in Supabase SQL Editor.

## Step 4: Run the Embedding Pipeline

No need to copy scripts! Use the generic chunk embedder directly:

```bash
# Navigate to the project root
cd /path/to/chunking-expt

# Run the generic embedder with your table name and chunk file
uv run python 3_database/common/chunk_embedder.py <strategy_name> 2_chunks/<strategy_name>/chunks/all_chunks_combined.json

# Example for tool_chunks:
uv run python 3_database/common/chunk_embedder.py tool_chunks 2_chunks/tool_chunks/chunks/all_chunks_combined.json

# To clear table before inserting (optional):
uv run python 3_database/common/chunk_embedder.py tool_chunks 2_chunks/tool_chunks/chunks/all_chunks_combined.json --clear
```

This will:
1. Load chunks from `2_chunks/<strategy_name>/chunks/`
2. Generate embeddings using OpenAI
3. Store chunks and embeddings in Supabase

## Step 5: Test Your Setup

Create a test script to verify everything works:

```python
from common.hybrid_search import HybridSearch

# Initialize searcher for your table
searcher = HybridSearch("<strategy_name>")

# Test search
results = searcher.search("your test query", match_count=5)

# Display results
for result in results:
    print(f"Score: {result['hybrid_score']:.4f}")
    print(f"Text: {result['text'][:100]}...")
    print("-" * 80)
```

## Step 6: Usage in Your Application

```python
from common.hybrid_search import HybridSearch

# Create searcher for your chunk strategy
searcher = HybridSearch("<strategy_name>")

# Perform searches
results = searcher.search(user_query, match_count=20)
```

## Example: Adding Tool Chunks

```bash
# 1. Create table in Supabase (run SQL from Step 2)

# 2. Generate and run hybrid search function
uv run python 3_database/common/setup/create_hybrid_search_function.py tool_chunks
# Copy the generated SQL from 3_database/common/setup/hybrid_search_tool_chunks.sql
# Run it in Supabase SQL Editor

# 3. Run embedding pipeline (no copying needed!)
uv run python 3_database/common/chunk_embedder.py tool_chunks 2_chunks/tool_chunks/chunks/all_chunks_combined.json

# 4. Test
python -c "from common.hybrid_search import HybridSearch; s = HybridSearch('tool_chunks'); print(s.search('AI safety', 5))"
```

## Notes
- Each strategy uses the same table schema for consistency
- The hybrid search combines vector similarity and full-text search
- Default embedding model: OpenAI's `text-embedding-3-large` (1024 dimensions)
- Make sure your chunk JSON files have: `text`, `title`, `cue_start`, `cue_end` fields