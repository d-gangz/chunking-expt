# What This Does

Manages vector embeddings and hybrid search infrastructure using local PostgreSQL with pgvector, enabling efficient retrieval through combined vector similarity and full-text search.

# File Structure

```
├── docker/                          # Database container configuration
│   ├── docker-compose.yml          # PostgreSQL + pgvector setup
│   ├── postgres/                   # Database config files
│   │   └── init/                   # SQL initialization scripts
├── common/                         # Shared database utilities
│   ├── chunk_embedder.py          # OpenAI embedding generation
│   ├── embedding_utils.py         # Embedding helper functions
│   ├── hybrid_search.py           # Unified search interface
│   └── setup/                     # Template SQL files
├── fixed_chunks/                   # Fixed-size chunk implementation
│   ├── scripts/                   # Data loading and pipeline
│   │   ├── run_embedding_pipeline.py # Safe data loader with checks
│   │   └── db_fixed_chunks.py    # Direct database operations
│   ├── setup/                     # SQL schema definitions
│   └── tests/                     # Verification and testing
├── scripts/                       # Database management tools
│   ├── setup_new_chunking_strategy.py # Automated strategy setup
│   └── verify_local_setup.py      # Health check utility
├── setup_local_supabase.sh        # One-click setup script
└── README.md                      # Comprehensive documentation
```

# Quick Start

- Entry point: `./setup_local_supabase.sh` - automated setup
- Start DB: `cd docker && docker compose up -d`
- Load data: `uv run python fixed_chunks/scripts/run_embedding_pipeline.py`
- Test: `uv run python fixed_chunks/tests/test_hybrid_search.py`

# How It Works

The system uses PostgreSQL with pgvector extension to store chunks with 1024-dimensional embeddings. Hybrid search combines vector similarity (cosine distance) with full-text search using Reciprocal Rank Fusion (RRF) for optimal retrieval performance.

# Interfaces

```python
# Hybrid search interface
from common.hybrid_search import HybridSearch

searcher = HybridSearch("fixed_chunks")
results = searcher.search(
    query="AI safety",
    match_count=10,
    rrf_k=60  # RRF parameter
)

# Chunk embedding interface  
from common.chunk_embedder import ChunkEmbedder

embedder = ChunkEmbedder("strategy_name")
embedder.process_chunks("path/to/chunks.json")
```

# Dependencies

**Code Dependencies:**
- psycopg2 for PostgreSQL connection
- openai for embedding generation (text-embedding-3-large, 1024 dims)
- pgvector extension for vector operations
- dotenv for environment variables

**Data Dependencies:**
- Reads from: `/2_chunks/*/chunks/all_chunks_combined.json` - JSON chunk files
- Stores in: PostgreSQL tables with vector embeddings
- Requires: OPENAI_API_KEY and SUPABASE_CONNECTION_STRING in .env

**Cross-Directory Usage:**
- Called by: `/4_labelled_dataset/` - retrieves chunks for dataset
- Called by: `/5_evaluation/` - performs retrieval for evaluation
- Provides: Hybrid search API for chunk retrieval

# Key Patterns

- Docker-based PostgreSQL with pgvector extension
- Hybrid search combining vector + full-text with RRF
- Strategy-based table naming (e.g., fixed_chunks table)
- Automated setup scripts for new strategies
- Connection pooling and error handling

# Common Tasks

- Add new strategy: `uv run python scripts/setup_new_chunking_strategy.py NAME`
- Reset database: `cd docker && docker compose down -v && docker compose up -d`
- Check health: `uv run python scripts/verify_local_setup.py`
- Direct SQL: `docker exec chunking-expt-postgres psql -U postgres`

# Recent Updates

- Migrated from Supabase cloud to local PostgreSQL (4b61339)
- Added automated chunking strategy setup (4e0c418)
- Implemented hybrid search with RRF (9d6ce24)
- Enhanced connection handling for Mac compatibility

# Watch Out For

- Use 127.0.0.1 not localhost (Mac IPv6 issues)
- Ensure OPENAI_API_KEY is set for embeddings
- Vector dimension is fixed at 1024 (text-embedding-3-large)
- Docker must be running before any operations
- Check PostgreSQL logs: `docker logs chunking-expt-postgres`