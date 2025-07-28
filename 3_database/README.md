# Database Setup Guide

This guide covers setting up and using the local Supabase PostgreSQL database for the chunking experiment project.

## Overview

The database uses PostgreSQL with pgvector extension for hybrid search capabilities, combining vector similarity search with full-text search.

## Quick Start

### Automated Setup (Recommended)

Run the setup script for a complete automated installation:

```bash
./3_database/setup_local_supabase.sh
```

This script will:
- Check prerequisites (Docker, uv, environment variables)
- Start the PostgreSQL container
- Verify the setup
- Optionally load initial data
- Run automated tests

### Manual Setup

### 1. Start the Database

```bash
cd 3_database/docker
docker compose up -d
```

### 2. Load Data

Two options available:

**Option A: Full Pipeline (Recommended)**
```bash
# Runs safety checks before loading data
uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py
```

**Option B: Direct Loading**
```bash
# Directly loads data without checks
uv run python 3_database/fixed_chunks/scripts/db_fixed_chunks.py
```

### 3. Verify Data

```bash
# Check loaded chunks
docker exec chunking-expt-postgres psql -U postgres -c "SELECT COUNT(*) FROM fixed_chunks;"
```

## Database Connection

### Connection Details
- **Host**: 127.0.0.1 (use IPv4, not localhost)
- **Port**: 5432
- **Database**: postgres
- **Username**: postgres
- **Password**: postgres
- **Connection String**: `postgresql://postgres:postgres@127.0.0.1:5432/postgres`

### GUI Access

We recommend using TablePlus for database visualization:
1. Download from https://tableplus.com/
2. Create new PostgreSQL connection with above details
3. Set SSL mode to "Disable"

## Architecture

### Table Schema

Each chunking strategy has its own table with identical schema:

```sql
CREATE TABLE fixed_chunks (
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

### Indexes

- **HNSW Index**: For fast vector similarity search
- **GIN Index**: For full-text search
- **B-tree Index**: For title-based queries

### Hybrid Search Function

Each table has a corresponding hybrid search function:
```sql
hybrid_search_fixed_chunks(query_text, query_embedding, match_count, rrf_k)
```

## Adding New Chunking Strategies

### 🚀 For Junior Developers - Start Here!

**Want to add a new chunking strategy? Follow these 3 steps:**

1. **First, create your chunks** (in the `2_chunks/` folder)
   ```bash
   # Your chunks should be at:
   2_chunks/YOUR_STRATEGY_NAME/chunks/all_chunks_combined.json
   ```

2. **Make sure the database is running**
   ```bash
   cd 3_database/docker
   docker compose up -d
   ```

3. **Run the magic command**
   ```bash
   uv run python 3_database/scripts/setup_new_chunking_strategy.py YOUR_STRATEGY_NAME
   ```

That's it! Everything else is automated. 

**📖 Need more details?** Read `3_database/new-chunking-strategy.md`

### What the Automated Script Does

- ✅ Creates database table with proper indexes
- ✅ Sets up hybrid search function
- ✅ Generates embeddings using OpenAI
- ✅ Inserts all chunks into database
- ✅ Creates test files
- ✅ Generates documentation

### Manual Process (Advanced Users Only)

1. Create new table with same schema (change table name)
2. Use the generic template at `common/setup/generic_hybrid_search_template.sql`
3. Replace `{TABLE_NAME}` with your table name
4. Run the SQL to create table and function

## Docker Management

### Start Database
```bash
cd 3_database/docker
docker compose up -d
```

### Stop Database
```bash
docker compose down
```

### Reset Database (Delete All Data)
```bash
docker compose down -v  # -v removes volumes
docker compose up -d
```

### View Logs
```bash
docker logs chunking-expt-postgres --tail 50
```

## Troubleshooting

### Connection Issues on Mac

If you get "server closed the connection unexpectedly":
- Always use `127.0.0.1` instead of `localhost`
- The database is configured for IPv4-only to avoid Mac IPv6 issues
- Check Docker is running: `docker ps`

### PostgreSQL Startup Errors

**Error: "unrecognized configuration parameter 'checkpoint_segments'"**
- This is already fixed in our configuration
- We use `max_wal_size=4GB` instead

**Error: "structure of query does not match function result type"**
- The hybrid search function has been updated to handle type mismatches
- Run: `docker exec chunking-expt-postgres psql -U postgres -f /docker-entrypoint-initdb.d/03-functions.sql`

### Docker Issues

**Container won't start:**
```bash
# Check logs
docker logs chunking-expt-postgres

