<!--
Document Type: Process Documentation
Purpose: Step-by-step guide for adding new chunking strategies to the database
Context: Created for systematic chunking strategy implementation and testing
Key Topics: Database setup, automated scripts, hybrid search, PostgreSQL, pgvector
Target Use: Process guide for implementing new chunking strategies
-->

# Adding a New Chunking Strategy to the Database

This guide explains how to add a new chunking strategy to the database using our automated setup script.

## Quick Start (Recommended)

If you have your chunks ready in `2_chunks/<strategy_name>/chunks/all_chunks_combined.json`, just run:

```bash
# Navigate to project root
cd /path/to/chunking-expt

# Run the automated setup
uv run python 3_database/scripts/setup_new_chunking_strategy.py <strategy_name>

# Example:
uv run python 3_database/scripts/setup_new_chunking_strategy.py semantic_chunks
```

This single command will:
1. ✅ Create the database table
2. ✅ Set up indexes (HNSW for vectors, GIN for text search)
3. ✅ Create the hybrid search function
4. ✅ Generate embeddings for all chunks
5. ✅ Insert chunks into the database
6. ✅ Create test files
7. ✅ Generate documentation

## Prerequisites

Before running the setup:

1. **Chunks are ready**: Your chunks must be saved as JSON at:
   ```
   2_chunks/<strategy_name>/chunks/all_chunks_combined.json
   ```

2. **Local database is running**:
   ```bash
   cd 3_database/docker
   docker compose up -d
   ```

3. **Environment variables are set** (in `.env` file):
   ```
   OPENAI_API_KEY=your-api-key
   SUPABASE_CONNECTION_STRING=postgresql://postgres:postgres@127.0.0.1:5432/postgres
   ```

## Step-by-Step Process

### Step 1: Generate Your Chunks

First, create your chunks using the appropriate script in `2_chunks/`:

```bash
# Example: Generate fixed-size chunks
uv run python 2_chunks/fixed_chunks/generate_chunks.py

# This creates: 2_chunks/fixed_chunks/chunks/all_chunks_combined.json
```

### Step 2: Run the Automated Setup

```bash
uv run python 3_database/scripts/setup_new_chunking_strategy.py <strategy_name>
```

Options:
- `--skip-embeddings`: Skip embedding generation (useful for testing)

### Step 3: Test Your Setup

The script creates a test file. Run it to verify everything works:

```bash
uv run python 3_database/<strategy_name>/tests/test_<strategy_name>_search.py
```

### Step 4: Use in Your Code

```python
from database.common.hybrid_search import HybridSearch

# Create searcher for your strategy
searcher = HybridSearch("<strategy_name>")

# Search
results = searcher.search("your query", match_count=10)

# Process results
for result in results:
    print(f"Score: {result['hybrid_score']:.4f}")
    print(f"Text: {result['text'][:200]}...")
```

## What the Script Creates

Running the setup script creates this structure:

```
3_database/
└── <strategy_name>/
    ├── README.md              # Documentation for this strategy
    ├── setup/
    │   ├── create_table_<strategy_name>.sql      # Table creation SQL
    │   └── hybrid_search_<strategy_name>.sql     # Search function SQL
    └── tests/
        └── test_<strategy_name>_search.py        # Test script
```

## Manual Process (If Needed)

If you prefer manual setup or need to customize:

### 1. Create Table

```sql
CREATE TABLE IF NOT EXISTS <strategy_name> (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    title TEXT NOT NULL,
    cue_start FLOAT NOT NULL,
    cue_end FLOAT NOT NULL,
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_<strategy_name>_embedding ON <strategy_name> 
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_<strategy_name>_text_fts ON <strategy_name>
USING gin(to_tsvector('english', text));

CREATE INDEX idx_<strategy_name>_title ON <strategy_name>(title);
```

### 2. Create Hybrid Search Function

Use the template at `common/setup/generic_hybrid_search_template.sql`, replace `{TABLE_NAME}` with your table name.

### 3. Generate Embeddings

```bash
uv run python 3_database/common/chunk_embedder.py <strategy_name> \
    2_chunks/<strategy_name>/chunks/all_chunks_combined.json
```

## Examples

### Adding "semantic_chunks" Strategy

```bash
# 1. Ensure chunks exist
ls 2_chunks/semantic_chunks/chunks/all_chunks_combined.json

# 2. Run automated setup
uv run python 3_database/scripts/setup_new_chunking_strategy.py semantic_chunks

# 3. Test
uv run python 3_database/semantic_chunks/tests/test_semantic_chunks_search.py
```

### Adding "tool_chunks" Without Embeddings (for testing)

```bash
# Setup structure without generating embeddings
uv run python 3_database/scripts/setup_new_chunking_strategy.py tool_chunks --skip-embeddings

# Generate embeddings later
uv run python 3_database/common/chunk_embedder.py tool_chunks \
    2_chunks/tool_chunks/chunks/all_chunks_combined.json
```

## Troubleshooting

### "Chunks file not found"
- Make sure you've run the chunking script in `2_chunks/<strategy_name>/`
- Verify the file exists at `2_chunks/<strategy_name>/chunks/all_chunks_combined.json`

### "Table already exists"
- The script handles existing tables gracefully
- Use `--clear` flag with chunk_embedder to clear existing data

### "Connection refused"
- Ensure Docker is running: `docker ps`
- Start the database: `cd 3_database/docker && docker compose up -d`

### "Invalid table name"
- Table names must contain only letters, numbers, and underscores
- Examples: `semantic_chunks` ✅, `tool-chunks` ❌, `chunks@2024` ❌

## Best Practices

1. **Naming Convention**: Use lowercase with underscores (e.g., `semantic_chunks`, not `SemanticChunks`)
2. **Test First**: Run with `--skip-embeddings` to test setup before expensive embedding generation
3. **Monitor Costs**: The script shows estimated OpenAI API costs before proceeding
4. **Chunk Validation**: Ensure your chunks have required fields: `text`, `title`, `cue_start`, `cue_end`

## Notes

- Each strategy uses identical table schema for consistency
- Embeddings use OpenAI's `text-embedding-3-large` (1024 dimensions)
- The hybrid search combines vector similarity and full-text search using Reciprocal Rank Fusion (RRF)
- All tables are created in the same database for easy comparison