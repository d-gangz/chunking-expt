# Fixed Chunks Evaluation with Phoenix

This directory contains the Phoenix experiment script for evaluating the performance of the fixed chunks retrieval system using hybrid search.

## Overview

The experiment evaluates how well the fixed chunks retrieval system can find relevant chunks for a given query using:
- **Hybrid Search**: Combines vector similarity search and full-text search using Reciprocal Rank Fusion (RRF)
- **Phoenix Experiments**: Arize Phoenix framework for systematic evaluation and tracking

## Metrics

The experiment calculates the following metrics:

1. **MRR (Mean Reciprocal Rank)**: Measures how high the first relevant result appears in the ranking
   - Score range: 0 to 1 (higher is better)
   - MRR = 1 means the first result is always relevant
   - MRR = 0.5 means the first relevant result is typically at position 2
   
2. **Recall**: Measures the proportion of relevant chunks that were retrieved
   - Score range: 0 to 1 (higher is better)
   - Recall = 1 means all relevant chunks were found

3. **Precision**: Measures the proportion of retrieved chunks that are relevant
   - Evaluated at all retrieved results (configurable via search_results_count)
   - Score range: 0 to 1 (higher is better)

## Prerequisites

1. **Dependencies**: Install required packages
   ```bash
   pip install arize-phoenix pandas openai psycopg2-binary python-dotenv nest-asyncio
   ```

2. **Environment Variables**: Ensure `.env` file contains:
   ```
   OPENAI_API_KEY=your-openai-api-key
   SUPABASE_CONNECTION_STRING=your-supabase-connection-string
   ```

3. **Database Setup**: The fixed_chunks table must be populated with embeddings
   - Run the embedding pipeline in `3_database/fixed_chunks/`
   - Ensure the `hybrid_search_fixed_chunks` SQL function exists

4. **Dataset**: The Phoenix dataset must exist at:
   ```
   4_labelled_dataset/fixed_chunks/generate-dataset/phoenix_dataset_simplified_v2.json
   ```

## Running the Experiment

### Basic Usage

```bash
# Navigate to the evaluation directory
cd 5_evaluation/fixed_chunks/

# Run the experiment
uv run python run_phoenix_experiment.py
```

### What Happens

1. **Phoenix Launch**: Opens Phoenix UI at http://localhost:6006
2. **Dataset Loading**: Loads and uploads the evaluation dataset to Phoenix
3. **Dry Run**: Runs on 3 examples first for validation
4. **User Confirmation**: Asks if you want to proceed with full experiment
5. **Full Experiment**: Evaluates all queries in the dataset
6. **Results**: Displays summary statistics in console and Phoenix UI

### Experiment Flow

```
1. Load Dataset → 2. Dry Run (3 examples) → 3. Confirm → 4. Full Run → 5. Results
```

## Output

The experiment produces:

1. **Console Output**: Summary statistics including:
   - Overall MRR, Recall, and Precision scores with standard deviations
   - Results broken down by difficulty level (easy, medium, hard)

2. **Phoenix UI**: Interactive visualization at http://localhost:6006
   - Navigate to Experiments tab
   - Find your experiment by name: `fixed_chunks_eval_at{N}_{timestamp}`
   - Where N is the number of search results (e.g., at10, at20, at30)

## Understanding Results

### Good Performance Indicators
- MRR > 0.5: First relevant result typically in top 2
- Recall > 0.7: Finding most relevant chunks
- Precision > 0.3: Good relevance in retrieved results

### Poor Performance Indicators
- MRR < 0.2: Relevant results buried deep
- Recall < 0.3: Missing many relevant chunks
- Many retrieval errors

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   Solution: Install missing packages with pip
   ```

2. **Database Connection Failed**
   ```
   Solution: Check SUPABASE_CONNECTION_STRING in .env
   ```

3. **No Chunks Found**
   ```
   Solution: Run the embedding pipeline first in 3_database/fixed_chunks/
   ```

4. **Phoenix Won't Start**
   ```
   Solution: Check if port 6006 is already in use
   ```

## Customization

### Modify Search Parameters

In `run_phoenix_experiment.py`, adjust the number of search results:
```python
class FixedChunksExperiment:
    def __init__(self, dataset_path: str):
        # ...
        self.search_results_count = 30  # Change this to 10, 20, 30, etc.
```

This will:
- Retrieve that many results per query
- Update the experiment name (e.g., `fixed_chunks_eval_at30_timestamp`)
- Adjust precision calculation to evaluate all retrieved results

### Add New Metrics

Add custom evaluators in the `create_evaluators()` method:
```python
@create_evaluator(name="YourMetric", kind="CODE")
def your_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
    # Your metric calculation
    retrieved_ids = output.get("retrieved_chunk_ids", [])
    expected_ids = json.loads(expected.get("expected_chunk_ids", "[]"))
    
    # Calculate your metric
    score = your_calculation(retrieved_ids, expected_ids)
    return score
```

## Next Steps

After running the experiment:

1. **Analyze Results**: Review metrics to identify weaknesses
2. **Optimize Parameters**: Adjust search parameters if needed
3. **Compare Strategies**: Run similar experiments for other chunking strategies
4. **Iterate**: Improve chunking or retrieval based on findings

## Related Files

- **Dataset**: `4_labelled_dataset/fixed_chunks/generate-dataset/phoenix_dataset_simplified_v2.json`
- **Metrics**: `0_util/metrics.py`
- **Hybrid Search**: `3_database/common/hybrid_search.py`
- **Database Setup**: `3_database/fixed_chunks/`