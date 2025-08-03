# What This Does

Creates evaluation datasets with ground truth labels mapping questions to relevant transcript chunks, enabling systematic evaluation of retrieval quality across different chunking strategies.

# File Structure

```
├── baseline-questions/              # Core question-answer pairs
│   ├── base_ground_truth.json     # Master set of Q&A with quotes
│   ├── insights.json               # Practical insights extracted
│   ├── generate_ground_truth.py   # Ground truth generation script
│   └── plan-base-questions.md     # Strategy documentation
├── fixed_chunks/                   # Fixed-chunk specific datasets
│   ├── generate-dataset/          # Phoenix-compatible datasets
│   │   ├── generate_phoenix_dataset_v2.py # Dataset generator
│   │   ├── phoenix_dataset_fixed_chunks_v2.json # Full dataset
│   │   └── phoenix_dataset_simplified_v2.json # Final dataset
│   └── retrieve-chunks/           # Database chunk retrieval
│       ├── retrieve_raw_chunks.py # Fetch chunks from DB
│       └── raw_chunks_from_db.json # Retrieved chunk data
└── brainstorm.md                  # Query type framework docs
```

# Quick Start

- Entry point: Strategy-specific dataset generators
- Retrieve chunks: `uv run python fixed_chunks/retrieve-chunks/retrieve_raw_chunks.py`
- Generate dataset: `uv run python fixed_chunks/generate-dataset/generate_phoenix_dataset_v2.py`

# How It Works

The system generates evaluation datasets by matching ground truth quotes from transcripts to actual chunks in the database. It identifies which chunks contain the beginning of relevant quotes, creating question-chunk mappings for retrieval evaluation.

# Interfaces

```python
# Phoenix dataset format (simplified v2)
{
    "query": "What is the question?",
    "expected": ["chunk_id_1", "chunk_id_2"],  # Relevant chunk IDs
    "metadata": {
        "query_type": "factual|conceptual|practical",
        "transcript": "source_transcript_name"
    }
}

# Base ground truth format
{
    "question": "The question text",
    "quoted_text": "Exact quote from transcript",
    "insights": ["Key insight 1", "Key insight 2"],
    "transcript": "transcript_title"
}
```

# Dependencies

**Code Dependencies:**
- Uses standard Python JSON processing
- Text normalization utilities for matching
- psycopg2 for database connectivity

**Data Dependencies:**
- Reads from: `/baseline-questions/base_ground_truth.json` - Q&A pairs
- Reads from: `/3_database/` via retrieve_raw_chunks.py - chunk data
- Writes to: Strategy-specific dataset files

**Cross-Directory Usage:**
- Output used by: `/5_evaluation/` - for running evaluations
- Provides: Ground truth datasets for retrieval testing

# Key Patterns

- Quote-based chunk matching (finds where quotes begin)
- Three query types: factual, conceptual, practical
- Phoenix-compatible output format
- Version 2: Only marks chunks where quotes start

# Common Tasks

- Add new questions: Edit base_ground_truth.json
- Retrieve latest chunks: Run retrieve_raw_chunks.py
- Regenerate dataset: Run generate_phoenix_dataset_v2.py
- Add new strategy: Create new subdirectory with scripts

# Recent Updates

- Implemented v2 dataset with quote-start matching (5956aeb)
- Added query type framework for varied evaluation (435a3ee)
- Simplified Phoenix dataset format (f99ba59)
- Created chunk retrieval infrastructure (89efc7f)

# Watch Out For

- Quote matching is case-insensitive but position-sensitive
- Only chunks where quotes BEGIN are marked as relevant
- Chunk IDs must match database exactly
- Title normalization needed for accurate matching
- Database must be running for chunk retrieval