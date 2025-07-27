#!/usr/bin/env python3
"""
Generate hybrid search SQL function for a specific table.
This script creates the SQL needed to set up hybrid search for any chunk table.
"""

import sys
import os


def generate_hybrid_search_sql(table_name: str) -> str:
    """
    Generate the SQL for creating a hybrid search function for a specific table.
    
    Args:
        table_name: Name of the table (e.g., "tool_chunks", "nugget_chunks")
    
    Returns:
        SQL string for creating the function
    """
    sql_template = """-- Hybrid search function for {table_name} using Reciprocal Rank Fusion (RRF)
-- This function combines vector similarity search and full-text search
-- 
-- Generated from template for table: {table_name}

CREATE OR REPLACE FUNCTION hybrid_search_{table_name}(
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
            t.id,
            t.text,
            t.title,
            t.cue_start,
            t.cue_end,
            1 - (t.embedding <=> query_embedding) AS similarity,
            ROW_NUMBER() OVER (ORDER BY t.embedding <=> query_embedding) AS rank
        FROM {table_name} t
        ORDER BY t.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    fts_search AS (
        SELECT
            t.id,
            t.text,
            t.title,
            t.cue_start,
            t.cue_end,
            ts_rank_cd(to_tsvector('english', t.text), websearch_to_tsquery('english', query_text)) AS rank_score,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(to_tsvector('english', t.text), websearch_to_tsquery('english', query_text)) DESC
            ) AS rank
        FROM {table_name} t
        WHERE to_tsvector('english', t.text) @@ websearch_to_tsquery('english', query_text)
        ORDER BY rank_score DESC
        LIMIT match_count * 2
    )
    SELECT
        COALESCE(s.id, f.id) AS id,
        COALESCE(s.text, f.text) AS text,
        COALESCE(s.title, f.title) AS title,
        COALESCE(s.cue_start, f.cue_start) AS cue_start,
        COALESCE(s.cue_end, f.cue_end) AS cue_end,
        COALESCE(s.similarity, 0) AS similarity_score,
        COALESCE(f.rank_score, 0) AS fts_score,
        COALESCE(1.0 / (rrf_k + s.rank), 0) +
        COALESCE(1.0 / (rrf_k + f.rank), 0) AS hybrid_score
    FROM semantic_search s
    FULL OUTER JOIN fts_search f ON s.id = f.id
    ORDER BY hybrid_score DESC
    LIMIT match_count;
END;
$$;"""
    
    return sql_template.format(table_name=table_name)


def main():
    """Main function to generate SQL for a specific table."""
    if len(sys.argv) != 2:
        print("Usage: python create_hybrid_search_function.py <table_name>")
        print("Example: python create_hybrid_search_function.py tool_chunks")
        sys.exit(1)
    
    table_name = sys.argv[1]
    
    # Generate SQL
    sql = generate_hybrid_search_sql(table_name)
    
    # Save to file
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, f"hybrid_search_{table_name}.sql")
    
    with open(output_file, 'w') as f:
        f.write(sql)
    
    print(f"✅ Generated SQL function for table: {table_name}")
    print(f"📄 Saved to: {output_file}")
    print("\nNext steps:")
    print(f"1. Copy the contents of {output_file}")
    print("2. Run it in your Supabase Dashboard SQL Editor")
    print(f"3. Use it in Python: searcher = HybridSearch('{table_name}')")


if __name__ == "__main__":
    main()