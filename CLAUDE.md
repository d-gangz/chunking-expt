# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a transcript chunking experiment project aimed at optimizing video transcript retrieval for Q&A systems. The goal is to develop and evaluate different chunking techniques to enable effective Retrieval-Augmented Generation (RAG) for answering questions from video content.

The project implements a systematic evaluation framework using Phoenix (by Arize) to compare different chunking strategies, with automated experiment management, PostgreSQL + pgvector for vector search, and comprehensive metrics tracking.

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

### Database Setup

```bash
# Start PostgreSQL with pgvector using Docker
cd 3_database/docker
docker-compose up -d

# Verify database is running
docker-compose ps

# Stop database when done
docker-compose down
```

### Running Scripts

Always use UV to run Python scripts:

```bash
# Run any Python script
uv run python script_name.py

# Examples by stage:
uv run python 1_transcripts/clean_transcripts.py                    # With timestamps
uv run python 1_transcripts/clean_transcripts_no_timestamp.py       # Without timestamps
uv run python 2_chunks/fixed_chunks/generate_chunks.py              # Generate fixed chunks
uv run python 3_database/fixed_chunks/scripts/run_embedding_pipeline.py  # Generate embeddings
uv run python 4_labelled_dataset/fixed_chunks/generate-dataset/generate_phoenix_dataset_v2.py  # Create evaluation dataset
uv run python 5_evaluation/fixed_chunks/run_phoenix_experiment.py   # Run Phoenix evaluation
```

## Project Architecture

### File Organization Structure

The project follows a numbered folder structure where each stage of the pipeline has its own directory. Each folder contains:

- Raw data files (input)
- Python scripts for processing
- Results/output files
- CLAUDE.md documentation for each directory

```
chunking-expt/
├── 0_util/                    # Utility functions and shared modules
│   ├── CLAUDE.md              # Directory documentation
│   └── metrics.py             # Evaluation metrics (MRR, recall, precision)
├── 1_transcripts/             # Transcript processing stage
│   ├── CLAUDE.md              # Directory documentation
│   ├── raw/                   # Raw transcript files (CSVs)
│   ├── cleaned-timestamp/     # Cleaned transcripts with timestamps
│   ├── cleaned-full/          # Cleaned transcripts without timestamps
│   ├── clean_transcripts.py   # Processing script with timestamps
│   └── clean_transcripts_no_timestamp.py  # Processing without timestamps
├── 2_chunks/                  # Chunking stage
│   ├── CLAUDE.md              # Directory documentation
│   └── fixed_chunks/          # Fixed-size chunking strategy
│       ├── chunks/            # Generated chunks output
│       ├── chunk_verify/      # Timing verification tools
│       └── generate_chunks.py # Fixed chunking script
├── 3_database/                # Database and embeddings stage
│   ├── CLAUDE.md              # Directory documentation
│   ├── README.md              # Database setup guide
│   ├── docker/                # PostgreSQL + pgvector Docker setup
│   │   ├── docker-compose.yml # Docker configuration
│   │   └── postgres/          # PostgreSQL init scripts
│   ├── common/                # Shared database utilities
│   │   ├── chunk_embedder.py  # Embedding generation
│   │   ├── hybrid_search.py   # Hybrid search implementation
│   │   └── setup/             # SQL templates
│   └── fixed_chunks/          # Fixed chunks database implementation
│       ├── scripts/           # Database pipeline scripts
│       ├── setup/             # SQL setup files
│       └── tests/             # Database tests
├── 4_labelled_dataset/        # Labelled data for evaluation
│   ├── CLAUDE.md              # Directory documentation
│   ├── baseline-questions/    # Base ground truth questions
│   │   ├── base_ground_truth.json  # Strategy-agnostic ground truth
│   │   └── insights.json      # Question categorization
│   └── fixed_chunks/          # Fixed chunks dataset
│       ├── generate-dataset/  # Phoenix dataset generation
│       └── retrieve-chunks/   # Chunk retrieval utilities
├── 5_evaluation/              # Evaluation stage
│   ├── CLAUDE.md              # Directory documentation
│   ├── fixed_chunks/          # Fixed chunks evaluation
│   │   ├── README.md          # Phoenix experiment guide
│   │   └── run_phoenix_experiment.py  # Phoenix evaluation script
│   └── phoenix/               # Phoenix experiment tracking
│       ├── phoenix.db         # Experiment database
│       ├── exports/           # Exported results
│       └── trace_datasets/    # Traced evaluations
├── communication/             # Team communication and planning
│   ├── CLAUDE.md              # Directory documentation
│   ├── 1-aug.md               # Team updates
│   ├── expt-plan.md           # Experiment methodology
│   └── request.md             # Project requirements
└── tasks/                     # PRDs and task management
    ├── CLAUDE.md              # Directory documentation
    ├── prd-*.md               # Product requirement documents
    └── tasks-*.md             # Implementation task lists
```

