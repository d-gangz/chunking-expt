
        CREATE OR REPLACE FUNCTION hybrid_search_fixed_chunks(
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
                FROM fixed_chunks c
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
                FROM fixed_chunks c
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
        