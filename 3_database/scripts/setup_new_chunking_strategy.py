#!/usr/bin/env python3
"""
Automated setup script for adding new chunking strategies to the database.
This script handles all the steps required to add a new chunking strategy:
1. Creates the database table
2. Sets up the hybrid search function
3. Processes chunks and generates embeddings
4. Creates test files
5. Validates the setup
"""

import os
import sys
import json
import argparse
import psycopg2
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the correct path
sys.path.insert(0, str(project_root / "3_database"))
from common.chunk_embedder import ChunkEmbedder
from common.embedding_utils import EmbeddingGenerator

load_dotenv()


class ChunkingStrategySetup:
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("SUPABASE_CONNECTION_STRING not found in environment variables")
        
        # Define paths
        self.chunks_dir = project_root / "2_chunks" / strategy_name / "chunks"
        self.chunks_file = self.chunks_dir / "all_chunks_combined.json"
        self.db_dir = project_root / "3_database" / strategy_name
        self.scripts_dir = self.db_dir / "scripts"
        self.setup_dir = self.db_dir / "setup"
        self.tests_dir = self.db_dir / "tests"
        
    def validate_chunks_file(self) -> bool:
        """Validate that the chunks file exists and has the correct format."""
        if not self.chunks_file.exists():
            print(f"❌ Chunks file not found: {self.chunks_file}")
            print(f"   Please ensure you've run the chunking script in 2_chunks/{self.strategy_name}/")
            return False
        
        try:
            with open(self.chunks_file, 'r') as f:
                chunks = json.load(f)
            
            if not chunks:
                print("❌ Chunks file is empty")
                return False
            
            # Check first chunk has required fields
            required_fields = ['text', 'title', 'cue_start', 'cue_end']
            first_chunk = chunks[0]
            missing_fields = [field for field in required_fields if field not in first_chunk]
            
            if missing_fields:
                print(f"❌ Missing required fields in chunks: {missing_fields}")
                return False
            
            print(f"✅ Found {len(chunks)} valid chunks in {self.chunks_file.name}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in chunks file: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading chunks file: {e}")
            return False
    
    def create_table(self) -> bool:
        """Create the database table for the chunking strategy."""
        print(f"\n📊 Creating table '{self.strategy_name}'...")
        
        create_table_sql = f"""
        -- Create table for {self.strategy_name} chunks
        CREATE TABLE IF NOT EXISTS {self.strategy_name} (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            title TEXT NOT NULL,
            cue_start FLOAT NOT NULL,
            cue_end FLOAT NOT NULL,
            embedding vector(1024) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        -- Create HNSW index for vector similarity search
        CREATE INDEX IF NOT EXISTS idx_{self.strategy_name}_embedding 
        ON {self.strategy_name} 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);

        -- Create GIN index for full-text search
        CREATE INDEX IF NOT EXISTS idx_{self.strategy_name}_text_fts
        ON {self.strategy_name}
        USING gin(to_tsvector('english', text));

        -- Create index on title for title-based queries
        CREATE INDEX IF NOT EXISTS idx_{self.strategy_name}_title
        ON {self.strategy_name}(title);
        """
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            cur.execute(create_table_sql)
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ Table '{self.strategy_name}' created successfully")
            
            # Save SQL for reference
            self.setup_dir.mkdir(parents=True, exist_ok=True)
            sql_file = self.setup_dir / f"create_table_{self.strategy_name}.sql"
            with open(sql_file, 'w') as f:
                f.write(create_table_sql)
            print(f"📄 Table creation SQL saved to: {sql_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            return False
    
    def create_hybrid_search_function(self) -> bool:
        """Create the hybrid search function for the chunking strategy."""
        print(f"\n🔍 Creating hybrid search function...")
        
        # First drop the function if it exists (to handle return type changes)
        drop_sql = f"DROP FUNCTION IF EXISTS hybrid_search_{self.strategy_name}(TEXT, vector(1024), INT, INT);"
        
        hybrid_search_sql = f"""
        CREATE OR REPLACE FUNCTION hybrid_search_{self.strategy_name}(
            query_text TEXT,
            query_embedding vector(1024),
            match_count INT DEFAULT 20,
            rrf_k INT DEFAULT 60
        )
        RETURNS TABLE (
            id INT,
            text TEXT,
            title TEXT,
            cue_start FLOAT,
            cue_end FLOAT,
            similarity_score FLOAT,
            fts_rank FLOAT,
            hybrid_score FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            WITH vector_search AS (
                SELECT 
                    c.id,
                    c.text,
                    c.title,
                    c.cue_start,
                    c.cue_end,
                    1 - (c.embedding <=> query_embedding) AS similarity_score,
                    NULL::FLOAT AS fts_rank
                FROM {self.strategy_name} c
                ORDER BY c.embedding <=> query_embedding
                LIMIT match_count * 2
            ),
            fts_search AS (
                SELECT 
                    c.id,
                    c.text,
                    c.title,
                    c.cue_start,
                    c.cue_end,
                    NULL::FLOAT AS similarity_score,
                    ts_rank_cd(to_tsvector('english', c.text), plainto_tsquery('english', query_text)) AS fts_rank
                FROM {self.strategy_name} c
                WHERE to_tsvector('english', c.text) @@ plainto_tsquery('english', query_text)
                ORDER BY fts_rank DESC
                LIMIT match_count * 2
            ),
            all_results AS (
                SELECT * FROM vector_search
                UNION ALL
                SELECT * FROM fts_search
            ),
            grouped_results AS (
                SELECT 
                    all_results.id,
                    MAX(all_results.text) AS text,
                    MAX(all_results.title) AS title,
                    MAX(all_results.cue_start) AS cue_start,
                    MAX(all_results.cue_end) AS cue_end,
                    MAX(COALESCE(all_results.similarity_score, 0)) AS max_similarity,
                    MAX(COALESCE(all_results.fts_rank, 0)) AS max_fts_rank
                FROM all_results
                GROUP BY all_results.id
            ),
            scored_results AS (
                SELECT 
                    *,
                    (
                        1.0 / (rrf_k + (CASE WHEN max_similarity > 0 THEN 
                            1 + (1 - max_similarity) * (match_count * 2 - 1)
                        ELSE match_count * 2 END))
                        +
                        1.0 / (rrf_k + (CASE WHEN max_fts_rank > 0 THEN 
                            1 + (SELECT COUNT(*) FROM fts_search f2 WHERE f2.fts_rank > max_fts_rank)
                        ELSE match_count * 2 END))
                    ) AS hybrid_score
                FROM grouped_results
            )
            SELECT 
                scored_results.id::INT,
                scored_results.text::TEXT,
                scored_results.title::TEXT,
                scored_results.cue_start::FLOAT,
                scored_results.cue_end::FLOAT,
                scored_results.max_similarity::FLOAT AS similarity_score,
                scored_results.max_fts_rank::FLOAT AS fts_rank,
                scored_results.hybrid_score::FLOAT
            FROM scored_results
            ORDER BY scored_results.hybrid_score DESC
            LIMIT match_count;
        END;
        $$;
        """
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor()
            
            # Drop existing function first
            cur.execute(drop_sql)
            
            # Create the new function
            cur.execute(hybrid_search_sql)
            conn.commit()
            cur.close()
            conn.close()
            print(f"✅ Hybrid search function created successfully")
            
            # Save SQL for reference
            sql_file = self.setup_dir / f"hybrid_search_{self.strategy_name}.sql"
            with open(sql_file, 'w') as f:
                f.write(hybrid_search_sql)
            print(f"📄 Function SQL saved to: {sql_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating hybrid search function: {e}")
            return False
    
    def generate_embeddings(self) -> bool:
        """Generate embeddings for all chunks."""
        print(f"\n🤖 Generating embeddings for {self.strategy_name}...")
        
        try:
            # Add the strategy to allowed tables in chunk_embedder
            # This is a temporary workaround until we implement proper validation
            embedder = ChunkEmbedder(self.strategy_name)
            
            # Load chunks
            chunks = embedder.load_chunks_from_json(str(self.chunks_file))
            
            # Check for existing data
            existing_count = embedder.get_chunk_count()
            if existing_count > 0:
                print(f"⚠️  Table already contains {existing_count} chunks")
                response = input("Do you want to continue and add more chunks? (yes/no): ")
                if response.lower() != 'yes':
                    print("Skipping embedding generation")
                    return True
            
            # Process chunks
            embedder.process_chunks(chunks)
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating embeddings: {e}")
            return False
    
    def create_test_file(self):
        """Create a test file for the new chunking strategy."""
        print(f"\n🧪 Creating test file...")
        
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = self.tests_dir / f"test_{self.strategy_name}_search.py"
        
        test_content = f'''#!/usr/bin/env python3
"""
Test script for {self.strategy_name} hybrid search functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the correct path
sys.path.insert(0, str(project_root / "3_database"))
from common.hybrid_search import HybridSearch


def test_search():
    """Test basic search functionality."""
    print("Testing {self.strategy_name} search...")
    
    # Initialize searcher
    searcher = HybridSearch("{self.strategy_name}")
    
    # Test queries
    test_queries = [
        "AI safety",
        "machine learning",
        "neural networks",
        "deep learning"
    ]
    
    for query in test_queries:
        print(f"\\n🔍 Searching for: '{{query}}'")
        print("-" * 80)
        
        results = searcher.search(query, match_count=5)
        
        if not results:
            print("No results found")
            continue
        
        for i, result in enumerate(results, 1):
            print(f"\\nResult {{i}}:")
            print(f"Title: {{result['title']}}")
            print(f"Time: {{result['cue_start']:.1f}}s - {{result['cue_end']:.1f}}s")
            print(f"Score: {{result['hybrid_score']:.4f}} (similarity: {{result['similarity_score']:.4f}}, fts: {{result['fts_rank']:.4f}})")
            print(f"Text: {{result['text'][:200]}}...")
    
    print(f"\\n✅ {self.strategy_name} search test completed!")


def test_count():
    """Test chunk count."""
    from common.chunk_embedder import ChunkEmbedder
    
    embedder = ChunkEmbedder("{self.strategy_name}")
    count = embedder.get_chunk_count()
    print(f"\\n📊 Total chunks in {self.strategy_name}: {{count:,}}")


if __name__ == "__main__":
    test_search()
    test_count()
'''
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Make executable
        os.chmod(test_file, 0o755)
        
        print(f"✅ Test file created: {test_file}")
    
    def create_readme(self):
        """Create a README for the new strategy directory."""
        readme_file = self.db_dir / "README.md"
        
        readme_content = f"""# {self.strategy_name.replace('_', ' ').title()} Database Setup

This directory contains the database setup and scripts for the {self.strategy_name} chunking strategy.

## Structure

```
{self.strategy_name}/
├── scripts/      # Processing scripts
├── setup/        # SQL setup files
├── tests/        # Test scripts
└── README.md     # This file
```

## Usage

### Search for chunks

```python
from common.hybrid_search import HybridSearch

searcher = HybridSearch("{self.strategy_name}")
results = searcher.search("your query here", match_count=10)
```

### Run tests

```bash
uv run python 3_database/{self.strategy_name}/tests/test_{self.strategy_name}_search.py
```

### Regenerate embeddings

```bash
uv run python 3_database/common/chunk_embedder.py {self.strategy_name} 2_chunks/{self.strategy_name}/chunks/all_chunks_combined.json
```

## Table Details

- **Table name**: `{self.strategy_name}`
- **Embedding model**: text-embedding-3-large (1024 dimensions)
- **Indexes**: HNSW (vector), GIN (full-text), B-tree (title)
- **Search function**: `hybrid_search_{self.strategy_name}`
"""
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"📄 README created: {readme_file}")
    
    def run_setup(self, skip_embeddings: bool = False):
        """Run the complete setup process."""
        print(f"\n🚀 Setting up new chunking strategy: {self.strategy_name}")
        print("=" * 80)
        
        # Step 1: Validate chunks file
        if not self.validate_chunks_file():
            return False
        
        # Step 2: Create database table
        if not self.create_table():
            return False
        
        # Step 3: Create hybrid search function
        if not self.create_hybrid_search_function():
            return False
        
        # Step 4: Generate embeddings (unless skipped)
        if not skip_embeddings:
            if not self.generate_embeddings():
                return False
        else:
            print("\n⏭️  Skipping embedding generation (--skip-embeddings flag)")
        
        # Step 5: Create test file
        self.create_test_file()
        
        # Step 6: Create README
        self.create_readme()
        
        print("\n" + "=" * 80)
        print(f"✅ Setup complete for '{self.strategy_name}'!")
        print("\nNext steps:")
        print(f"1. Test your setup: uv run python 3_database/{self.strategy_name}/tests/test_{self.strategy_name}_search.py")
        print(f"2. Use in your code: HybridSearch('{self.strategy_name}')")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Automated setup for new chunking strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s semantic_chunks          # Full setup including embeddings
  %(prog)s tool_chunks --skip-embeddings  # Setup without generating embeddings
        """
    )
    
    parser.add_argument(
        "strategy_name",
        help="Name of the chunking strategy (e.g., 'semantic_chunks', 'tool_chunks')"
    )
    
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip embedding generation (useful for testing or if you'll generate them later)"
    )
    
    args = parser.parse_args()
    
    # Validate strategy name
    if not args.strategy_name.replace('_', '').isalnum():
        print(f"❌ Invalid strategy name: {args.strategy_name}")
        print("   Strategy name should only contain letters, numbers, and underscores")
        sys.exit(1)
    
    # Run setup
    setup = ChunkingStrategySetup(args.strategy_name)
    success = setup.run_setup(skip_embeddings=args.skip_embeddings)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()