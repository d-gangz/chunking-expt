#!/bin/bash

# Setup script for local Supabase PostgreSQL with pgvector
# This script automates the complete setup process

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$SCRIPT_DIR/docker"

echo -e "${GREEN}🚀 Local Supabase Setup Script${NC}"
echo "=========================================="

# Check prerequisites
echo -e "\n${YELLOW}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed and running${NC}"

# Check Python and uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install uv first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ uv is installed${NC}"

# Check .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ .env file not found in project root${NC}"
    echo "Please create .env file with required variables"
    exit 1
fi

# Check for required environment variables
if ! grep -q "OPENAI_API_KEY" "$PROJECT_ROOT/.env"; then
    echo -e "${RED}❌ OPENAI_API_KEY not found in .env file${NC}"
    exit 1
fi

if ! grep -q "SUPABASE_CONNECTION_STRING.*127.0.0.1" "$PROJECT_ROOT/.env"; then
    echo -e "${YELLOW}⚠️  Warning: SUPABASE_CONNECTION_STRING doesn't appear to be pointing to local database${NC}"
    echo "Expected: postgresql://postgres:postgres@127.0.0.1:5432/postgres"
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Start Docker containers
echo -e "\n${YELLOW}🐳 Starting Docker containers...${NC}"
cd "$DOCKER_DIR"

# Check if container is already running
if docker ps --format '{{.Names}}' | grep -q "chunking-expt-postgres"; then
    echo -e "${GREEN}✅ Container already running${NC}"
else
    docker compose up -d
    echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
    
    # Wait for database to be ready
    MAX_ATTEMPTS=30
    ATTEMPT=0
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if docker exec chunking-expt-postgres pg_isready -U postgres &> /dev/null; then
            echo -e "${GREEN}✅ Database is ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
        ATTEMPT=$((ATTEMPT + 1))
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo -e "\n${RED}❌ Database failed to start in time${NC}"
        exit 1
    fi
fi

# Verify setup
echo -e "\n${YELLOW}🔍 Verifying setup...${NC}"
cd "$PROJECT_ROOT"

if uv run python 3_database/scripts/verify_local_setup.py; then
    echo -e "\n${GREEN}✅ Setup verification passed${NC}"
else
    echo -e "\n${RED}❌ Setup verification failed${NC}"
    exit 1
fi

# Optional: Load initial data
echo -e "\n${YELLOW}📦 Data Loading Options:${NC}"
echo "1. Load data using safe pipeline (recommended):"
echo "   uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py"
echo ""
echo "2. Load data directly:"
echo "   uv run python 3_database/fixed_chunks/scripts/db_fixed_chunks.py"
echo ""
echo "3. Skip data loading for now"
echo ""
read -p "Choose an option (1/2/3): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}📥 Loading data with safe pipeline...${NC}"
        uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py
        ;;
    2)
        echo -e "\n${YELLOW}📥 Loading data directly...${NC}"
        uv run python 3_database/fixed_chunks/scripts/db_fixed_chunks.py
        ;;
    3)
        echo -e "${YELLOW}⏭️  Skipping data loading${NC}"
        ;;
    *)
        echo -e "${YELLOW}⏭️  Invalid choice, skipping data loading${NC}"
        ;;
esac

# Run automated test
echo -e "\n${YELLOW}🧪 Running automated pipeline test...${NC}"
if uv run python 3_database/scripts/test_pipeline_automated.py; then
    echo -e "\n${GREEN}✅ Pipeline test passed${NC}"
else
    echo -e "\n${RED}❌ Pipeline test failed${NC}"
    echo "Check the errors above for details"
fi

# Success message
echo -e "\n${GREEN}🎉 Local Supabase setup complete!${NC}"
echo ""
echo "📚 Quick Reference:"
echo "  - Start database: cd 3_database/docker && docker compose up -d"
echo "  - Stop database: cd 3_database/docker && docker compose down"
echo "  - View logs: docker logs chunking-expt-postgres --tail 50"
echo "  - Connect with TablePlus: Host=127.0.0.1, Port=5432, User=postgres, Password=postgres"
echo "  - Run tests: uv run python 3_database/fixed_chunks/tests/test_hybrid_search.py"
echo ""
echo "For more information, see 3_database/README.md"