-- Instructions to enable pgvector extension in Supabase
-- 
-- MANUAL STEP REQUIRED:
-- 1. Go to your Supabase Dashboard
-- 2. Navigate to SQL Editor
-- 3. Run the following command:

CREATE EXTENSION IF NOT EXISTS vector;

-- To verify the extension is enabled, run:
-- SELECT * FROM pg_extension WHERE extname = 'vector';