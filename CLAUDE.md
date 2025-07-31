# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a transcript chunking experiment project aimed at optimizing video transcript retrieval for Q&A systems. The goal is to develop and evaluate different chunking techniques to enable effective Retrieval-Augmented Generation (RAG) for answering questions from video content.

## Key Commands

### Development Setup

```bash
# Install dependencies using uv
uv pip install -r requirements.txt

# Format code with Black
uv run black .

# Run linting
uv run pylint <module_name>

# Type checking
uv run mypy <module_name>
```

### Running Scripts

Always use UV to run Python scripts:

```bash
# Run any Python script
uv run python script_name.py

# Examples by stage:
uv run python 1_transcripts/clean_transcripts.py
uv run python 2_chunks/generate_chunks.py
uv run python 3_database/generate_embeddings.py
uv run python 4_labelled_dataset/generate_labels.py
uv run python 5_evaluation/evaluate_chunks.py
```

## Important Tool Usage

### Web Searches

Always use the `WebSearch` tool for web searches instead of other search methods. This provides more accurate and up-to-date information.

### Web links

If user provide web links, always use `WebFetch` to fetch the contents.

## Project Architecture

### File Organization Structure

The project follows a numbered folder structure where each stage of the pipeline has its own directory. Each folder contains:

- Raw data files (input)
- Python scripts for processing
- Results/output files

```
chunking-expt/
├── 0_util/              # Utility functions and shared modules
│   ├── metrics.py       # Evaluation metrics
│   └── [other utils]
├── 1_transcripts/       # Transcript processing stage
│   ├── raw/             # Raw transcript files (CSVs)
│   ├── cleaned/         # Cleaned transcript outputs
│   └── clean_transcripts.py  # Processing script
├── 2_chunks/            # Chunking stage
│   ├── raw/             # Input transcripts
│   ├── chunks/          # Generated chunks output
│   └── generate_chunks.py    # Chunking script
├── 3_database/          # Database and embeddings stage
│   ├── embeddings/      # Generated embeddings
│   ├── db/              # Vector database files
│   └── generate_embeddings.py # Embedding script
├── 4_labelled_dataset/  # Labelled data for evaluation
│   ├── questions/       # Question-answer pairs
│   ├── ground_truth/    # Ground truth mappings
│   └── generate_labels.py    # Labelling script
└── 5_evaluation/        # Evaluation stage
    ├── results/         # Evaluation results
    ├── reports/         # Generated reports
    └── evaluate_chunks.py    # Evaluation script
```

### Folder Organization Principles

1. **Numbered Folders**: Each folder is numbered (0-5) to indicate the pipeline order
2. **Self-Contained**: Each folder contains all inputs, scripts, and outputs for that stage
3. **Clear Separation**: Raw data, scripts, and results are clearly separated within each folder
4. **Progressive Pipeline**: Output from one stage becomes input for the next stage

## General Evaluation Architecture Patterns

### Parallel Processing Pattern:

```python
MAX_WORKERS = 32  # Optimize for your system

def process_batch(items, process_func):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_func, item): item for item in items}
        results = []
        for future in tqdm(as_completed(futures), total=len(items)):
            results.append(future.result())
    return results
```

### Progress Tracking:

```python
# Use tqdm for long operations
for item in tqdm(items, desc="Processing"):
    process(item)

# Use rich.console for detailed status
with console.status("[yellow]Evaluating traces...") as status:
    for i, trace in enumerate(traces):
        status.update(f"Processing {i+1}/{len(traces)}")
```

## Code Documentation Guidelines

- Add comprehensive docstrings at the top of all Python scripts describing their purpose and functionality
- **Always specify where the script obtains its input data** (e.g., file paths, directories, APIs)
- Include inline comments to explain complex logic or non-obvious code segments
- Aim for clear, concise documentation that helps other developers understand the code quickly

Example docstring format:
```python
"""
Script to process transcript chunks and generate embeddings.

Input: Reads chunks from 2_chunks/chunks/
Output: Saves embeddings to 3_database/embeddings/
Dependencies: Requires OpenAI API key in .env file
"""
```
