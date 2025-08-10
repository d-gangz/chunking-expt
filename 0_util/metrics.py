"""
Evaluation metrics for Retrieval-Augmented Generation (RAG) systems.

Input data sources: Retrieved results and ground truth labels from evaluation pipelines
Output destinations: Metric scores for evaluation analysis
Dependencies: None (pure Python implementation)
Key exports: calculate_mrr(), calculate_recall(), calculate_precision()
Side effects: None (pure functions)

EVALUATION METRICS GUIDE:

This module provides three key metrics for evaluating retrieval quality in RAG systems:

1. MEAN RECIPROCAL RANK (MRR)
   - Measures ranking quality by rewarding higher-ranked relevant results
   - Formula: MRR = max(1/rank) for all relevant items found
   - Range: 0.0 to 1.0 (higher is better)
   - Interpretation:
     * 1.0 = Perfect (first result is always relevant)
     * 0.5 = First relevant result typically at position 2
     * 0.0 = No relevant results found
   - Use case: When result ranking matters (e.g., showing top results to users)

2. RECALL
   - Measures completeness by calculating proportion of relevant items retrieved
   - Formula: Recall = (Relevant Items Retrieved) / (Total Relevant Items)
   - Range: 0.0 to 1.0 (higher is better)
   - Interpretation:
     * 1.0 = Perfect (all relevant items found)
     * 0.7 = Found 70% of all relevant items
     * 0.0 = No relevant items found
   - Use case: When you need comprehensive coverage (e.g., research queries)

3. PRECISION
   - Measures relevance by calculating proportion of retrieved items that are relevant
   - Formula: Precision = (Relevant Items Retrieved) / (Total Items Retrieved)
   - Range: 0.0 to 1.0 (higher is better)
   - Interpretation:
     * 1.0 = Perfect (all retrieved items are relevant)
     * 0.5 = Half of retrieved items are relevant
     * 0.0 = No retrieved items are relevant
   - Use case: When you want to minimize irrelevant results (resource efficiency)

USAGE PATTERNS:

# Single query evaluation
retrieved_chunks = ["chunk_1", "chunk_5", "chunk_3", "chunk_8"]
ground_truth = ["chunk_1", "chunk_3", "chunk_7"]

mrr = calculate_mrr(retrieved_chunks, ground_truth)      # 1.0 (chunk_1 at position 1)
recall = calculate_recall(retrieved_chunks, ground_truth) # 0.67 (2 of 3 relevant found)
precision = calculate_precision(retrieved_chunks, ground_truth) # 0.5 (2 of 4 retrieved are relevant)

# Batch evaluation across multiple queries
for query, results, truth in evaluation_dataset:
    scores.append({
        'mrr': calculate_mrr(results, truth),
        'recall': calculate_recall(results, truth),
        'precision': calculate_precision(results, truth)
    })

IMPORTANT NOTES:
- All functions expect lists of comparable identifiers (strings, IDs)
- Order matters for MRR calculation (first element = rank 1)
- Empty ground truth lists will raise ZeroDivisionError for recall
- Empty retrieved lists will return 0.0 for all metrics
- Functions assume no duplicates within each list
"""


def calculate_mrr(output: list[str], expected: list[str]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR) for a single query.

    MRR measures ranking quality by finding the highest-ranked relevant result
    and returning the reciprocal of its position (1/rank).

    Args:
        output: Ranked list of retrieved items (first item = rank 1)
        expected: List of relevant/ground truth items

    Returns:
        float: MRR score between 0.0 and 1.0 (higher is better)

    Example:
        output = ["doc_a", "doc_b", "doc_c"]    # doc_b is relevant at position 2
        expected = ["doc_b", "doc_d"]
        mrr = calculate_mrr(output, expected)   # Returns 0.5 (1/2)
    """
    if not output or not expected:
        return 0.0

    # Find the highest-ranked (smallest index) relevant item
    best_rank = float("inf")
    for relevant_item in expected:
        if relevant_item in output:
            rank = output.index(relevant_item) + 1  # Convert to 1-based ranking
            best_rank = min(best_rank, rank)

    # Return reciprocal rank of the best result, or 0 if no relevant items found
    return 1.0 / best_rank if best_rank != float("inf") else 0.0


def calculate_recall(output: list[str], expected: list[str]) -> float:
    """
    Calculate recall (completeness) for retrieved results.

    Recall measures what proportion of all relevant items were successfully retrieved.
    High recall means you found most/all of the relevant information.

    Args:
        output: List of retrieved items
        expected: List of all relevant/ground truth items

    Returns:
        float: Recall score between 0.0 and 1.0 (higher is better)

    Raises:
        ZeroDivisionError: If expected list is empty (no ground truth to evaluate against)

    Example:
        output = ["doc_a", "doc_b", "doc_x"]     # Retrieved 3 items
        expected = ["doc_a", "doc_b", "doc_c"]   # 3 relevant items total
        recall = calculate_recall(output, expected)  # Returns 0.67 (found 2 of 3)
    """
    if not expected:
        raise ZeroDivisionError(
            "Cannot calculate recall with empty ground truth (expected list)"
        )

    if not output:
        return 0.0

    # Count how many relevant items were retrieved
    relevant_retrieved = len([item for item in expected if item in output])

    # Calculate proportion of relevant items that were found
    return relevant_retrieved / len(expected)


def calculate_precision(output: list[str], expected: list[str]) -> float:
    """
    Calculate precision (relevance quality) for retrieved results.

    Precision measures what proportion of retrieved items are actually relevant.
    High precision means you retrieved mostly relevant information with little noise.

    Args:
        output: List of retrieved items (total number retrieved)
        expected: List of relevant/ground truth items

    Returns:
        float: Precision score between 0.0 and 1.0 (higher is better)

    Example:
        output = ["doc_a", "doc_b", "doc_x", "doc_y"]  # Retrieved 4 items
        expected = ["doc_a", "doc_b", "doc_c"]         # doc_a, doc_b are relevant
        precision = calculate_precision(output, expected)  # Returns 0.5 (2 relevant of 4 retrieved)
    """
    if not output:
        return 0.0  # No items retrieved means 0 precision

    if not expected:
        return 0.0  # No ground truth means all retrieved items are irrelevant

    # Count how many retrieved items are actually relevant
    relevant_retrieved = len([item for item in output if item in expected])

    # Calculate proportion of retrieved items that are relevant
    return relevant_retrieved / len(output)
