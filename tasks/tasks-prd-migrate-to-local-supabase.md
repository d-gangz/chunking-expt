## Relevant Files

- `3_database/docker/docker-compose.yml` - Docker Compose configuration for local Supabase PostgreSQL instance
- `3_database/docker/postgres/init/01-extensions.sql` - SQL script to enable pgvector and other required extensions
- `3_database/docker/postgres/init/02-schema.sql` - Database schema initialization from existing setup
- `3_database/docker/postgres/init/03-functions.sql` - Hybrid search functions and stored procedures
- `3_database/scripts/verify_local_setup.py` - Health check script for local Supabase
- `3_database/fixed_chunks/scripts/run_embedding_pipeline.py` - Existing pipeline script to test with local DB
- `3_database/fixed_chunks/scripts/db_fixed_chunks.py` - Existing direct insertion script to test with local DB
- `3_database/README.md` - Setup instructions and migration guide
- `.env` - Update with local connection string and Docker credentials

### Notes

- Leverage all existing SQL files from `3_database/fixed_chunks/setup/` directory
- No changes needed to existing Python code - only connection string update
- Use `uv run python` for all Python script execution as per CLAUDE.md
- Docker data will be stored in named volumes for better performance

## Key Implementation Details from Research

### Supabase Docker PostgreSQL

- **Docker Image**: `supabase/postgres:15.1.0.151` (includes pgvector)
- **Volume Mapping**: Use named volumes for PostgreSQL data persistence
- **Health Checks**: Built-in `pg_isready` command with retry logic
- **Memory Settings**: Configure shared_buffers (256MB), work_mem (16MB) for vector operations
- **Connection Format**: `postgresql://postgres:password@localhost:5432/database`

### Existing Codebase Integration

- **Current Setup Scripts**: Reuse `supabase_setup.py`, `enable_pgvector.sql`, `hybrid_search_function.sql`
- **Embedding Pipeline**: Use existing `run_embedding_pipeline.py` for data loading
- **Vector Dimensions**: 1024 (matching current OpenAI text-embedding-3-large setup)
- **Table Structure**: Maintain exact schema from `fixed_chunks` table

## Tasks

- [ ] 1.0 Set up Docker infrastructure for local Supabase PostgreSQL
  - [ ] 1.1 Create Docker Compose configuration file at `3_database/docker/docker-compose.yml`
    ```yaml
    # Use supabase/postgres:15.1.0.151 image with pgvector included
    # Configure health checks, volumes, and PostgreSQL settings
    ```
  - [ ] 1.2 Configure Docker Compose to use environment variables from root `.env` file
    ```yaml
    # docker-compose.yml will reference ../../.env for database credentials
    # Use env_file: ../../.env in Docker Compose configuration
    ```
  - [ ] 1.3 Set up directory structure for Docker initialization scripts
    ```bash
    mkdir -p 3_database/docker/postgres/init
    ```
  - [ ] 1.4 Configure named Docker volumes for PostgreSQL data persistence
  - [ ] 1.5 Add memory and performance tuning parameters to docker-compose command section

- [ ] 2.0 Configure database initialization and schema migration
  - [ ] 2.1 Create `01-extensions.sql` to enable pgvector extension
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
  - [ ] 2.2 Convert existing `fixed_chunks/scripts/supabase_setup.py` SQL to `02-schema.sql`
    ```python
    # Extract CREATE TABLE and CREATE INDEX statements from Python code
    ```
  - [ ] 2.3 Copy `fixed_chunks/setup/hybrid_search_function.sql` to `03-functions.sql`
  - [ ] 2.4 Create initialization script that maintains exact table schema (1024-dimension vectors)
  - [ ] 2.5 Ensure all indexes (HNSW, GIN, B-tree) are created during initialization

- [ ] 3.0 Verify and adapt existing data insertion scripts
  - [ ] 3.1 Test `fixed_chunks/scripts/run_embedding_pipeline.py` with local database
    ```bash
    # This script already handles complete pipeline with safety checks
    uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py
    ```
  - [ ] 3.2 Verify `fixed_chunks/scripts/db_fixed_chunks.py` works with local connection
    ```bash
    # Direct embedding and insertion script
    uv run python 3_database/fixed_chunks/scripts/db_fixed_chunks.py
    ```
  - [ ] 3.3 Ensure data from `2_chunks/fixed_chunks/chunks/all_chunks_combined.json` can be loaded
    ```python
    # Existing scripts already handle this JSON file
    # Just verify it works with local database
    ```
  - [ ] 3.4 Create README section documenting how to load initial data after setup

- [ ] 4.0 Update connection configuration for local Supabase
  - [ ] 4.1 Replace cloud connection string with local connection in `.env` file
    ```bash
    # Local Supabase Connection
    SUPABASE_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/postgres
    ```
  - [ ] 4.2 Add Docker database credentials to `.env` file
    ```bash
    # Docker PostgreSQL Configuration
    POSTGRES_PASSWORD=postgres
    POSTGRES_DB=postgres
    POSTGRES_USER=postgres
    ```
  - [ ] 4.3 Verify all existing scripts work with local connection string
  - [ ] 4.4 Test that `ChunkEmbedder`, `HybridSearch` classes work unchanged with local database

- [ ] 5.0 Implement verification and testing procedures
  - [ ] 5.1 Create `verify_local_setup.py` based on existing `verify_setup.py`
    ```python
    # Check Docker is running, database is accessible
    # Verify pgvector extension, table exists, indexes created
    ```
  - [ ] 5.2 Add health check endpoint to verify Docker PostgreSQL readiness
  - [ ] 5.3 Create test script to verify hybrid search works with local data
    ```python
    # Run sample searches, verify RRF scoring works correctly
    ```
  - [ ] 5.4 Implement automated test that runs complete pipeline locally
  - [ ] 5.5 Add comparison script to ensure local results match cloud results

- [ ] 6.0 Create documentation and setup automation
  - [ ] 6.1 Write comprehensive README.md with step-by-step setup instructions
  - [ ] 6.2 Create one-command setup script `setup_local_supabase.sh`
    ```bash
    #!/bin/bash
    # Start Docker, wait for readiness
    # Run existing supabase_setup.py to create tables
    # Load initial data using existing pipeline scripts
    ```
  - [ ] 6.3 Document how to use existing data loading scripts:
    ```markdown
    # After setup, load data using:
    uv run python 3_database/fixed_chunks/scripts/supabase_setup.py  # Create tables
    uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py  # Load data
    ```
  - [ ] 6.4 Document troubleshooting steps for common issues
  - [ ] 6.5 Create quick-start guide for new team members