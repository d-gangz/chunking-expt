# PRD: Migrate from Supabase Cloud to Local Supabase Open-Source

## Introduction/Overview

This project currently uses Supabase Cloud for storing transcript chunks with vector embeddings and performing hybrid search (vector + keyword). The goal is to migrate to Supabase's open-source version running locally for experimentation purposes, with PostgreSQL data stored within the `3_database/` folder. This ensures all team members can access the same experimental data by cloning the repository, eliminating cloud dependencies while maintaining all existing functionality.

## Goals

1. Replace Supabase Cloud with local Supabase open-source (PostgreSQL + pgvector) for experimentation
2. Store PostgreSQL data directory within `3_database/` folder for team access
3. Maintain ALL existing functionality (vector embeddings, hybrid search, chunk storage)
4. Enable simple setup for team members who clone the repository
5. Provide sample data for immediate experimentation

## User Stories

1. **As a developer**, I want to clone the repository and run a local Supabase instance with all chunk data available, so that I can develop without cloud dependencies.

2. **As a team member**, I want to access the same chunk database as my colleagues without needing Supabase Cloud credentials, so that we can collaborate effectively.

3. **As a researcher**, I want to run hybrid search queries locally with the same performance as the cloud version, so that I can experiment without incurring costs.

4. **As a new contributor**, I want clear instructions to start the local Supabase instance and verify it's working, so that I can contribute immediately.

## Functional Requirements

1. **Local Supabase Setup**:

   - Use Docker Compose to run Supabase open-source stack
   - PostgreSQL data directory mapped to `3_database/postgres-data/`
   - pgvector extension enabled for vector similarity search
   - All existing SQL functions and indexes preserved

2. **Data Persistence**:

   - PostgreSQL data files stored in `3_database/postgres-data/`
   - SQL dump files in `3_database/dumps/` for easier Git storage
   - Import/export scripts for data management
   - Mock data automatically loaded on first run

3. **Code Compatibility**:

   - NO changes to existing Python code logic
   - Update connection string to point to local instance
   - Maintain all existing classes: `ChunkEmbedder`, `HybridSearch`, etc.
   - Same table schemas and column types

4. **Existing Features Preserved**:

   - Vector embeddings (1024 dimensions) using pgvector
   - Hybrid search with Reciprocal Rank Fusion (RRF)
   - HNSW indexing for fast vector search
   - Full-text search with GIN indexes
   - All SQL functions remain unchanged

5. **Setup Automation**:

   - Docker Compose configuration for one-command startup
   - Automatic pgvector extension installation
   - Database initialization with existing schemas
   - Mock data loading script

6. **Developer Experience**:
   - Single command to start: `docker-compose up`
   - Health check endpoint to verify setup
   - Clear logs showing database readiness
   - Simple connection string update in .env

## Non-Goals (Out of Scope)

1. Changing the database schema or search algorithms
2. Modifying existing Python code functionality
3. Implementing Supabase Auth, Storage, or Realtime features
4. Cloud deployment or remote access
5. Database clustering or replication

## Design Considerations

### File Structure

```
3_database/
├── docker/
│   ├── docker-compose.yml      # Supabase stack configuration
│   └── postgres/
│       └── init/              # Initialization scripts
│           ├── 01-extensions.sql
│           ├── 02-schema.sql
│           └── 03-functions.sql
├── postgres-data/             # PostgreSQL data directory (mapped volume)
├── dumps/                     # SQL dumps for version control
│   ├── schema.sql            # Table definitions
│   ├── functions.sql         # Hybrid search functions
│   └── mock_data.sql         # Sample data
├── scripts/
│   ├── export_data.py        # Export current data to SQL
│   ├── import_data.py        # Import SQL dumps
│   └── verify_setup.py       # Health check script
├── .env.local                # Local environment variables
└── README.md                 # Setup instructions
```

### Docker Compose Configuration

```yaml
version: "3.8"
services:
  postgres:
    image: supabase/postgres:15.1.0.117
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
```

### Connection String Update

```bash
# .env.local (for local development)
SUPABASE_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/postgres
```

## Technical Considerations

1. **Data Storage**:

   - Store sample data as SQL files (INSERT statements) that can be easily loaded
   - PostgreSQL data directory can be excluded from Git if it gets too large
   - For experimentation, a few hundred chunks of sample data is sufficient

2. **pgvector Compatibility**:

   - Ensure Docker image includes pgvector extension
   - Verify vector operations work with existing scripts

3. **Platform Compatibility**:
   - Docker Desktop required for Windows/macOS
   - Native Docker for Linux
   - Same setup process across all platforms

## Success Metrics

1. **Zero Code Changes**: All existing Python scripts work without modification
2. **Simple Setup**: Team member can start experimenting within 5 minutes of cloning
3. **Functionality**: Hybrid search works with sample data
4. **Data Accessibility**: Sample data visible immediately after `docker-compose up`

## Simple Migration Plan

### Step 1: Set Up Local PostgreSQL with Docker

1. Create Docker Compose configuration with Supabase PostgreSQL image
2. Map data directory to `3_database/postgres-data/`
3. Set up initialization scripts using existing SQL files

### Step 2: Initialize Database and Load Data

1. Run existing setup scripts in order:
   - `fixed_chunks/setup/enable_pgvector.sql` - Enable pgvector extension
   - `fixed_chunks/scripts/supabase_setup.py` - Create tables and indexes
   - `fixed_chunks/setup/hybrid_search_function.sql` - Add search functions
2. Load data using existing pipeline:
   - `fixed_chunks/scripts/run_embedding_pipeline.py` - Complete pipeline with safety checks
   - OR `fixed_chunks/scripts/db_fixed_chunks.py` - Direct embedding and insertion
3. Verify setup with `fixed_chunks/tests/verify_setup.py`

### Step 3: Update Connection

1. tell user to update their `.env` with local connection string.
2. Test existing scripts work without modification
3. Document setup process in README

## Setup Instructions (Draft)

```bash
# 1. Clone the repository
git clone <repo-url>
cd chunking-expt

# 2. Navigate to database directory
cd 3_database

# 3. Start Supabase PostgreSQL locally
docker-compose up -d

# 4. Wait for PostgreSQL to be ready (about 30 seconds)
docker-compose logs -f postgres  # Watch logs to see when ready

# 5. Set up database schema and extensions
# Run the setup script which creates tables and indexes
uv run python fixed_chunks/scripts/supabase_setup.py

# 6. Verify the setup is working
uv run python fixed_chunks/tests/verify_setup.py

# 7. Load data using the existing pipeline
# This will generate embeddings and insert chunks
uv run python fixed_chunks/scripts/run_embedding_pipeline.py

# 8. Test hybrid search functionality
uv run python fixed_chunks/tests/test_hybrid_search.py
```

## Open Questions

1. How much sample data should we include for experimentation? (A few hundred chunks should be sufficient)
2. Should we document schema changes when they occur, or just update the SQL files?

## Next Steps

1. Create Docker Compose configuration with Supabase PostgreSQL image
2. Configure initialization to use existing SQL files
3. Test the complete pipeline with existing scripts:
   - `supabase_setup.py` - Creates tables and indexes automatically
   - `run_embedding_pipeline.py` - Handles the complete embedding and insertion process
   - `verify_setup.py` - Validates everything is working
4. Create a small sample dataset from existing chunks for quick experimentation
5. Document any environment variable changes needed (just the connection string)