# Remove and recreate
cd 3_database/docker
docker compose down -v
docker compose up -d
```

**Port already in use:**
```bash
# Find process using port 5432
lsof -i :5432

# Kill the process or change port in docker-compose.yml
```

### Python/Import Errors

**Module not found errors:**
```bash
# Ensure you're in project root
cd /path/to/chunking-expt

# Run with uv
uv run python 3_database/scripts/script_name.py
```

**psycopg2 installation issues:**
```bash
# Install with uv
uv pip install psycopg2-binary
```

### Check Database Health

```bash
# Test connection
docker exec chunking-expt-postgres psql -U postgres -c "SELECT 1;"

# Check pgvector
docker exec chunking-expt-postgres psql -U postgres -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# List tables
docker exec chunking-expt-postgres psql -U postgres -c "\dt"
```

### Clear Data

```bash
# Truncate table (keep structure)
docker exec chunking-expt-postgres psql -U postgres -c "TRUNCATE TABLE fixed_chunks RESTART IDENTITY;"
```

## File Structure

```
3_database/
├── docker/
│   ├── docker-compose.yml       # Docker configuration
│   ├── postgres/
│   │   ├── postgresql.conf      # PostgreSQL config (IPv4-only)
│   │   ├── pg_hba.conf         # Authentication config
│   │   └── init/               # Initialization scripts
│   │       ├── 01-extensions.sql
│   │       ├── 02-schema.sql
│   │       └── 03-functions.sql
├── fixed_chunks/               # Fixed chunks strategy
│   └── scripts/
│       ├── run_embedding_pipeline.py  # Safe pipeline runner
│       └── db_fixed_chunks.py        # Direct loader
└── common/                     # Shared utilities
    └── setup/
        └── generic_hybrid_search_template.sql
```

## Environment Variables

Required in `.env` file:
```bash
# OpenAI for embeddings
OPENAI_API_KEY=your-api-key

# Local database connection
SUPABASE_CONNECTION_STRING=postgresql://postgres:postgres@127.0.0.1:5432/postgres

# Docker PostgreSQL settings
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
```

## Quick Start Guide for New Team Members

### Prerequisites

1. **Install Docker Desktop**
   - Mac: https://www.docker.com/products/docker-desktop/
   - Ensure Docker is running (whale icon in menu bar)

2. **Install uv** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd chunking-expt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env  # If example exists
   # Edit .env and add your OPENAI_API_KEY
   ```

### Getting Started

1. **Run the automated setup**
   ```bash
   ./3_database/setup_local_supabase.sh
   ```
   Choose option 1 when prompted to load sample data.

2. **Verify everything is working**
   ```bash
   uv run python 3_database/scripts/verify_local_setup.py
   ```

3. **Run a test search**
   ```bash
   uv run python 3_database/fixed_chunks/tests/test_hybrid_search.py
   ```

### Daily Usage

**Start the database:**
```bash
cd 3_database/docker && docker compose up -d
```

**Stop the database:**
```bash
cd 3_database/docker && docker compose down
```

**Load new data:**
```bash
uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py
```

**Run searches:**
```python
from common.hybrid_search import HybridSearch

searcher = HybridSearch("fixed_chunks")
results = searcher.search("AI safety", match_count=10)
```

### GUI Access

Use TablePlus for visual database exploration:
1. Download from https://tableplus.com/
2. Create new connection:
   - Type: PostgreSQL
   - Host: 127.0.0.1
   - Port: 5432
   - User: postgres
   - Password: postgres
   - Database: postgres
   - SSL: Disable

### Common Tasks

**Add a new chunking strategy:**
1. Create new table with same schema (change table name)
2. Use template at `common/setup/generic_hybrid_search_template.sql`
3. Replace `{TABLE_NAME}` with your table name
4. Load data using `ChunkEmbedder` class

**Run performance tests:**
```bash
uv run python 3_database/scripts/test_pipeline_automated.py
```

**Debug connection issues:**
```bash
uv run python 3_database/scripts/verify_local_setup.py
```