# Transcript Chunking Experiment

## Overview

This project explores different methods for chunking video transcripts to optimize retrieval accuracy for Q&A systems. The goal is to enable effective retrieval of relevant information when members ask questions, ensuring they receive the right insights from video content.

## Objective

Develop and evaluate transcript chunking techniques that:

- Maintain semantic coherence within chunks
- Preserve context for accurate information retrieval
- Enable effective RAG (Retrieval-Augmented Generation) for Q&A systems
- Handle speaker identification and multi-speaker conversations

## Experiment Methodology

### 1. Baseline Establishment

- Collect ~5 video transcripts (including Gang's planning video)
- Identify current transcript generation process
- Document speaker identification methods

### 2. Quality Assessment Framework

#### Synthetic Query Generation Phase

1. Feed complete transcript to an LLM with a specialized prompt
2. Generate synthetic queries that target specific information in the transcript
3. Create ground truth mappings between queries and their correct chunks
4. Store queries and mappings in the labeled dataset folder

#### Chunk Generation Phase

1. Apply different chunking methods to transcripts
2. Export chunks in JSON format with metadata (chunk ID, method, context)
3. Generate embeddings for each chunk and store in vector database

#### Evaluation Phase

1. For each synthetic query, retrieve relevant chunks using embeddings
2. Measure if the correct chunk (from ground truth) was retrieved
3. Calculate retrieval metrics (precision, recall, F1 score)
4. Compare effectiveness across different chunking strategies

### 3. Chunking Methods to Evaluate

- **Fixed-size chunking**: Split by character/word count with consistent chunk sizes
- **Contextual chunking**: Maintain semantic context and topic boundaries
- **Nuggetization**: Extract key information nuggets from the transcript

## Project Structure

```
chunking-expt/
├── README.md
├── requirements.txt
├── CLAUDE.md              # Claude AI project instructions
├── 0_util/                # Utility functions and shared metrics
│   └── metrics.py         # Common evaluation metrics
├── 1_transcripts/         # Transcript processing pipeline
│   ├── raw/               # Raw video transcript files (CSV exports)
│   └── cleaned/           # Cleaned/processed transcripts
├── 2_chunks/              # Chunking tools and outputs
│   ├── fixed_size/        # Fixed-size chunked transcripts (JSON)
│   ├── contextual/        # Contextual chunked transcripts (JSON)
│   └── nuggetization/     # Nuggetized transcripts (JSON)
├── 3_database/            # Vector database and embeddings
│   └── chunk_embeddings/  # Generated embeddings for chunks
├── 4_labelled_dataset/    # Synthetic queries and labeled data
│   ├── queries/           # LLM-generated synthetic queries
│   └── query_chunk_pairs/ # Query-to-chunk ground truth mappings
├── 5_evaluation/          # Evaluation of chunking strategies
│   ├── results/           # Retrieval accuracy and performance metrics
│   └── reports/           # Analysis of chunking effectiveness
└── plan/                  # Project planning and documentation
```

## Setup

```bash
# Clone the repository
git clone [repository-url]
cd chunking-expt

# Install dependencies
uv pip install -r requirements.txt
```

## Workflow Pipeline

The project follows a numbered pipeline approach:

1. **Transcript Processing (1_transcripts/)**

   - Import raw CSV transcript exports
   - Clean and normalize transcript data
   - Prepare transcripts for chunking

2. **Chunk Generation (2_chunks/)**

   - Apply different chunking strategies
   - Export chunks as JSON with metadata
   - Each chunking method creates its own output folder

3. **Database Creation (3_database/)**

   - Generate embeddings for all chunks
   - Create vector database for similarity search
   - Index chunks for efficient retrieval

4. **Labeled Dataset Creation (4_labelled_dataset/)**

   - Use LLM to generate synthetic queries from transcripts
   - Create ground truth mappings (query → correct chunk)
   - Store as evaluation dataset

5. **Evaluation (5_evaluation/)**
   - Test retrieval accuracy for each chunking method
   - Measure if queries retrieve their correct chunks
   - Compare performance across different strategies

## Usage

```bash
# Process transcripts
uv run python 1_transcripts/clean_transcripts.py

# Generate chunks
uv run python 2_chunks/generate_chunks.py

# Create embeddings
uv run python 3_database/generate_embeddings.py

# Generate synthetic queries
uv run python 4_labelled_dataset/generate_queries.py

# Run evaluation
uv run python 5_evaluation/evaluate_chunks.py
```

## Evaluation Metrics

- **Precision@K**: Precision of top-K retrieved chunks
- **Recall@K**: Coverage of relevant information retrieved
- **Mean Reciprocal Rank (MRR)**: Average rank position of correct chunks

## Next Steps

1. Coordinate with Jair to obtain video transcripts
2. Implement baseline chunking method
3. Develop evaluation framework
4. Test and compare multiple chunking techniques
5. Document findings and recommendations
