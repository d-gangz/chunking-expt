"""
Quick validation script to check database integrity and data quality.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def quick_validation():
    """Run quick validation checks on the database."""
    connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
    
    print("🔍 QUICK VALIDATION CHECKS")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check 1: Row count vs source file
        print("\n1. Checking row count...")
        cur.execute("SELECT COUNT(*) as count FROM fixed_chunks")
        db_count = cur.fetchone()['count']
        
        # Load source file to compare
        json_path = "/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/all_chunks_combined.json"
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                chunks = json.load(f)
            source_count = len(chunks)
            
            print(f"   Database chunks: {db_count:,}")
            print(f"   Source file chunks: {source_count:,}")
            
            if db_count == source_count:
                print("   ✅ Counts match!")
            else:
                print(f"   ⚠️  Mismatch: {abs(db_count - source_count)} difference")
        else:
            print(f"   Database chunks: {db_count:,}")
            print("   ⚠️  Cannot verify against source file")
        
        # Check 2: Embedding dimensions
        print("\n2. Checking embedding dimensions...")
        cur.execute("""
            SELECT 
                MIN(array_length(embedding::float[], 1)) as min_dim,
                MAX(array_length(embedding::float[], 1)) as max_dim,
                AVG(array_length(embedding::float[], 1)) as avg_dim
            FROM fixed_chunks
            WHERE embedding IS NOT NULL
        """)
        dims = cur.fetchone()
        
        if dims['min_dim'] == dims['max_dim'] == 1024:
            print(f"   ✅ All embeddings have 1024 dimensions")
        else:
            print(f"   ❌ Dimension mismatch: min={dims['min_dim']}, max={dims['max_dim']}, avg={dims['avg_dim']:.2f}")
        
        # Check 3: Data quality
        print("\n3. Checking data quality...")
        
        # Check for null values
        cur.execute("""
            SELECT 
                SUM(CASE WHEN text IS NULL THEN 1 ELSE 0 END) as null_text,
                SUM(CASE WHEN title IS NULL THEN 1 ELSE 0 END) as null_title,
                SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as null_embedding
            FROM fixed_chunks
        """)
        nulls = cur.fetchone()
        
        null_issues = []
        for field, count in nulls.items():
            if count > 0:
                null_issues.append(f"{field}: {count}")
        
        if null_issues:
            print(f"   ⚠️  Found null values: {', '.join(null_issues)}")
        else:
            print("   ✅ No null values found")
        
        # Check text lengths
        cur.execute("""
            SELECT 
                MIN(LENGTH(text)) as min_len,
                MAX(LENGTH(text)) as max_len,
                AVG(LENGTH(text)) as avg_len
            FROM fixed_chunks
        """)
        lengths = cur.fetchone()
        
        print(f"   Text lengths: min={lengths['min_len']}, max={lengths['max_len']}, avg={lengths['avg_len']:.0f}")
        
        # Check 4: Sample data
        print("\n4. Sample data verification...")
        cur.execute("""
            SELECT title, chunk_index, total_chunks, cue_start, cue_end,
                   LENGTH(text) as text_len,
                   array_length(embedding::float[], 1) as embedding_dim
            FROM fixed_chunks
            ORDER BY RANDOM()
            LIMIT 5
        """)
        samples = cur.fetchall()
        
        print("   Random samples:")
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. {sample['title']} - Chunk {sample['chunk_index']}/{sample['total_chunks']}")
            print(f"      Time: {sample['cue_start']:.1f}s - {sample['cue_end']:.1f}s")
            print(f"      Text length: {sample['text_len']} chars, Embedding: {sample['embedding_dim']}D")
        
        # Check 5: Index usage
        print("\n5. Checking index health...")
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE tablename = 'fixed_chunks'
        """)
        indexes = cur.fetchall()
        
        if indexes:
            print("   Index usage statistics:")
            for idx in indexes:
                print(f"   - {idx['indexname']}: {idx['idx_scan']} scans")
        else:
            print("   ⚠️  No index statistics available yet")
        
        print("\n" + "=" * 80)
        print("✅ Quick validation complete!")
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    quick_validation()