### Folder Organization Principles

1. **Numbered Folders**: Each folder is numbered (0-5) to indicate the pipeline order
2. **Self-Contained**: Each folder contains all inputs, scripts, and outputs for that stage
3. **Clear Separation**: Raw data, scripts, and results are clearly separated within each folder
4. **Progressive Pipeline**: Output from one stage becomes input for the next stage

## Evaluation Framework

### Phoenix-Based Evaluation

The project uses Arize Phoenix for systematic experiment tracking and evaluation:

```bash
# Run Phoenix evaluation for fixed chunks
cd 5_evaluation/fixed_chunks/
uv run python run_phoenix_experiment.py

# Phoenix UI will open at http://localhost:6006
```

### Metrics

The evaluation framework tracks three key metrics:

1. **MRR (Mean Reciprocal Rank)**: Measures ranking quality

   - 1.0 = perfect (first result always relevant)
   - 0.5 = first relevant result typically at position 2

2. **Recall**: Proportion of relevant chunks retrieved

   - 1.0 = all relevant chunks found
   - Important for comprehensive answers

3. **Precision**: Proportion of retrieved chunks that are relevant
   - Evaluated at configurable retrieval counts (10, 20, 30)
   - Balances quality vs quantity

### Hybrid Search

The system implements hybrid search combining:

- **Vector Search**: Semantic similarity using embeddings
- **Full-Text Search**: Keyword matching
- **Reciprocal Rank Fusion (RRF)**: Combines both approaches

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

### Experiment Management:

```python
# Phoenix experiment naming convention
experiment_name = f"fixed_chunks_eval_at{search_results_count}_{timestamp}"

# Dataset versioning
dataset_path = "phoenix_dataset_simplified_v2.json"
```

## Recent Updates (Updated: 2025-08-03)

### Major Changes

1. **Phoenix Evaluation Framework**: Implemented comprehensive evaluation using Arize Phoenix with MRR, recall, and precision metrics
2. **Fixed Chunking Strategy**: Added fixed-size chunking with configurable chunk sizes and overlaps
3. **Local PostgreSQL + pgvector**: Migrated from cloud Supabase to local Docker-based PostgreSQL with pgvector extension
4. **Hybrid Search**: Implemented Reciprocal Rank Fusion (RRF) combining vector and full-text search
5. **Subdirectory Documentation**: Added CLAUDE.md files to all major directories for better code navigation
6. **Timestamp Options**: Added transcript cleaning with and without timestamps for different use cases
7. **Team Communication**: Established structured experiment planning and PRD-driven development

### Infrastructure Improvements

- Docker-based database setup for reproducibility
- Automated chunking strategy setup scripts
- Comprehensive test suites for database operations
- Phoenix experiment tracking with persistent storage

## Important Notes

### Environment Setup

1. **Required Environment Variables** (.env file):

   ```
   OPENAI_API_KEY=your-openai-api-key
   SUPABASE_CONNECTION_STRING=postgresql://postgres:postgres@localhost:5432/postgres
   ```

2. **Database Must Be Running**: Start PostgreSQL before running database operations:

   ```bash
   cd 3_database/docker && docker-compose up -d
   ```

3. **Use UV for Python**: All Python scripts must be run with `uv run` prefix

### Development Workflow

1. **Strategy-Agnostic Ground Truth**: All chunking strategies use the same base ground truth from `4_labelled_dataset/baseline-questions/`
2. **Experiment Tracking**: Phoenix UI tracks all experiments with versioned datasets
3. **Parallel Processing**: Use ThreadPoolExecutor for batch operations (MAX_WORKERS=32)
4. **Documentation First**: Update CLAUDE.md files when adding new features or changing architecture

### Key Design Decisions

- **Numbered Directories**: Pipeline stages are numbered 0-5 for clear execution order
- **Self-Contained Stages**: Each directory contains inputs, scripts, and outputs
- **Hybrid Search Default**: All retrieval uses combined vector + text search
- **Phoenix for Evaluation**: Standardized on Phoenix for experiment tracking and metrics
