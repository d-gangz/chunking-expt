"""
Simple script to retrieve raw data from fixed_chunks table exactly as stored in database.
"""

import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def retrieve_raw_chunks():
    """Retrieve all data from fixed_chunks table exactly as stored."""
    conn = psycopg2.connect(os.getenv("SUPABASE_CONNECTION_STRING"))
    cur = conn.cursor()
    
    try:
        # Get all columns except embedding (too large)
        query = """
            SELECT 
                id,
                text,
                title,
                cue_start,
                cue_end,
                created_at
            FROM fixed_chunks
            ORDER BY id
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        # Convert to list of dictionaries - exactly as in database
        chunks = []
        for row in rows:
            chunk = {
                'id': row[0],
                'text': row[1],
                'title': row[2],
                'cue_start': row[3],
                'cue_end': row[4],
                'created_at': str(row[5]) if row[5] else None
            }
            chunks.append(chunk)
        
        print(f"Retrieved {len(chunks)} chunks from database")
        return chunks
        
    finally:
        cur.close()
        conn.close()


def main():
    """Main function to retrieve and save raw chunks."""
    chunks = retrieve_raw_chunks()
    
    # Save raw data
    output_path = "/Users/gang/suite-work/chunking-expt/4_labelled_dataset/fixed_chunks/raw_chunks_from_db.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2)
    
    print(f"Saved raw chunks to {output_path}")


if __name__ == "__main__":
    main()