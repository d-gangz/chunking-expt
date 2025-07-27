"""
Verify database setup by checking table schema and indexes.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def verify_database_setup():
    """Verify that the database is properly set up."""
    connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 Verifying database setup...")
        print("-" * 50)
        
        # Check if pgvector extension is enabled
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        vector_ext = cur.fetchone()
        if vector_ext:
            print("✅ pgvector extension is enabled")
        else:
            print("❌ pgvector extension is NOT enabled")
            print("   Please enable it in Supabase Dashboard")
        
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'fixed_chunks'
            );
        """)
        table_exists = cur.fetchone()['exists']
        
        if table_exists:
            print("✅ Table 'fixed_chunks' exists")
            
            # Check table columns
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'fixed_chunks'
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            
            print("\n📋 Table columns:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"   - {col['column_name']}: {col['data_type']} {nullable}")
            
            # Check indexes
            cur.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'fixed_chunks';
            """)
            indexes = cur.fetchall()
            
            print("\n🔍 Indexes:")
            for idx in indexes:
                print(f"   - {idx['indexname']}")
                if 'hnsw' in idx['indexdef']:
                    print("     Type: HNSW (vector search)")
                elif 'gin' in idx['indexdef']:
                    print("     Type: GIN (full-text search)")
                elif 'btree' in idx['indexdef']:
                    print("     Type: B-tree")
            
            # Check row count
            cur.execute("SELECT COUNT(*) as count FROM fixed_chunks;")
            row_count = cur.fetchone()['count']
            print(f"\n📊 Row count: {row_count}")
            
        else:
            print("❌ Table 'fixed_chunks' does NOT exist")
            print("   Run supabase_setup.py to create it")
        
        print("\n✅ Verification complete!")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        print("\nPossible issues:")
        print("1. Check your SUPABASE_CONNECTION_STRING in .env")
        print("2. Ensure your Supabase database is accessible")
        print("3. Make sure pgvector extension is enabled")
        return False
        
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    verify_database_setup()