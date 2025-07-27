"""
Supabase database setup script for fixed chunks table and indexes.
Creates the table schema and necessary indexes for hybrid search.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class SupabaseSetup:
    def __init__(self):
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        
    def create_table(self):
        """Create the fixed_chunks table with vector column."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS fixed_chunks (
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
        """
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            cur.execute(create_table_sql)
            conn.commit()
            print("✅ Table 'fixed_chunks' created successfully")
            
            # Check if table was created
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'fixed_chunks'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            print("\nTable columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
                
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def create_indexes(self):
        """Create indexes for efficient hybrid search."""
        indexes = [
            # HNSW index for vector search (cosine similarity)
            """
            CREATE INDEX IF NOT EXISTS fixed_chunks_embedding_hnsw_idx
            ON fixed_chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """,
            
            # GIN index for full-text search
            """
            CREATE INDEX IF NOT EXISTS fixed_chunks_text_gin_idx
            ON fixed_chunks
            USING GIN (to_tsvector('english', text));
            """,
            
            # B-tree index on title for keyword search
            """
            CREATE INDEX IF NOT EXISTS fixed_chunks_title_idx
            ON fixed_chunks (title);
            """
        ]
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            for i, index_sql in enumerate(indexes):
                cur.execute(index_sql)
                index_type = ["HNSW (vector)", "GIN (text)", "B-tree (title)"][i]
                print(f"✅ Created {index_type} index")
                
            conn.commit()
            
            # Verify indexes
            cur.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'fixed_chunks';
            """)
            
            indexes = cur.fetchall()
            print("\nCreated indexes:")
            for idx_name, idx_def in indexes:
                print(f"  - {idx_name}")
                
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    
    def setup_database(self):
        """Run complete database setup."""
        print("Starting Supabase database setup...")
        print("-" * 50)
        
        # Create table
        self.create_table()
        print()
        
        # Create indexes
        self.create_indexes()
        print()
        
        print("✅ Database setup complete!")
        
    def drop_table(self):
        """Drop the fixed_chunks table (use with caution!)."""
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            cur.execute("DROP TABLE IF EXISTS fixed_chunks CASCADE;")
            conn.commit()
            print("✅ Table 'fixed_chunks' dropped")
            
        except Exception as e:
            print(f"❌ Error dropping table: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()


if __name__ == "__main__":
    setup = SupabaseSetup()
    
    # Run the setup
    setup.setup_database()
    
    # Note: To reset the database, uncomment the following line:
    # setup.drop_table()