# What This Does

Evaluates chunking strategies using Arize Phoenix for experiment tracking, measuring retrieval quality with MRR and Recall metrics against ground truth datasets.

# File Structure

```
├── fixed_chunks/                    # Fixed chunks evaluation
│   ├── run_phoenix_experiment.py   # Main evaluation script
│   └── README.md                   # Strategy-specific docs
├── phoenix/                        # Phoenix data storage
│   ├── phoenix.db                 # Experiment database
│   ├── exports/                   # Exported results
│   ├── inferences/                # Model outputs
│   └── trace_datasets/            # Traced datasets
└── phoenix-instructions.md        # Phoenix server setup
```

# Quick Start

- Entry point: `fixed_chunks/run_phoenix_experiment.py`
- Run eval: `uv run python 5_evaluation/fixed_chunks/run_phoenix_experiment.py`
- Launch Phoenix: `export PHOENIX_WORKING_DIR=.../5_evaluation/phoenix && phoenix serve`
- View results: Open http://localhost:6006 in browser

# How It Works

The evaluation runs retrieval experiments using hybrid search, compares retrieved chunks against ground truth labels, and calculates MRR/Recall metrics. Phoenix tracks all experiments, enabling comparison across different retrieval parameters and strategies.

# Interfaces

```python
# Experiment configuration
task = lambda example: {
    "output": searcher.search(
        query=example["query"],
        match_count=k,  # Configurable retrieval count
        as_chunks=False  # Return chunk IDs only
    )
}

# Metrics calculation
evaluator = create_evaluator(
    name="retrieval_metrics",
    description="MRR and Recall evaluation",
    evaluate=lambda output, expected: {
        "mrr": calculate_mrr(output, expected),
        "recall": calculate_recall(output, expected)
    }
)
```

# Dependencies

**Code Dependencies:**
- Imports from: `/0_util/metrics.py` - MRR and Recall functions
- Imports from: `/3_database/common/hybrid_search.py` - Retrieval
- Uses Phoenix for experiment tracking
- ThreadPoolExecutor for parallel processing
- Rich console for status display

**Data Dependencies:**
- Reads from: `/4_labelled_dataset/*/phoenix_dataset_simplified_v2.json`
- Connects to: PostgreSQL database for retrieval
- Writes to: `/phoenix/` - experiment results

**Cross-Directory Usage:**
- Evaluates: Chunking strategies from `/2_chunks/`
- Tests: Retrieval quality from `/3_database/`
- Uses: Ground truth from `/4_labelled_dataset/`

# Key Patterns

- Configurable retrieval count (k parameter: 10, 20, 30)
- Phoenix experiment tracking and visualization
- Parallel processing with ThreadPoolExecutor (32 workers)
- Rich console output for progress tracking
- Precision metrics at different retrieval counts

# Common Tasks

- Run experiment: Execute run_phoenix_experiment.py
- Change k values: Modify RETRIEVAL_COUNTS list
- View results: Launch Phoenix server and browse UI
- Export results: Use Phoenix export functionality
- Compare experiments: Use Phoenix UI comparison features

# Recent Updates

- Added configurable retrieval count experiments (3845064)
- Implemented Phoenix integration for tracking
- Enhanced with rich console output
- Added comprehensive error handling
- Precision metrics calculation for variable k

# Watch Out For

- Phoenix server must be running to view results
- Set PHOENIX_WORKING_DIR for persistent storage
- Database must be running for retrieval
- Async handling needed for Jupyter environments (nest_asyncio)
- Retrieval counts impact both recall and precision metrics