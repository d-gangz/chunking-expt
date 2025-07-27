"""
Script to run the full embedding pipeline with safety checks.
Guides through the process of generating embeddings and inserting into database.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def check_prerequisites():
    """Check if all prerequisites are met before running the pipeline."""
    print("🔍 Checking prerequisites...")
    print("-" * 50)
    
    all_good = True
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in .env")
        all_good = False
    else:
        print("✅ OPENAI_API_KEY found")
    
    if not os.getenv("SUPABASE_CONNECTION_STRING"):
        print("❌ SUPABASE_CONNECTION_STRING not found in .env")
        all_good = False
    else:
        print("✅ SUPABASE_CONNECTION_STRING found")
    
    # Check input file
    chunks_file = "/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/all_chunks_combined.json"
    if not os.path.exists(chunks_file):
        print(f"❌ Chunks file not found: {chunks_file}")
        all_good = False
    else:
        print("✅ Chunks file found")
    
    return all_good

def main():
    """Main function to run the embedding pipeline."""
    print("🚀 EMBEDDING PIPELINE RUNNER")
    print("=" * 80)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix the issues above.")
        return
    
    print("\n✅ All prerequisites met!")
    
    # Import and run verification
    print("\n" + "=" * 80)
    print("STEP 1: Verifying database setup...")
    print("=" * 80)
    
    try:
        # Add parent directory to path to import from tests folder
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from tests.test_database_setup import test_database_setup
        if not test_database_setup():
            print("\n❌ Database setup verification failed. Please fix the issues above.")
            return
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return
    
    # Get user confirmation
    print("\n" + "=" * 80)
    print("STEP 2: Ready to generate embeddings")
    print("=" * 80)
    
    try:
        # Import ChunkEmbedder from the same directory
        from db_fixed_chunks import ChunkEmbedder
        embedder = ChunkEmbedder()
        
        # Load chunks to estimate cost
        json_path = "/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/all_chunks_combined.json"
        chunks = embedder.load_chunks_from_json(json_path)
        texts = [chunk['text'] for chunk in chunks]
        
        # Estimate cost
        total_tokens, estimated_cost = embedder.embedding_generator.estimate_cost(texts)
        
        print(f"\n📊 Pipeline Summary:")
        print(f"   - Total chunks to process: {len(chunks):,}")
        print(f"   - Total tokens: {total_tokens:,}")
        print(f"   - Estimated cost: ${estimated_cost:.4f}")
        print(f"   - Estimated time: ~{len(chunks) // 100 * 2} minutes (at 100 chunks/batch)")
        
        # Check existing chunks
        current_count = embedder.get_chunk_count()
        if current_count > 0:
            print(f"\n⚠️  WARNING: Database already contains {current_count:,} chunks")
            print("   The pipeline will resume from where it left off (if checkpoint exists)")
        
        print("\n" + "-" * 50)
        response = input("\nProceed with embedding generation? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("\n❌ Pipeline cancelled by user.")
            return
        
        # Run the pipeline
        print("\n" + "=" * 80)
        print("STEP 3: Running embedding pipeline...")
        print("=" * 80)
        
        embedder.process_chunks(json_path, resume=True)
        
        print("\n✅ Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user.")
        print("   You can resume from the last checkpoint by running this script again.")
    except Exception as e:
        print(f"\n❌ Error during pipeline execution: {e}")
        print("\nTroubleshooting:")
        print("1. Check your OpenAI API key is valid and has credits")
        print("2. Ensure Supabase database is accessible")
        print("3. Check network connectivity")
        print("4. Review error messages above")


if __name__ == "__main__":
    main()