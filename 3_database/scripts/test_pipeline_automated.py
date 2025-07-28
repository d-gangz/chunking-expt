#!/usr/bin/env python3
"""
Automated end-to-end pipeline test for local Supabase setup.
Tests the complete flow: chunks → embeddings → database → search
"""

import os
import sys
import json
import time
import psycopg2
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "3_database"))

from common.chunk_embedder import ChunkEmbedder
from common.hybrid_search import HybridSearch
from common.embedding_utils import EmbeddingGenerator

# Test configuration
TEST_CHUNK_COUNT = 5  # Number of chunks to test with
TEST_TABLE_NAME = "test_pipeline_chunks"  # Temporary table for testing


class PipelineTest:
    def __init__(self):
        self.conn_string = os.getenv("SUPABASE_CONNECTION_STRING")
        self.test_passed = True
        self.start_time = time.time()
        
    def log(self, message: str, is_error: bool = False):
        """Log a message with timestamp."""
        timestamp = time.time() - self.start_time
        prefix = "❌" if is_error else "✅"
        print(f"[{timestamp:6.2f}s] {prefix} {message}")
        if is_error:
            self.test_passed = False
    
    def setup_test_table(self) -> bool:
        """Create a temporary test table."""
        print("\n📋 Setting up test table...")
        try:
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            
            # Drop table if exists
            cur.execute(f"DROP TABLE IF EXISTS {TEST_TABLE_NAME} CASCADE")
            
            # Create test table with same schema as fixed_chunks
            cur.execute(f"""
                CREATE TABLE {TEST_TABLE_NAME} (
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
                
                -- Create indexes
                CREATE INDEX ON {TEST_TABLE_NAME} USING hnsw (embedding vector_cosine_ops);
                CREATE INDEX ON {TEST_TABLE_NAME} USING gin (to_tsvector('english', text));
                CREATE INDEX ON {TEST_TABLE_NAME} (title);
            """)
            
            # Create hybrid search function for test table
            cur.execute(f"""
                CREATE OR REPLACE FUNCTION hybrid_search_{TEST_TABLE_NAME}(
                    query_text text,
                    query_embedding vector(1024),
                    match_count int DEFAULT 20,
                    rrf_k int DEFAULT 60
                )
                RETURNS TABLE(
                    id integer,
                    text text,
                    title text,
                    cue_start float,
                    cue_end float,
                    similarity_score float,
                    fts_score float,
                    hybrid_score float
                )
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    RETURN QUERY
                    WITH semantic_search AS (
                        SELECT
                            fc.id,
                            fc.text,
                            fc.title,
                            fc.cue_start,
                            fc.cue_end,
                            1 - (fc.embedding <=> query_embedding) AS similarity,
                            ROW_NUMBER() OVER (ORDER BY fc.embedding <=> query_embedding) AS rank
                        FROM {TEST_TABLE_NAME} fc
                        ORDER BY fc.embedding <=> query_embedding
                        LIMIT match_count * 2
                    ),
                    fts_search AS (
                        SELECT
                            fc.id,
                            fc.text,
                            fc.title,
                            fc.cue_start,
                            fc.cue_end,
                            ts_rank_cd(to_tsvector('english', fc.text), websearch_to_tsquery('english', query_text)) AS rank_score,
                            ROW_NUMBER() OVER (
                                ORDER BY ts_rank_cd(to_tsvector('english', fc.text), websearch_to_tsquery('english', query_text)) DESC
                            ) AS rank
                        FROM {TEST_TABLE_NAME} fc
                        WHERE to_tsvector('english', fc.text) @@ websearch_to_tsquery('english', query_text)
                        ORDER BY rank_score DESC
                        LIMIT match_count * 2
                    )
                    SELECT
                        COALESCE(s.id, f.id) AS id,
                        COALESCE(s.text, f.text) AS text,
                        COALESCE(s.title, f.title) AS title,
                        COALESCE(s.cue_start, f.cue_start) AS cue_start,
                        COALESCE(s.cue_end, f.cue_end) AS cue_end,
                        COALESCE(s.similarity, 0)::float AS similarity_score,
                        COALESCE(f.rank_score, 0)::float AS fts_score,
                        (COALESCE(1.0 / (rrf_k + s.rank), 0) +
                        COALESCE(1.0 / (rrf_k + f.rank), 0))::float AS hybrid_score
                    FROM semantic_search s
                    FULL OUTER JOIN fts_search f ON s.id = f.id
                    ORDER BY hybrid_score DESC
                    LIMIT match_count;
                END;
                $$;
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.log(f"Created test table '{TEST_TABLE_NAME}' with indexes and function")
            return True
            
        except Exception as e:
            self.log(f"Failed to create test table: {e}", is_error=True)
            return False
    
    def load_sample_chunks(self) -> List[Dict]:
        """Load a sample of chunks from the JSON file."""
        print("\n📦 Loading sample chunks...")
        try:
            json_path = project_root / "2_chunks/fixed_chunks/chunks/all_chunks_combined.json"
            
            with open(json_path, 'r', encoding='utf-8') as f:
                all_chunks = json.load(f)
            
            # Take first N chunks for testing
            sample_chunks = all_chunks[:TEST_CHUNK_COUNT]
            
            # Add required fields if missing
            for i, chunk in enumerate(sample_chunks):
                if 'chunk_index' not in chunk:
                    chunk['chunk_index'] = i
                if 'total_chunks' not in chunk:
                    chunk['total_chunks'] = len(sample_chunks)
            
            self.log(f"Loaded {len(sample_chunks)} sample chunks from {len(all_chunks)} total")
            return sample_chunks
            
        except Exception as e:
            self.log(f"Failed to load chunks: {e}", is_error=True)
            return []
    
    def test_embedding_generation(self, chunks: List[Dict]) -> List[Dict]:
        """Test embedding generation for sample chunks."""
        print("\n🧮 Testing embedding generation...")
        try:
            embedder = EmbeddingGenerator(
                model="text-embedding-3-large",
                dimensions=1024
            )
            
            texts = [chunk['text'] for chunk in chunks]
            
            # Test cost estimation
            total_tokens, estimated_cost = embedder.estimate_cost(texts)
            self.log(f"Estimated tokens: {total_tokens:,}, cost: ${estimated_cost:.4f}")
            
            # Generate embeddings
            start = time.time()
            embeddings = embedder.create_embeddings_with_retry(texts)
            duration = time.time() - start
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk['embedding'] = embedding
            
            self.log(f"Generated {len(embeddings)} embeddings in {duration:.2f}s")
            self.log(f"Average time per embedding: {duration/len(embeddings):.3f}s")
            
            # Verify embedding dimensions
            if len(embeddings[0]) == 1024:
                self.log("Embedding dimensions correct (1024)")
            else:
                self.log(f"Wrong embedding dimensions: {len(embeddings[0])}", is_error=True)
            
            return chunks
            
        except Exception as e:
            self.log(f"Embedding generation failed: {e}", is_error=True)
            return []
    
    def test_database_insertion(self, chunks_with_embeddings: List[Dict]) -> bool:
        """Test inserting chunks into database."""
        print("\n💾 Testing database insertion...")
        try:
            # Custom insertion for test table with all required fields
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            
            start = time.time()
            
            # Insert each chunk
            for chunk in chunks_with_embeddings:
                cur.execute(f"""
                    INSERT INTO {TEST_TABLE_NAME} 
                    (text, title, cue_start, cue_end, chunk_index, total_chunks, embedding) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    chunk['text'],
                    chunk.get('title', ''),
                    chunk.get('cue_start', 0),
                    chunk.get('cue_end', 0),
                    chunk.get('chunk_index', 0),
                    chunk.get('total_chunks', len(chunks_with_embeddings)),
                    chunk['embedding']
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            duration = time.time() - start
            
            # Verify insertion
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {TEST_TABLE_NAME}")
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            if count == len(chunks_with_embeddings):
                self.log(f"Inserted {count} chunks in {duration:.2f}s")
                self.log(f"Average insertion time: {duration/count:.3f}s per chunk")
                return True
            else:
                self.log(f"Count mismatch: expected {len(chunks_with_embeddings)}, got {count}", is_error=True)
                return False
                
        except Exception as e:
            self.log(f"Database insertion failed: {e}", is_error=True)
            return False
    
    def test_hybrid_search(self) -> bool:
        """Test hybrid search functionality."""
        print("\n🔍 Testing hybrid search...")
        try:
            searcher = HybridSearch(TEST_TABLE_NAME)
            
            # Test queries
            test_queries = [
                "AI prompting techniques",
                "legal counsel",
                "best practices"
            ]
            
            all_searches_passed = True
            
            for query in test_queries:
                start = time.time()
                results = searcher.search(query, match_count=3)
                duration = time.time() - start
                
                if results:
                    self.log(f"Query '{query}': {len(results)} results in {duration:.3f}s")
                    
                    # Verify result structure
                    required_fields = ['id', 'text', 'title', 'hybrid_score', 'similarity_score', 'fts_score']
                    for field in required_fields:
                        if field not in results[0]:
                            self.log(f"Missing field '{field}' in results", is_error=True)
                            all_searches_passed = False
                    
                    # Check score ranges
                    top_result = results[0]
                    if 0 <= top_result['similarity_score'] <= 1:
                        self.log(f"  Top similarity score: {top_result['similarity_score']:.4f}")
                    else:
                        self.log(f"  Invalid similarity score: {top_result['similarity_score']}", is_error=True)
                        all_searches_passed = False
                else:
                    self.log(f"No results for query '{query}'", is_error=True)
                    all_searches_passed = False
            
            return all_searches_passed
            
        except Exception as e:
            self.log(f"Hybrid search test failed: {e}", is_error=True)
            return False
    
    def test_performance_metrics(self) -> Dict:
        """Collect and display performance metrics."""
        print("\n📊 Performance Metrics...")
        try:
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            
            # Get table size
            cur.execute(f"""
                SELECT 
                    pg_size_pretty(pg_total_relation_size('{TEST_TABLE_NAME}')) as total_size,
                    pg_size_pretty(pg_relation_size('{TEST_TABLE_NAME}')) as table_size,
                    pg_size_pretty(pg_indexes_size('{TEST_TABLE_NAME}')) as indexes_size
            """)
            sizes = cur.fetchone()
            
            self.log(f"Table size: {sizes[1]}, Indexes: {sizes[2]}, Total: {sizes[0]}")
            
            cur.close()
            conn.close()
            
            return {
                'total_size': sizes[0],
                'table_size': sizes[1],
                'indexes_size': sizes[2]
            }
            
        except Exception as e:
            self.log(f"Failed to get metrics: {e}", is_error=True)
            return {}
    
    def cleanup(self):
        """Clean up test table and function."""
        print("\n🧹 Cleaning up...")
        try:
            conn = psycopg2.connect(self.conn_string)
            cur = conn.cursor()
            
            # Drop function and table
            cur.execute(f"DROP FUNCTION IF EXISTS hybrid_search_{TEST_TABLE_NAME}(text, vector, int, int)")
            cur.execute(f"DROP TABLE IF EXISTS {TEST_TABLE_NAME}")
            
            conn.commit()
            cur.close()
            conn.close()
            
            self.log("Cleaned up test table and function")
            
        except Exception as e:
            self.log(f"Cleanup failed: {e}", is_error=True)
    
    def run(self) -> bool:
        """Run the complete pipeline test."""
        print("🚀 AUTOMATED PIPELINE TEST")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Pre-flight checks
        print("\n✈️  Pre-flight checks...")
        try:
            conn = psycopg2.connect(self.conn_string)
            conn.close()
            self.log("Database connection OK")
        except Exception as e:
            self.log(f"Database connection failed: {e}", is_error=True)
            return False
        
        # Run pipeline steps
        steps = [
            ("Setup test table", self.setup_test_table),
            ("Load sample chunks", self.load_sample_chunks),
            ("Generate embeddings", lambda: self.test_embedding_generation(self.sample_chunks)),
            ("Insert into database", lambda: self.test_database_insertion(self.chunks_with_embeddings)),
            ("Test hybrid search", self.test_hybrid_search),
            ("Collect metrics", self.test_performance_metrics)
        ]
        
        # Execute steps
        for step_name, step_func in steps:
            result = step_func()
            
            # Store results for next steps
            if step_name == "Load sample chunks":
                self.sample_chunks = result
                if not result:
                    break
            elif step_name == "Generate embeddings":
                self.chunks_with_embeddings = result
                if not result:
                    break
        
        # Cleanup
        self.cleanup()
        
        # Summary
        total_time = time.time() - self.start_time
        print("\n" + "=" * 60)
        print("PIPELINE TEST SUMMARY")
        print("=" * 60)
        print(f"Total execution time: {total_time:.2f}s")
        print(f"Result: {'✅ ALL TESTS PASSED' if self.test_passed else '❌ SOME TESTS FAILED'}")
        
        if self.test_passed:
            print("\n✅ The complete pipeline is working correctly!")
            print("   - Chunks can be loaded")
            print("   - Embeddings can be generated") 
            print("   - Data can be inserted into database")
            print("   - Hybrid search is functional")
        else:
            print("\n❌ Pipeline test failed. Check the errors above.")
        
        return self.test_passed


def main():
    """Run the automated pipeline test."""
    tester = PipelineTest()
    success = tester.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())