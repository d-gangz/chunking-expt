#!/usr/bin/env python3
"""
Verification script for local Supabase setup.
Checks database connectivity, extensions, tables, and functions.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from dotenv import load_dotenv

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "3_database"))

from common.chunk_embedder import ChunkEmbedder
from common.hybrid_search import HybridSearch

load_dotenv()


def check_docker_running():
    """Check if Docker container is running."""
    print("🐳 Checking Docker container...")
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=chunking-expt-postgres", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        if "chunking-expt-postgres" in result.stdout:
            print("✅ Docker container is running")
            return True
        else:
            print("❌ Docker container is not running")
            print("   Run: cd 3_database/docker && docker compose up -d")
            return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def check_database_connection():
    """Check database connectivity."""
    print("\n🔌 Checking database connection...")
    conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    if not conn_string:
        print("❌ SUPABASE_CONNECTION_STRING not found in environment")
        return False
    
    if "127.0.0.1" not in conn_string and "localhost" not in conn_string:
        print("⚠️  WARNING: Connection string doesn't appear to be local")
        print(f"   Connection: {conn_string[:50]}...")
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def check_pgvector_extension():
    """Check if pgvector extension is installed."""
    print("\n🔍 Checking pgvector extension...")
    conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT extname, extversion 
            FROM pg_extension 
            WHERE extname = 'vector';
        """)
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            print(f"✅ pgvector extension installed")
            print(f"   Version: {result['extversion']}")
            return True
        else:
            print("❌ pgvector extension not found")
            return False
    except Exception as e:
        print(f"❌ Error checking extension: {e}")
        return False


def check_tables():
    """Check if required tables exist."""
    print("\n📊 Checking tables...")
    conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        # Check for fixed_chunks table
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'fixed_chunks'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            # Get row count
            cur.execute("SELECT COUNT(*) FROM fixed_chunks;")
            count = cur.fetchone()[0]
            print(f"✅ Table 'fixed_chunks' exists")
            print(f"   Rows: {count:,}")
            
            # Check indexes
            cur.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'fixed_chunks';
            """)
            indexes = cur.fetchall()
            print(f"   Indexes: {len(indexes)}")
            for idx_name, _ in indexes:
                print(f"     - {idx_name}")
        else:
            print("❌ Table 'fixed_chunks' not found")
            
        cur.close()
        conn.close()
        return table_exists
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False


def check_functions():
    """Check if hybrid search function exists."""
    print("\n🔧 Checking functions...")
    conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM pg_proc 
                WHERE proname = 'hybrid_search_fixed_chunks'
            );
        """)
        function_exists = cur.fetchone()[0]
        
        if function_exists:
            print("✅ Function 'hybrid_search_fixed_chunks' exists")
        else:
            print("❌ Function 'hybrid_search_fixed_chunks' not found")
            
        cur.close()
        conn.close()
        return function_exists
    except Exception as e:
        print(f"❌ Error checking functions: {e}")
        return False


def test_chunk_embedder():
    """Test ChunkEmbedder functionality."""
    print("\n🧪 Testing ChunkEmbedder...")
    try:
        embedder = ChunkEmbedder("fixed_chunks")
        count = embedder.get_chunk_count()
        print(f"✅ ChunkEmbedder working")
        print(f"   Chunks in database: {count:,}")
        return True
    except Exception as e:
        print(f"❌ ChunkEmbedder test failed: {e}")
        return False


def test_hybrid_search():
    """Test HybridSearch functionality."""
    print("\n🔎 Testing HybridSearch...")
    try:
        searcher = HybridSearch("fixed_chunks")
        results = searcher.search("AI safety", match_count=3)
        
        if results:
            print(f"✅ HybridSearch working")
            print(f"   Found {len(results)} results for 'AI safety'")
            print(f"   Top result: {results[0]['title']}")
        else:
            print("⚠️  HybridSearch returned no results (database might be empty)")
            
        return True
    except Exception as e:
        print(f"❌ HybridSearch test failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("🚀 LOCAL SUPABASE SETUP VERIFICATION")
    print("=" * 50)
    
    checks = [
        ("Docker Container", check_docker_running),
        ("Database Connection", check_database_connection),
        ("pgvector Extension", check_pgvector_extension),
        ("Tables", check_tables),
        ("Functions", check_functions),
        ("ChunkEmbedder", test_chunk_embedder),
        ("HybridSearch", test_hybrid_search),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            success = check_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:.<30} {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n✅ All checks passed! Local Supabase is ready to use.")
        print("\nNext steps:")
        print("- Load data: uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py")
        print("- Run tests: uv run python 3_database/fixed_chunks/tests/test_hybrid_search.py")
    else:
        print("\n❌ Some checks failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure Docker is running: docker ps")
        print("2. Check .env file has correct connection string")
        print("3. Restart container: cd 3_database/docker && docker compose down && docker compose up -d")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())