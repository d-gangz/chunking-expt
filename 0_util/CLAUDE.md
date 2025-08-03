# What This Does

Provides shared utility functions for evaluation metrics used throughout the chunking experiment pipeline, particularly for measuring retrieval quality.

# File Structure

```
├── metrics.py # Evaluation metrics (MRR, recall) for retrieval quality
```

# Quick Start

- Entry point: `metrics.py` - exports evaluation functions
- Import: `from metrics import calculate_mrr, calculate_recall`
- Test: Run evaluation scripts that use these metrics

# How It Works

This module provides standardized evaluation metrics that measure how well the retrieval system finds relevant chunks for given queries by comparing retrieved results against expected ground truth.

# Interfaces

```python
# Main exports and their signatures
calculate_mrr(output: list[str], expected: list[str]) -> float
calculate_recall(output: list[str], expected: list[str]) -> float

# Example usage:
mrr_score = calculate_mrr(retrieved_chunks, ground_truth_chunks)
recall_score = calculate_recall(retrieved_chunks, ground_truth_chunks)
```

# Dependencies

**Code Dependencies:**
- No external imports - pure Python implementation

**Cross-Directory Usage:**
- Called by: `/5_evaluation/fixed_chunks/run_phoenix_experiment.py` - evaluation scripts
- Used for: Calculating retrieval quality metrics in evaluation pipelines

# Key Patterns

- Pure functions with no side effects
- List-based comparison of retrieved vs expected items
- MRR rewards higher-ranked relevant results

# Common Tasks

- Calculate MRR: Pass retrieved and expected chunk lists
- Calculate recall: Measure proportion of relevant items retrieved
- Combine metrics: Use both for comprehensive evaluation

# Recent Updates

- Core metric functions established for evaluation pipeline
- Used in Phoenix experiment evaluation

# Watch Out For

- Order matters for MRR calculation
- Empty expected lists will cause division by zero in recall
- Assumes chunk IDs are comparable strings