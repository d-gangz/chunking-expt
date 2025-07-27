"""
Script to check if pgvector extension is enabled in Supabase.
Run this after manually enabling the extension in Supabase Dashboard.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_pgvector_extension():
    """Check if pgvector extension is enabled in the database."""
    try:
        conn = psycopg2.connect(os.getenv("SUPABASE_CONNECTION_STRING"))
        cur = conn.cursor()
        
        # Check if vector extension exists
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        result = cur.fetchone()
        
        if result:
            print("✅ pgvector extension is enabled!")
            print(f"   Extension details: {result}")
            return True
        else:
            print("❌ pgvector extension is NOT enabled.")
            print("\nTo enable it:")
            print("1. Go to your Supabase Dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Run: CREATE EXTENSION IF NOT EXISTS vector;")
            return False
            
    except Exception as e:
        print(f"❌ Error checking pgvector: {e}")
        return False
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_pgvector_extension()