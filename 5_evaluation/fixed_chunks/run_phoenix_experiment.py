"""
Phoenix experiment script for evaluating fixed chunks retrieval performance.

This script runs experiments using Arize Phoenix to evaluate the performance of
the fixed chunks retrieval system using MRR (Mean Reciprocal Rank) and Recall metrics.

Input: Reads Phoenix dataset from 4_labelled_dataset/fixed_chunks/generate-dataset/phoenix_dataset_simplified_v2.json
Output: Experiment results with MRR and Recall metrics for each query
Dependencies: Requires Phoenix, OpenAI API key, and Supabase connection string in .env file
"""

import os
import sys
import json
import phoenix as px
import pandas as pd
from phoenix.experiments import run_experiment
from phoenix.experiments.evaluators import create_evaluator
from phoenix.experiments.types import Example
from typing import List, Dict, Any
from datetime import datetime

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
util_path = os.path.join(project_root, "0_util")
db_path = os.path.join(project_root, "3_database")

sys.path.insert(0, util_path)
sys.path.insert(0, db_path)

# Import metrics and hybrid search
from metrics import calculate_mrr, calculate_recall  # type: ignore
from common.hybrid_search import HybridSearch  # type: ignore

# Try to import and apply nest_asyncio for Jupyter environments
try:
    import nest_asyncio  # type: ignore

    nest_asyncio.apply()
except ImportError:
    pass  # Not required for non-Jupyter environments


