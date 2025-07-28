# Fixed Chunks Database Setup

This directory contains the database setup and scripts for the fixed_chunks chunking strategy.

## Structure

```
fixed_chunks/
├── scripts/      # Processing scripts
├── setup/        # SQL setup files
├── tests/        # Test scripts
└── README.md     # This file
```

## Usage

### Search for chunks

```python
from common.hybrid_search import HybridSearch

searcher = HybridSearch("fixed_chunks")
results = searcher.search("your query here", match_count=10)
```

### Run tests

```bash
uv run python 3_database/fixed_chunks/tests/test_fixed_chunks_search.py
```

### Regenerate embeddings

```bash
uv run python 3_database/common/chunk_embedder.py fixed_chunks 2_chunks/fixed_chunks/chunks/all_chunks_combined.json
```

## Table Details

- **Table name**: `fixed_chunks`
- **Embedding model**: text-embedding-3-large (1024 dimensions)
- **Indexes**: HNSW (vector), GIN (full-text), B-tree (title)
- **Search function**: `hybrid_search_fixed_chunks`
