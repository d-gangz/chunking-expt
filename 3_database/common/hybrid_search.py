"""
Hybrid search implementation combining vector and keyword search using Reciprocal Rank Fusion.
Uses OpenAI embeddings and Supabase's pgvector for efficient retrieval.

How hybrid search works:
- Combines vector similarity search (semantic) and full-text search (keyword) results
- Uses Reciprocal Rank Fusion (RRF) to merge rankings from both search methods
- Formula: hybrid_score = 1/(k + semantic_rank) + 1/(k + fts_rank)
- Default k=60 (smoothing constant to prevent top results from dominating)
- Score range: ~0 to 0.033 (higher is better)
- Scores around 0.0328 indicate high ranking in both searches
- Scores around 0.0164 indicate high ranking in only one search

Implementation follows Supabase's recommended approach:
https://supabase.com/docs/guides/ai/hybrid-search
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class HybridSearch:
    def __init__(self, table_name: str = "fixed_chunks"):
        """
        Initialize the hybrid search with OpenAI and Supabase connections.
        
        Args:
            table_name: Name of the table to search (default: "fixed_chunks")
                       Examples: "fixed_chunks", "tool_chunks", "nugget_chunks"
        """
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.connection_string = os.getenv("SUPABASE_CONNECTION_STRING")
        self.embedding_model = "text-embedding-3-large"
        self.embedding_dimensions = 1024
        self.table_name = table_name
        self.search_function_name = f"hybrid_search_{table_name}"
        
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query using OpenAI.
        
        Args:
            query: The search query text
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query,
                dimensions=self.embedding_dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            raise
    
    def search(self, query: str, match_count: int = 20, rrf_k: int = 60) -> List[Dict]:
        """
        Perform hybrid search combining vector similarity and full-text search.
        
        Args:
            query: The search query
            match_count: Number of results to return (default: 20)
            rrf_k: RRF constant for score fusion (default: 60)
            
        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)
        
        # Connect to database
        conn = None
        cur = None
        
        try:
            conn = psycopg2.connect(self.connection_string)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Call the hybrid search function for the specified table
            cur.execute(
                f"SELECT * FROM {self.search_function_name}(%s, %s::vector, %s, %s)",
                (query, query_embedding, match_count, rrf_k)
            )
            
            results = cur.fetchall()
            
            # Convert results to list of dicts
            return [dict(row) for row in results]
            
        except Exception as e:
            print(f"Error during hybrid search: {e}")
            raise
            
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    def format_results(self, results: List[Dict], max_text_length: int = 200) -> str:
        """
        Format search results for display.
        
        Args:
            results: List of search results
            max_text_length: Maximum characters to show from text (default: 200)
            
        Returns:
            Formatted string of results
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            text_preview = result['text'][:max_text_length]
            if len(result['text']) > max_text_length:
                text_preview += "..."
                
            formatted.append(f"""
{i}. [{result['title']}] ({result['cue_start']:.1f}s - {result['cue_end']:.1f}s)
   Hybrid Score: {result['hybrid_score']:.4f}
   Similarity: {result['similarity_score']:.4f} | FTS: {result['fts_score']:.4f}
   Text: {text_preview}
""")
        
        return "\n".join(formatted)


def main():
    """Example usage of hybrid search with different tables."""
    # Example 1: Search fixed_chunks table (default)
    searcher_fixed = HybridSearch()  # or HybridSearch("fixed_chunks")
    
    # Example 2: Search tool_chunks table
    # searcher_tool = HybridSearch("tool_chunks")
    
    # Example 3: Search nugget_chunks table  
    # searcher_nugget = HybridSearch("nugget_chunks")
    
    # Example queries
    example_queries = [
        "AI prompting techniques for legal counsel",
        "how to use AI for writing",
        "best practices for using Claude",
        "AI safety and ethics"
    ]
    
    print("Hybrid Search Examples")
    print("=" * 80)
    
    for query in example_queries[:1]:  # Run just the first query as example
        print(f"\nQuery: '{query}'")
        print(f"Table: {searcher_fixed.table_name}")
        print("-" * 80)
        
        try:
            # Perform search
            results = searcher_fixed.search(query, match_count=10)
            
            # Display results
            if results:
                print(f"Found {len(results)} results:")
                print(searcher_fixed.format_results(results[:5]))  # Show top 5
            else:
                print("No results found.")
                
        except Exception as e:
            print(f"Search failed: {e}")
    
    print("\n" + "=" * 80)
    print("\nTo use in your code:")
    print("```python")
    print("# For fixed chunks (default)")
    print("searcher = HybridSearch()")
    print("# or explicitly: searcher = HybridSearch('fixed_chunks')")
    print("")
    print("# For other chunk strategies")
    print("searcher_tool = HybridSearch('tool_chunks')")
    print("searcher_nugget = HybridSearch('nugget_chunks')")
    print("")
    print("results = searcher.search('your query here', match_count=20)")
    print("```")


if __name__ == "__main__":
    main()