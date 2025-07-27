"""
Comprehensive test script to verify the complete database setup.
Checks pgvector extension, table schema, indexes, and function availability.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def test_database_setup():
    """Run comprehensive tests on database setup."""
    connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    all_tests_passed = True
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 DATABASE SETUP VERIFICATION")
        print("=" * 80)
        
        # Test 1: pgvector extension
        print("\n1. Checking pgvector extension...")
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        vector_ext = cur.fetchone()
        if vector_ext:
            print("   ✅ pgvector extension is enabled")
        else:
            print("   ❌ pgvector extension is NOT enabled")
            print("      ACTION: Enable it in Supabase Dashboard SQL Editor:")
            print("      CREATE EXTENSION IF NOT EXISTS vector;")
            all_tests_passed = False
        
        # Test 2: Table existence
        print("\n2. Checking fixed_chunks table...")
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fixed_chunks'
            );
        """)
        table_exists = cur.fetchone()['exists']
        
        if table_exists:
            print("   ✅ Table 'fixed_chunks' exists")
            
            # Check columns
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'fixed_chunks'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            expected_columns = {
                'id': 'integer',
                'text': 'text',
                'title': 'text',
                'cue_start': 'double precision',
                'cue_end': 'double precision',
                'chunk_index': 'integer',
                'total_chunks': 'integer',
                'embedding': 'USER-DEFINED',  # vector type
                'created_at': 'timestamp without time zone'
            }
            
            print("   Checking column schema...")
            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                if col_name in expected_columns:
                    if col_type == expected_columns[col_name] or (col_name == 'embedding' and col_type == 'USER-DEFINED'):
                        print(f"      ✅ {col_name}: {col_type}")
                    else:
                        print(f"      ❌ {col_name}: {col_type} (expected: {expected_columns[col_name]})")
                        all_tests_passed = False
                else:
                    print(f"      ⚠️  Unexpected column: {col_name}")
        else:
            print("   ❌ Table 'fixed_chunks' does NOT exist")
            print("      ACTION: Run supabase_setup.py")
            all_tests_passed = False
        
        # Test 3: Indexes
        print("\n3. Checking indexes...")
        cur.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'fixed_chunks';
        """)
        indexes = cur.fetchall()
        
        expected_indexes = {
            'fixed_chunks_embedding_hnsw_idx': 'HNSW',
            'fixed_chunks_text_gin_idx': 'GIN',
            'fixed_chunks_title_idx': 'B-tree'
        }
        
        found_indexes = {idx['indexname']: idx['indexdef'] for idx in indexes}
        
        for idx_name, idx_type in expected_indexes.items():
            if idx_name in found_indexes:
                print(f"   ✅ {idx_name} ({idx_type})")
            else:
                print(f"   ❌ Missing index: {idx_name} ({idx_type})")
                all_tests_passed = False
        
        # Test 4: Hybrid search function
        print("\n4. Checking hybrid search function...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_proc 
                WHERE proname = 'hybrid_search_fixed_chunks'
            );
        """)
        function_exists = cur.fetchone()['exists']
        
        if function_exists:
            print("   ✅ hybrid_search_fixed_chunks function exists")
        else:
            print("   ❌ hybrid_search_fixed_chunks function does NOT exist")
            print("      ACTION: Run hybrid_search_function.sql in Supabase Dashboard")
            all_tests_passed = False
        
        # Test 5: Data statistics
        print("\n5. Checking data statistics...")
        cur.execute("SELECT COUNT(*) as count FROM fixed_chunks;")
        row_count = cur.fetchone()['count']
        print(f"   Total chunks in database: {row_count:,}")
        
        if row_count > 0:
            # Check embedding dimensions
            cur.execute("""
                SELECT array_length(embedding::float[], 1) as dimensions 
                FROM fixed_chunks 
                LIMIT 1;
            """)
            dimensions = cur.fetchone()['dimensions']
            if dimensions == 1024:
                print(f"   ✅ Embedding dimensions: {dimensions}")
            else:
                print(f"   ❌ Embedding dimensions: {dimensions} (expected: 1024)")
                all_tests_passed = False
            
            # Sample data
            cur.execute("""
                SELECT title, cue_start, cue_end, LENGTH(text) as text_length
                FROM fixed_chunks
                LIMIT 3;
            """)
            samples = cur.fetchall()
            print("\n   Sample chunks:")
            for sample in samples:
                print(f"      - {sample['title']} ({sample['cue_start']:.1f}s - {sample['cue_end']:.1f}s): {sample['text_length']} chars")
        
        print("\n" + "=" * 80)
        
        if all_tests_passed:
            print("✅ ALL TESTS PASSED! Database is properly configured.")
        else:
            print("❌ Some tests failed. Please address the issues above.")
        
        return all_tests_passed
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        print("\nPossible issues:")
        print("1. Check your SUPABASE_CONNECTION_STRING in .env")
        print("2. Ensure your Supabase database is accessible")
        print("3. Check network connectivity")
        return False
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    test_database_setup()