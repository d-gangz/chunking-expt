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

#### Question Generation Phase

1. Feed complete transcript to an LLM
2. Generate 10 questions that a General Counsel (GC) might ask
3. Ensure questions are comprehensively answered within the video content

#### Evaluation Phase

1. Apply different chunking methods to transcripts
2. Use RAG to answer the generated questions
3. Compare answers against baseline (full transcript responses)
4. Measure retrieval accuracy and answer quality

### 3. Chunking Methods to Evaluate

- **Fixed-size chunking**: Split by character/word count
- **Semantic chunking**: Use embeddings to identify topic boundaries
- **Sentence-based chunking**: Maintain complete sentences
- **Sliding window**: Overlapping chunks for context preservation
- **Topic modeling**: Cluster related content
- **Speaker-aware chunking**: Maintain speaker continuity

## Project Structure

```
chunking-expt/
├── README.md
├── requirements.txt
├── transcripts/
│   ├── raw/               # Raw video transcript files
│   ├── cleaned/           # Cleaned/processed transcripts
│   └── clean_transcripts.py  # Script to clean and preprocess transcripts
├── chunks/
│   ├── fixed_size/        # Fixed-size chunked transcripts
│   ├── semantic/          # Semantic chunked transcripts
│   ├── sentence_based/    # Sentence-based chunks
│   ├── sliding_window/    # Sliding window chunks
│   └── generate_chunks.py # Script to generate chunks using different methods
├── embeddings/
│   ├── chunk_embeddings/  # Generated embeddings for chunks
│   ├── labeled_data/      # Labeled data for evaluation
│   └── generate_embeddings.py  # Script to create embeddings
├── evaluation/
│   ├── questions/         # Generated test questions
│   ├── results/           # Evaluation results (recall, precision, etc.)
│   └── evaluate_chunks.py # Script to evaluate chunking effectiveness
└── scripts/
    ├── utils.py           # Helper functions
    └── config.py          # Configuration settings
```

## Setup

```bash
# Clone the repository
git clone [repository-url]
cd chunking-expt

# Install dependencies
uv pip install -r requirements.txt
```

## Usage

[To be documented as implementation progresses]

## Evaluation Metrics

- **Retrieval Accuracy**: Percentage of relevant chunks retrieved
- **Answer Quality**: Comparison with baseline answers

## Next Steps

1. Coordinate with Jair to obtain video transcripts
2. Implement baseline chunking method
3. Develop evaluation framework
4. Test and compare multiple chunking techniques
5. Document findings and recommendations
