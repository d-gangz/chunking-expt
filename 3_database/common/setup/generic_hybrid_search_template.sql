-- Generic Hybrid Search Function Template
-- Replace {TABLE_NAME} with your actual table name (e.g., tool_chunks, nugget_chunks)
-- 
-- This template creates a hybrid search function for any chunk table
-- Prerequisites: 
-- 1. Your table must have columns: id, text, title, cue_start, cue_end, embedding
-- 2. The embedding column must be of type vector(1024)
-- 3. pgvector extension must be enabled
--
-- To use this template:
-- 1. Replace all occurrences of {TABLE_NAME} with your table name
-- 2. Run this SQL in your Supabase Dashboard SQL Editor

CREATE OR REPLACE FUNCTION hybrid_search_{TABLE_NAME}(
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
        FROM {TABLE_NAME} t
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
        FROM {TABLE_NAME} t
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
$$;

-- Example usage for different tables:
-- 
-- For tool_chunks table:
-- Replace {TABLE_NAME} with tool_chunks to create hybrid_search_tool_chunks function
--
-- For nugget_chunks table:
-- Replace {TABLE_NAME} with nugget_chunks to create hybrid_search_nugget_chunks function