class FixedChunksExperiment:
    """Manages Phoenix experiments for fixed chunks evaluation."""

    def __init__(self, dataset_path: str):
        """
        Initialize the experiment with dataset path.

        Args:
            dataset_path: Path to the Phoenix dataset JSON file
        """
        self.dataset_path = dataset_path
        self.searcher = HybridSearch("fixed_chunks")
        self.search_results_count = 30  # Number of results to retrieve
        self.experiment_metadata = {
            "experiment_type": "fixed_chunks_retrieval",
            "model": "text-embedding-3-large",
            "embedding_dimensions": 1024,
            "retrieval_method": "hybrid_search",
            "timestamp": datetime.now().isoformat(),
            "chunking_strategy": "fixed_chunks",
            "search_results_count": self.search_results_count,
        }

    def load_phoenix_dataset(self):
        """
        Load the Phoenix dataset from JSON file.

        Data flow in Phoenix:
        - input_keys columns -> available in task function and evaluators via 'input' parameter
        - output_keys columns -> available in evaluators via 'expected' parameter
        - metadata_keys columns -> available in evaluators via 'metadata' parameter
        - task function output -> available in evaluators via 'output' parameter

        Returns:
            Phoenix Dataset object
        """
        print(f"Loading dataset from {self.dataset_path}...")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Transform data into DataFrame format for Phoenix
        rows = []
        for item in data:
            row = {
                "question_id": item["metadata"]["question_id"],
                "query": item["input"],  # The question/query text
                "expected_chunk_ids": json.dumps(
                    item["expected"]
                ),  # Serialize list as JSON string
                "difficulty": item["metadata"]["difficulty"],
                "comprehensive_answer": item["metadata"]["comprehensive_answer"],
                "source_quotes": json.dumps(
                    item["metadata"]["source_quotes"]
                ),  # Serialize as JSON
            }
            rows.append(row)

        # Create pandas DataFrame
        df = pd.DataFrame(rows)

        # Check if dataset already exists in Phoenix
        client = px.Client()
        dataset_name = "fixed_chunks_evaluation"

        try:
            # Try to get the existing dataset
            dataset = client.get_dataset(name=dataset_name)
            print(f"Using existing dataset: {dataset_name}")
        except:
            # Dataset doesn't exist, upload it
            print(f"Uploading new dataset: {dataset_name}")
            dataset = client.upload_dataset(
                dataframe=df,
                input_keys=["query"],  # Input column(s)
                output_keys=["expected_chunk_ids"],  # Expected output for evaluation
                metadata_keys=[
                    "question_id",
                    "difficulty",
                    "comprehensive_answer",
                    "source_quotes",
                ],  # Additional metadata
                dataset_name=dataset_name,
            )

        print(f"Loaded {len(df)} examples into Phoenix dataset")
        return dataset

    def hybrid_search_task(self, example: Example) -> Dict[str, Any]:
        """
        Task function that performs hybrid search for a given query.

        Args:
            example: Phoenix Example object containing input query

        Returns:
            Dictionary containing retrieved chunk IDs and search results
        """
        query = example.input.get("query") or example.input.get("question")

        try:
            # Perform hybrid search
            search_results = self.searcher.search(
                query=query,
                match_count=self.search_results_count,  # Retrieve top N results
                rrf_k=60,  # RRF constant
            )

            # Extract chunk IDs from results
            retrieved_ids = [result["id"] for result in search_results]

            # Return results
            return {
                "retrieved_chunk_ids": retrieved_ids,
                "search_results": search_results,
                "query": query,
                "num_results": len(search_results),
            }

        except Exception as e:
            print(f"Error during search for query '{query}': {e}")
            return {
                "retrieved_chunk_ids": [],
                "search_results": [],
                "query": query,
                "error": str(e),
                "num_results": 0,
            }

    def create_evaluators(self) -> List:
        """
        Create custom evaluators for MRR and Recall metrics.

        Returns:
            List of evaluator functions
        """

        @create_evaluator(name="MRR", kind="CODE")
        def mrr_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
            """Calculate Mean Reciprocal Rank (MRR) for retrieved chunks."""
            retrieved_ids = output.get("retrieved_chunk_ids", [])

            # Get expected IDs from expected parameter
            expected_chunk_ids_str = expected.get("expected_chunk_ids", "[]")
            expected_ids = (
                json.loads(expected_chunk_ids_str)
                if isinstance(expected_chunk_ids_str, str)
                else expected_chunk_ids_str
            )

            # Convert to strings for comparison (in case of type mismatch)
            retrieved_ids = [str(id) for id in retrieved_ids]
            expected_ids = [str(id) for id in expected_ids]

            # Calculate MRR using imported function
            mrr_score = calculate_mrr(retrieved_ids, expected_ids)

            return mrr_score

        @create_evaluator(name="Recall", kind="CODE")
        def recall_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
            """Calculate Recall for retrieved chunks."""
            retrieved_ids = output.get("retrieved_chunk_ids", [])

            # Get expected IDs from expected parameter
            expected_chunk_ids_str = expected.get("expected_chunk_ids", "[]")
            expected_ids = (
                json.loads(expected_chunk_ids_str)
                if isinstance(expected_chunk_ids_str, str)
                else expected_chunk_ids_str
            )

            # Convert to strings for comparison
            retrieved_ids = [str(id) for id in retrieved_ids]
            expected_ids = [str(id) for id in expected_ids]

            # Calculate recall using imported function
            recall_score = calculate_recall(retrieved_ids, expected_ids)

            return recall_score

        @create_evaluator(name="Precision", kind="CODE")
        def precision_at_k_evaluator(
            output: Dict[str, Any], expected: Dict[str, Any]
        ) -> float:
            """Calculate Precision for retrieved chunks."""
            k = self.search_results_count  # Evaluate precision at all retrieved results
            retrieved_ids = output.get("retrieved_chunk_ids", [])[:k]

            # Get expected IDs from expected parameter
            expected_chunk_ids_str = expected.get("expected_chunk_ids", "[]")
            expected_ids = (
                json.loads(expected_chunk_ids_str)
                if isinstance(expected_chunk_ids_str, str)
                else expected_chunk_ids_str
            )

            # Convert to strings for comparison
            retrieved_ids = [str(id) for id in retrieved_ids]
            expected_ids = [str(id) for id in expected_ids]

            # Calculate precision@k
            if not retrieved_ids:
                precision = 0.0
            else:
                relevant_in_top_k = len(
                    [id for id in retrieved_ids if id in expected_ids]
                )
                precision = relevant_in_top_k / len(retrieved_ids)

            return precision

        return [mrr_evaluator, recall_evaluator, precision_at_k_evaluator]

    def run_experiment(self, dry_run: bool = True):
        """
        Run the Phoenix experiment.

        Args:
            dry_run: If True, run on small subset first (default: True)
        """
        # Phoenix should be running already (launched manually)
        print("Connecting to Phoenix instance at http://localhost:6006")

        # Load dataset
        dataset = self.load_phoenix_dataset()

        # Create evaluators
        evaluators = self.create_evaluators()
        evaluator_names = []
        for e in evaluators:
            if hasattr(e, "__name__"):
                evaluator_names.append(e.__name__)
            elif hasattr(e, "name"):
                evaluator_names.append(e.name)
            else:
                evaluator_names.append(str(type(e).__name__))
        print(f"Created {len(evaluators)} evaluators: {evaluator_names}")

        # Experiment name with timestamp and search results count
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"fixed_chunks_eval_at{self.search_results_count}_{timestamp}"

        # Run dry run if requested
        if dry_run:
            print("\n=== Running Dry Run ===")
            dry_run_size = min(3, len(dataset.examples))

            dry_experiment = run_experiment(
                dataset=dataset,
                task=self.hybrid_search_task,
                evaluators=evaluators,
                experiment_name=f"{experiment_name}_dry_run",
                experiment_description="Dry run for fixed chunks retrieval evaluation",
                experiment_metadata={**self.experiment_metadata, "run_type": "dry_run"},
                dry_run=dry_run_size,
            )

            print(f"Dry run completed with {len(dry_experiment)} examples")

            # Get dry run results
            dry_results = dry_experiment.get_evaluations()
            print("\nDry Run Results Summary:")
            print(dry_results.describe())

            # Ask if user wants to continue (with non-interactive fallback)
            try:
                user_input = input("\nProceed with full experiment? (y/n): ")
                if user_input.lower() != "y":
                    print("Experiment cancelled.")
                    return
            except EOFError:
                # Non-interactive mode, proceed automatically
                print(
                    "\nRunning in non-interactive mode, proceeding with full experiment..."
                )

        # Run full experiment
        print("\n=== Running Full Experiment ===")
        print(f"Processing {len(dataset.examples)} examples...")

        full_experiment = run_experiment(
            dataset=dataset,
            task=self.hybrid_search_task,
            evaluators=evaluators,
            experiment_name=experiment_name,
            experiment_description="Full evaluation of fixed chunks retrieval using hybrid search",
            experiment_metadata={**self.experiment_metadata, "run_type": "full"},
        )

        print(f"\nFull experiment completed with {len(full_experiment)} runs")

        # Get and display results
        results_df = full_experiment.get_evaluations()

        print("\n=== Experiment Results ===")
        print(f"Experiment ID: {full_experiment.id}")
        print(f"Experiment Name: {experiment_name}")

        # Calculate overall metrics
        print("\nOverall Metrics:")
        for metric in ["MRR", "Recall", "Precision"]:
            if metric in results_df.columns:
                mean_score = results_df[metric].mean()
                std_score = results_df[metric].std()
                print(f"  {metric}: {mean_score:.4f} (±{std_score:.4f})")

        # Results by difficulty
        print("\nResults by Difficulty:")
        difficulty_cols = [
            col for col in results_df.columns if "difficulty" in col.lower()
        ]
        if difficulty_cols:
            # Group by difficulty if available
            for difficulty in ["easy", "medium", "hard"]:
                difficulty_mask = results_df[difficulty_cols[0]] == difficulty
                if difficulty_mask.any():
                    print(f"\n  {difficulty.capitalize()}:")
                    subset = results_df[difficulty_mask]
                    for metric in ["MRR", "Recall"]:
                        if metric in subset.columns:
                            print(f"    {metric}: {subset[metric].mean():.4f}")

        # Phoenix UI link
        print(f"\nView detailed results in Phoenix UI: http://localhost:6006")
        print(f"Navigate to Experiments > {experiment_name}")

        return full_experiment


def main():
    """Main function to run the Phoenix experiment."""
    # Dataset path
    dataset_path = "/Users/gang/suite-work/chunking-expt/4_labelled_dataset/fixed_chunks/generate-dataset/phoenix_dataset_simplified_v2.json"

    # Check if dataset exists
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please ensure the Phoenix dataset has been generated.")
        return

    # Initialize experiment
    experiment = FixedChunksExperiment(dataset_path)

    # Run experiment (with dry run by default)
    try:
        experiment.run_experiment(dry_run=True)
    except Exception as e:
        print(f"\nExperiment failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Phoenix is installed: pip install arize-phoenix")
        print("2. Verify OPENAI_API_KEY is set in .env file")
        print("3. Verify SUPABASE_CONNECTION_STRING is set in .env file")
        print("4. Ensure the fixed_chunks table has data and embeddings")
        print(
            "5. Check that the hybrid_search_fixed_chunks function exists in database"
        )


if __name__ == "__main__":
    main()
