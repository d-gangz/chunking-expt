"""
Direct database operations script that processes fixed chunks by generating OpenAI embeddings and inserting them into PostgreSQL with batch processing and checkpoint recovery.

Input data sources: 2_chunks/fixed_chunks/chunks/all_chunks_combined.json
Output destinations: PostgreSQL fixed_chunks table with vector embeddings
Dependencies: PostgreSQL with pgvector, OpenAI API (text-embedding-3-large), SUPABASE_CONNECTION_STRING env var, psycopg2
Key exports: ChunkEmbedder class, main() function
Side effects: Inserts chunks with embeddings to database, creates checkpoint files for resume capability
"""

import os
import json
import sys
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Optional
from tqdm import tqdm
from dotenv import load_dotenv

# Add parent directory to path to import from common
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.embedding_utils import EmbeddingGenerator

load_dotenv()

class ChunkEmbedder:
    def __init__(self, batch_size: int = 100):
        """
        Initialize the ChunkEmbedder with OpenAI client and database connection.
        
        Args:
            batch_size: Number of chunks to process in each batch (default: 100)
        """
        self.embedding_generator = EmbeddingGenerator(
            model="text-embedding-3-large",
            dimensions=1024
        )
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        self.batch_size = batch_size
        self.checkpoint_file = "embedding_checkpoint.json"
        
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
        
        # Remove chunk_id field if present
        for chunk in chunks:
            if 'chunk_id' in chunk:
                del chunk['chunk_id']
        
        print(f"Loaded {len(chunks)} chunks")
        return chunks
    
    def load_checkpoint(self) -> int:
        """Load the last processed chunk index from checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                return checkpoint.get('last_processed_index', 0)
        return 0
    
    def save_checkpoint(self, index: int):
        """Save the current processing progress."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump({'last_processed_index': index}, f)
    
    def insert_chunks_batch(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Insert a batch of chunks with their embeddings into the database.
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
        """
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor()
        
        try:
            # Prepare data for insertion
            insert_data = []
            for chunk, embedding in zip(chunks, embeddings):
                insert_data.append((
                    chunk['text'],
                    chunk['title'],
                    chunk['cue_start'],
                    chunk['cue_end'],
                    chunk['chunk_index'],
                    chunk['total_chunks'],
                    embedding
                ))
            
            # Use execute_batch for efficient insertion
            insert_query = """
                INSERT INTO fixed_chunks 
                (text, title, cue_start, cue_end, chunk_index, total_chunks, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            execute_batch(cur, insert_query, insert_data, page_size=self.batch_size)
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error inserting batch: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def process_chunks(self, json_path: str, resume: bool = True):
        """
        Process all chunks: generate embeddings and insert into database.
        
        Args:
            json_path: Path to the JSON file containing chunks
            resume: Whether to resume from checkpoint (default: True)
        """
        # Load chunks
        chunks = self.load_chunks_from_json(json_path)
        
        # Load checkpoint if resuming
        start_index = 0
        if resume:
            start_index = self.load_checkpoint()
            if start_index > 0:
                print(f"Resuming from chunk {start_index}")
        
        # Extract texts for embedding
        texts = [chunk['text'] for chunk in chunks]
        
        # Estimate cost
        total_tokens, estimated_cost = self.embedding_generator.estimate_cost(
            texts[start_index:]
        )
        print(f"\nEstimated embedding cost: ${estimated_cost:.4f}")
        print(f"Total tokens: {total_tokens:,}")
        
        # Validate texts
        issues = self.embedding_generator.validate_texts(texts[start_index:])
        if issues:
            print(f"\n⚠️  Warning: {len(issues)} texts exceed token limit!")
            for idx, token_count in issues[:5]:  # Show first 5 issues
                actual_idx = start_index + idx
                print(f"   Chunk {actual_idx}: {token_count} tokens")
        
        # Process in batches
        total_batches = (len(chunks) - start_index + self.batch_size - 1) // self.batch_size
        
        print(f"\nProcessing {len(chunks) - start_index} chunks in {total_batches} batches...")
        
        for i in tqdm(range(start_index, len(chunks), self.batch_size), 
                     desc="Processing chunks", 
                     initial=start_index // self.batch_size,
                     total=(len(chunks) + self.batch_size - 1) // self.batch_size):
            
            batch_chunks = chunks[i:i + self.batch_size]
            batch_texts = [chunk['text'] for chunk in batch_chunks]
            
            try:
                # Generate embeddings for batch
                batch_embeddings = self.embedding_generator.create_embeddings_with_retry(
                    batch_texts
                )
                
                # Insert batch into database
                self.insert_chunks_batch(batch_chunks, batch_embeddings)
                
                # Save checkpoint
                self.save_checkpoint(min(i + self.batch_size, len(chunks)))
                
            except Exception as e:
                print(f"\nError processing batch starting at index {i}: {e}")
                print("You can resume from this point by running the script again.")
                raise
        
        print(f"\n✅ Successfully processed and inserted {len(chunks)} chunks!")
        
        # Clean up checkpoint file
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("Checkpoint file removed.")
    
    def get_chunk_count(self) -> int:
        """Get the total number of chunks in the database."""
        conn = psycopg2.connect(self.connection_string)
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT COUNT(*) FROM fixed_chunks")
            count = cur.fetchone()[0]
            return count
        finally:
            cur.close()
            conn.close()


def main():
    """Main function to process chunks and generate embeddings."""
    # Path to the combined chunks file
    json_path = "/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/all_chunks_combined.json"
    
    # Check if file exists
    if not os.path.exists(json_path):
        print(f"❌ Error: File not found: {json_path}")
        print("Please ensure the chunks file exists at the specified path.")
        return
    
    # Initialize embedder
    embedder = ChunkEmbedder(batch_size=100)
    
    # Check current chunk count
    try:
        current_count = embedder.get_chunk_count()
        print(f"Current chunks in database: {current_count}")
    except Exception as e:
        print(f"Note: Could not check current chunk count: {e}")
    
    # Process chunks
    try:
        embedder.process_chunks(json_path, resume=True)
        
        # Verify final count
        final_count = embedder.get_chunk_count()
        print(f"\nFinal chunk count in database: {final_count}")
        
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure pgvector extension is enabled in Supabase")
        print("2. Verify your OPENAI_API_KEY is valid")
        print("3. Check your SUPABASE_CONNECTION_STRING")
        print("4. Run verify_setup.py to check database configuration")


if __name__ == "__main__":
    main()