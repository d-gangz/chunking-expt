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

# Examples:
uv run python transcripts/clean_transcripts.py
uv run python chunks/generate_chunks.py
uv run python embeddings/generate_embeddings.py
uv run python evaluation/evaluate_chunks.py
```

## Important Tool Usage

### Web Searches

Always use the `perplexity_ask` tool for web searches instead of other search methods. This provides more accurate and up-to-date information.

## Project Architecture

[to be determined]

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

- Add comprehensive docstrings to all Python scripts describing their purpose and functionality
- Include inline comments to explain complex logic or non-obvious code segments
- Aim for clear, concise documentation that helps other developers understand the code quickly