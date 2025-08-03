# Chunking Strategy Experiment Plan

## Overview

This document outlines the systematic approach for evaluating different chunking strategies to optimize video transcript retrieval for Q&A systems. The goal is to develop a fair comparison framework where each chunking method is evaluated against the same base ground truth dataset.

## Team & Responsibilities

### Gang (Product)

- Generate base ground truth dataset from 5 training transcripts
- Implement different chunking strategies
- Map base ground truth to chunk-strategy-specific labeled datasets
- Run evaluations and analyze results

### Jake (Engineer)

- Set up test databases for each chunking strategy
- Provide API endpoints for chunk retrieval and hybrid search
- Ensure integration with existing Postgres vector database infrastructure

### Jair (ML Engineer) & Mark (Product Manager)

- Review and validate approach
- Provide input on evaluation metrics and business requirements

## General Approach (Repeatable for All Chunk Strategies)

### Step 0: Base Ground Truth Creation (Gang)
Create the foundation dataset that all chunk strategies will be evaluated against:
1. Analyze the 5 training transcripts for cross-transcript insights
2. Generate 30 comprehensive answers with supporting quotes
3. Create 2-3 questions per insight (varying difficulty)
4. Validate all quotes exist verbatim in transcripts

### Step 1: Chunking Strategy Design (Gang + Jair)

1. Conceptualize the chunking strategy approach
2. Define technical requirements and specifications
3. Document chunk size, overlap, and splitting logic for Jake to build the database.

### Step 2: Database Integration (Jake)

For each chunking strategy:

1. Create new table/collection with strategy-specific name
2. Ingest chunks using existing Postgres hybrid search configuration
3. Enable hybrid search (keyword + vector) on the chunks
4. Create API endpoints that will be used for the evals:
   - Endpoint to retrieve all chunks for the 5 training transcripts
   - Endpoint for hybrid search across entire database

### Step 3: Ground Truth Mapping (Gang)

Convert base ground truth to strategy-specific labeled dataset:

1. Use Endpoint 1 to retrieve all chunks for the 5 training transcripts
2. Take quoted text from base ground truth
3. Find matching chunks using 80% text overlap threshold
4. Extract chunk IDs for evaluation
5. Create strategy-specific labeled dataset
6. Validate mapping quality

### Step 4: Evaluation (Gang)

1. Use hybrid search endpoint to retrieve chunks for each query
2. Calculate metrics:
   - MRR@10 (Mean Reciprocal Rank)
   - Recall@10 (Percentage of relevant chunks found)
   - Precision@10 (Percentage of top 10 that are relevant)
3. Analyze results and document findings

## Base Ground Truth Dataset

### Why This Approach?

Creating one base ground truth dataset and mapping it to each chunking strategy ensures:

- **Fair comparison**: All strategies evaluated on identical questions
- **Efficiency**: Avoid manual labeling for each strategy
- **Consistency**: Same insights and quotes used across all evaluations
- **Flexibility**: Handles different chunk boundaries gracefully

### Dataset Structure

- 30 insights with 90 questions from 5 training transcripts
- Each insight contains 2-4 verbatim quotes
- Questions vary by difficulty (easy/medium/hard)
- Cross-transcript connections prioritized

### Training Transcripts

These 5 transcripts are used to create the base ground truth:

1. "Laying the Groundwork - Employee & Early Shareholder Equity Best Practices (Louisa Daniels, Recursion; Jeff Le Sage, Liquid Stock)"
2. "Prompting with Precision: Leveraging AI Responsibly as In-House Counsel"
3. "TechGC Virtual Dinner: Level Up Your Board(Jolie Siegel, C4 Therapeutics; Alan Smith & Kat Duncan, Fenwick)"
4. "The Art of Professionalism: Navigating Ethical Conduct in Legal Practice"
5. "The Role of Legal in Building an Effective Diversity & Inclusion Program (Jill Simeone, Etsy)"

## API Requirements (Jake to Implement)

### Endpoint 1: Retrieve Training Chunks

Retrieve all chunks for the 5 training transcripts only.

**Arguments:**

- `chunk_strategy`: The name of the chunking strategy (e.g., "fixed_chunks", "semantic_chunks", "nuggetization")
  - This determines which database table/collection to query
  - Each strategy has its own set of pre-processed chunks stored

**Request:**

```bash
curl -X POST "https://api.example.com/chunks/training-set" \
  -H "Content-Type: application/json" \
  -d '{
    "chunk_strategy": "fixed_chunks"
  }'
```

**Expected Output Format:**

```json
[
  {
    "id": 1,
    "text": "chunk content...",
    "title": "Original Transcript Title",
    "cue_start": 0.123,
    "cue_end": 45.678,
    "chunk_index": 1,
    "total_chunks": 50
  }
]
```

### Endpoint 2: Hybrid Search

Search across entire transcript database (not just training set).

**Arguments:**

- `query`: The search query text from the user
- `chunk_strategy`: The name of the chunking strategy to search within (e.g., "fixed_chunks", "semantic_chunks")
  - Determines which chunk collection to search
- `num_results`: Number of top results to return (e.g., 10, 20, 30)

**Request:**

```bash
curl -X POST "https://api.example.com/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the risks of using AI in legal work?",
    "chunk_strategy": "fixed_chunks",
    "num_results": 10
  }'
```

**Expected Output Format:**

```json
{
  "results": [
    {
      "id": 123,
      "text": "matching chunk content...",
      "title": "Transcript Title",
      "score": 0.95,
      "rank": 1
      // Note: score and ranking format not finalized. Feel free to decide on best approach.
    }
  ],
  "total_results": 10,
  "query": "What are the risks of using AI in legal work?"
}
```

_Note: Results should be ranked by final score with best matches first._

## Current Lloyd Search Queries

### Key Question for Team

**Who can provide access to current Lloyd chatbot search queries?**

### Proposed Approach

1. **First**: Collect actual Lloyd search queries from production
2. **Then**: Gang recreates base ground truth using these real query patterns
3. **Finally**: Showcase questions to Kiran/Greg, demonstrating they're based on actual Lloyd usage

### Why Real Queries Matter

- Ensures evaluation reflects actual user needs
- Identifies common query patterns and terminology
- Validates that our test questions are realistic
- Improves ground truth dataset relevance

## Chunk Strategy: Fixed Chunks (First Implementation)

### Specifications

- **Strategy Name**: `fixed_chunks`
- **Chunk Size**: 3000 characters
- **Chunk Overlap**: 1500 characters (50% overlap)
- **Implementation**: I've used Langchain's RecursiveCharacterTextSplitter for this.

### Next Steps for Fixed Chunks

1. Jake: Set up database table and implement API endpoints
2. Gang: Validate chunk retrieval via API
3. Gang: Run evaluation using Phoenix framework
4. Team: Review results and iterate

## Future Chunking Strategies

Potential strategies to explore:

- **Semantic Chunking**: Based on topic boundaries
- **Sliding Window**: Different sizes and overlaps
- **Nuggetization**: Fact-based extraction
- **Hierarchical Chunking**: Nested levels of detail

Each will follow the same general approach outlined above.

---

_This plan is a living document. Updates will be made as we learn more about system constraints and requirements._
