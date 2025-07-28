"""
Generic chunk embedder that can work with any chunk table.
Processes chunks from JSON files, generates embeddings, and stores them in Supabase.
"""

import os
import json
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Optional
from tqdm import tqdm
from dotenv import load_dotenv

# Handle both module and script execution
try:
    from .embedding_utils import EmbeddingGenerator
except ImportError:
    from embedding_utils import EmbeddingGenerator

load_dotenv()

class ChunkEmbedder:
    def __init__(self, table_name: str, batch_size: int = 100):
        """
        Initialize the ChunkEmbedder for a specific table.
        
        Args:
            table_name: Name of the database table (e.g., "fixed_chunks", "tool_chunks")
            batch_size: Number of chunks to process in each batch (default: 100)
        """
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {table_name}. Only alphanumeric characters and underscores allowed.")
        
        self.table_name = table_name
        self.embedding_generator = EmbeddingGenerator(
            model="text-embedding-3-large",
            dimensions=1024
        )
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        self.batch_size = batch_size
        self.checkpoint_file = f"{table_name}_embedding_checkpoint.json"
        
    def load_chunks_from_json(self, json_path: str) -> List[Dict]:
        """
        Load chunks from a JSON file, excluding the 'chunk_id' field.
        
        Args:
            json_path: Path to the JSON file containing chunks
            
        Returns:
            List of chunk dictionaries
        """
        print(f"Loading chunks from {json_path}...")
        with open(json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Remove chunk_id from each chunk if present
        for chunk in chunks:
            chunk.pop('chunk_id', None)
        
        print(f"Loaded {len(chunks)} chunks")
        return chunks
    
    def load_checkpoint(self) -> int:
        """Load the last processed index from checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                return checkpoint.get('last_processed_index', 0)
        return 0
    
    def save_checkpoint(self, index: int):
        """Save the current processing index to checkpoint file."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump({'last_processed_index': index}, f)
    
    def insert_chunks_batch(self, chunks_with_embeddings: List[Dict], conn):
        """
        Insert a batch of chunks with embeddings into the database.
        
        Args:
            chunks_with_embeddings: List of chunks with their embeddings
            conn: Database connection
        """
        cur = conn.cursor()
        
        try:
            # Prepare data for batch insert
            insert_data = [
                (
                    chunk['text'],
                    chunk.get('title', ''),
                    chunk.get('cue_start', 0),
                    chunk.get('cue_end', 0),
                    chunk['embedding']
                )
                for chunk in chunks_with_embeddings
            ]
            
            # Batch insert using execute_batch for better performance
            insert_query = f"""
                INSERT INTO {self.table_name} 
                (text, title, cue_start, cue_end, embedding) 
                VALUES (%s, %s, %s, %s, %s)
            """
            
            execute_batch(cur, insert_query, insert_data, page_size=self.batch_size)
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error inserting batch: {e}")
            raise
        finally:
            cur.close()
    
    def process_chunks(self, chunks: List[Dict], resume_from: int = 0):
        """
        Process chunks: generate embeddings and insert into database.
        
        Args:
            chunks: List of chunk dictionaries
            resume_from: Index to resume processing from (for checkpoint recovery)
        """
        if resume_from > 0:
            print(f"Resuming from chunk {resume_from}")
            chunks = chunks[resume_from:]
        
        # Estimate cost
        texts = [chunk['text'] for chunk in chunks]
        total_tokens, estimated_cost = self.embedding_generator.estimate_cost(texts)
        
        print(f"\nProcessing {len(chunks)} chunks")
        print(f"Estimated tokens: {total_tokens:,}")
        print(f"Estimated cost: ${estimated_cost:.4f}")
        
        # Check for texts that exceed token limits
        issues = self.embedding_generator.validate_texts(texts)
        if issues:
            print(f"\nWarning: {len(issues)} chunks exceed token limit!")
            for idx, tokens in issues[:5]:  # Show first 5 issues
                print(f"  - Chunk {idx + resume_from}: {tokens} tokens")
        
        # Connect to database
        conn = psycopg2.connect(self.connection_string)
        
        try:
            # Process in batches
            for i in tqdm(range(0, len(chunks), self.batch_size), desc=f"Processing {self.table_name}"):
                batch = chunks[i:i + self.batch_size]
                batch_texts = [chunk['text'] for chunk in batch]
                
                # Generate embeddings
                embeddings = self.embedding_generator.create_embeddings_with_retry(batch_texts)
                
                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    chunk['embedding'] = embedding
                
                # Insert batch into database
                self.insert_chunks_batch(batch, conn)
                
                # Save checkpoint
                self.save_checkpoint(resume_from + i + len(batch))
            
            print(f"\n✅ Successfully processed {len(chunks)} chunks into {self.table_name}")
            
            # Clean up checkpoint file
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            print(f"Progress saved. You can resume from chunk {resume_from + i}")
            raise
        finally:
            conn.close()
    
    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the database table."""
        conn = psycopg2.connect(self.connection_string)
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cur.fetchone()[0]
            cur.close()
            return count
        finally:
            conn.close()
    
    def clear_table(self):
        """Clear all data from the table (use with caution!)."""
        response = input(f"⚠️  This will delete all data from {self.table_name}. Are you sure? (yes/no): ")
        if response.lower() == 'yes':
            conn = psycopg2.connect(self.connection_string)
            try:
                cur = conn.cursor()
                cur.execute(f"TRUNCATE TABLE {self.table_name}")
                conn.commit()
                cur.close()
                print(f"✅ Table {self.table_name} cleared")
            finally:
                conn.close()
        else:
            print("Operation cancelled")


def main():
    """Example usage of the generic ChunkEmbedder."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process chunks and generate embeddings")
    parser.add_argument("table_name", help="Name of the database table")
    parser.add_argument("json_path", help="Path to the chunks JSON file")
    parser.add_argument("--clear", action="store_true", help="Clear table before inserting")
    
    args = parser.parse_args()
    
    # Initialize embedder for the specified table
    embedder = ChunkEmbedder(args.table_name)
    
    # Clear table if requested
    if args.clear:
        embedder.clear_table()
    
    # Load chunks
    chunks = embedder.load_chunks_from_json(args.json_path)
    
    # Check for existing checkpoint
    resume_from = embedder.load_checkpoint()
    
    # Process chunks
    embedder.process_chunks(chunks, resume_from)
    
    # Show final count
    final_count = embedder.get_chunk_count()
    print(f"\nTotal chunks in {args.table_name}: {final_count:,}")


if __name__ == "__main__":
    main()