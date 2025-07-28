#!/usr/bin/env python3
"""
Test script for fixed_chunks hybrid search functionality.
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
    print("Testing fixed_chunks search...")
    
    # Initialize searcher
    searcher = HybridSearch("fixed_chunks")
    
    # Test queries
    test_queries = [
        "AI safety",
        "machine learning",
        "neural networks",
        "deep learning"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        print("-" * 80)
        
        results = searcher.search(query, match_count=5)
        
        if not results:
            print("No results found")
            continue
        
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Title: {result['title']}")
            print(f"Time: {result['cue_start']:.1f}s - {result['cue_end']:.1f}s")
            print(f"Score: {result['hybrid_score']:.4f} (similarity: {result['similarity_score']:.4f}, fts: {result['fts_rank']:.4f})")
            print(f"Text: {result['text'][:200]}...")
    
    print(f"\n✅ fixed_chunks search test completed!")


def test_count():
    """Test chunk count."""
    from common.chunk_embedder import ChunkEmbedder
    
    embedder = ChunkEmbedder("fixed_chunks")
    count = embedder.get_chunk_count()
    print(f"\n📊 Total chunks in fixed_chunks: {count:,}")


if __name__ == "__main__":
    test_search()
    test_count()
