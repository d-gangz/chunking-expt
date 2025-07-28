"""
Test script for hybrid search functionality.
Runs various test queries and validates search results.
"""

import time
import sys
import os
from typing import List, Dict

# Add parent directories to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from common.hybrid_search import HybridSearch

def test_search_queries():
    """Test various search queries and measure performance."""
    searcher = HybridSearch("fixed_chunks")  # Explicitly specify the table
    
    # Test queries covering different topics
    test_queries = [
        # Technical queries
        "AI prompting techniques for legal counsel",
        "how to write better prompts",
        "using Claude for coding",
        
        # General queries
        "best practices AI usage",
        "artificial intelligence safety",
        "machine learning applications",
        
        # Specific queries
        "GPT vs Claude comparison",
        "prompt engineering tips",
        "AI for content creation"
    ]
    
    print("🔍 HYBRID SEARCH TESTING")
    print("=" * 80)
    
    all_passed = True
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: '{query}'")
        print("-" * 50)
        
        try:
            # Measure search time
            start_time = time.time()
            results = searcher.search(query, match_count=5)
            search_time = time.time() - start_time
            
            # Check results
            if results:
                print(f"✅ Found {len(results)} results in {search_time:.3f}s")
                
                # Show top result
                top_result = results[0]
                print(f"\nTop result:")
                print(f"  Title: {top_result['title']}")
                print(f"  Time: {top_result['cue_start']:.1f}s - {top_result['cue_end']:.1f}s")
                print(f"  Scores: Hybrid={top_result['hybrid_score']:.4f}, "
                      f"Similarity={top_result['similarity_score']:.4f}, "
                      f"FTS={top_result['fts_score']:.4f}")
                print(f"  Text preview: {top_result['text'][:100]}...")
                
                # Performance check
                if search_time > 5:
                    print(f"⚠️  Search took longer than 5 seconds ({search_time:.3f}s)")
                    all_passed = False
                    
            else:
                print("❌ No results found")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            all_passed = False
    
    return all_passed

def test_edge_cases():
    """Test edge cases and error handling."""
    searcher = HybridSearch("fixed_chunks")  # Explicitly specify the table
    
    print("\n\n🔧 EDGE CASE TESTING")
    print("=" * 80)
    
    edge_cases = [
        ("Empty query", ""),
        ("Very long query", "a" * 1000),
        ("Special characters", "AI & ML: $100 @tech #future"),
        ("Non-English", "人工智能"),
        ("Single word", "AI"),
        ("Typos", "artificail inteligence")
    ]
    
    for case_name, query in edge_cases:
        print(f"\n{case_name}: '{query[:50]}...' if len(query) > 50 else '{query}'")
        try:
            results = searcher.search(query, match_count=3)
            print(f"✅ Handled successfully, found {len(results)} results")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_performance():
    """Test search performance under load."""
    searcher = HybridSearch("fixed_chunks")  # Explicitly specify the table
    
    print("\n\n⚡ PERFORMANCE TESTING")
    print("=" * 80)
    
    queries = ["AI safety", "machine learning", "prompt engineering"]
    
    # Sequential searches
    print("\nSequential search test (3 queries):")
    start_time = time.time()
    for query in queries:
        results = searcher.search(query, match_count=10)
    sequential_time = time.time() - start_time
    print(f"Total time: {sequential_time:.3f}s")
    print(f"Average per query: {sequential_time/len(queries):.3f}s")
    
    # Check if performance is acceptable
    avg_time = sequential_time / len(queries)
    if avg_time < 2:
        print("✅ Performance is excellent")
    elif avg_time < 5:
        print("✅ Performance is acceptable")
    else:
        print("⚠️  Performance needs optimization")

def main():
    """Run all tests."""
    print("🚀 HYBRID SEARCH TEST SUITE")
    print("=" * 80)
    
    try:
        # Check if database has data
        from db_fixed_chunks import ChunkEmbedder
        embedder = ChunkEmbedder()
        chunk_count = embedder.get_chunk_count()
        
        if chunk_count == 0:
            print("❌ No chunks found in database!")
            print("   Please run the embedding pipeline first.")
            return
        
        print(f"✅ Database contains {chunk_count:,} chunks")
        
        # Run tests
        test_results = []
        
        # Test 1: Search queries
        print("\n" + "=" * 80)
        search_passed = test_search_queries()
        test_results.append(("Search Queries", search_passed))
        
        # Test 2: Edge cases
        test_edge_cases()
        
        # Test 3: Performance
        test_performance()
        
        # Summary
        print("\n\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        if all(passed for _, passed in test_results):
            print("\n✅ ALL TESTS PASSED!")
        else:
            print("\n⚠️  Some tests failed. Review the output above.")
            
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        print("\nMake sure:")
        print("1. Database is properly set up")
        print("2. Embeddings have been generated")
        print("3. Hybrid search function is created")


if __name__ == "__main__":
    main()