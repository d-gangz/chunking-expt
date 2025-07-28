-- Hybrid search function for fixed_chunks using Reciprocal Rank Fusion (RRF)
-- This function combines vector similarity search and full-text search
-- 
-- Note: For other chunking strategies, use the generic template and replace table name

CREATE OR REPLACE FUNCTION hybrid_search_fixed_chunks(
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
        FROM fixed_chunks fc
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
        FROM fixed_chunks fc
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