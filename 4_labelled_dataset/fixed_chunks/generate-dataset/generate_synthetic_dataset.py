#!/usr/bin/env python3
"""
Generate synthetic dataset for RAG evaluation using LangChain.

This script processes transcript chunks and generates synthetic queries with insights
and chunk references, formatted for Arize Phoenix evaluation.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from tqdm import tqdm

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SyntheticQuery(BaseModel):
    """Structure for a synthetic practical query."""
    query: str = Field(description="The synthetic practical/application query that a user might ask")
    difficulty: str = Field(description="Difficulty level: easy, medium, or hard")
    expected_answer: str = Field(description="The expected comprehensive answer to the query")
    chunk_ids: List[int] = Field(description="IDs of chunks containing relevant information")


class SyntheticDataset(BaseModel):
    """Structure for multiple synthetic queries."""
    queries: List[SyntheticQuery] = Field(description="List of synthetic queries")


class SyntheticDatasetGenerator:
    """Generate synthetic queries from transcript chunks for RAG evaluation."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.7):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.query_generator = self._create_query_generator()
        
    def _create_query_generator(self):
        """Create a chain for generating synthetic queries from chunks."""
        
        prompt = ChatPromptTemplate.from_template("""
You are an expert at creating synthetic practical/application queries for evaluating RAG systems on video transcripts.

Given ALL the transcript chunks from a video about "{title}", generate ONLY practical/application queries that require synthesis and provide actionable insights.

These queries should:
- Require combining information from multiple chunks
- Focus on actionable advice and practical recommendations  
- Test the system's ability to extract insights, not just facts
- Be questions that users would ask to get practical guidance they can apply

Examples of practical queries:
- "How should I prepare my company for an IPO from an equity perspective?"
- "What's the best way to prompt ChatGPT for legal research?"
- "How can legal departments drive D&I initiatives?"
- "What strategies should I use when negotiating with AI vendors?"

TRANSCRIPT CHUNKS:
{chunks_text}

Generate exactly {num_queries} practical/application queries. For each query:
1. Create a natural practical question a user might ask to get actionable advice
2. Identify which specific chunk IDs contain relevant information (just the numeric IDs)
3. Provide the expected comprehensive answer that synthesizes information across chunks

{format_instructions}
""")
        
        output_parser = JsonOutputParser(pydantic_object=SyntheticDataset)
        
        chain = prompt | self.llm | output_parser
        
        return chain, output_parser
    
    def generate_queries_for_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        title: str,
        num_queries: int = 10
    ) -> List[SyntheticQuery]:
        """Generate synthetic queries for a set of chunks."""
        
        # Prepare chunks text with IDs - include all chunks
        chunks_text = "\n\n".join([
            f"[Chunk ID: {chunk['id']}]\n{chunk['text']}"
            for chunk in chunks
        ])
        
        chain, parser = self.query_generator
        
        try:
            result = chain.invoke({
                "title": title,
                "chunks_text": chunks_text,
                "num_queries": num_queries,
                "format_instructions": parser.get_format_instructions()
            })
            
            # Convert dict results to SyntheticQuery objects
            queries = []
            for query_dict in result['queries']:
                queries.append(SyntheticQuery(**query_dict))
            
            return queries
            
        except Exception as e:
            logger.error(f"Error generating queries: {e}")
            return []
    
    def process_all_chunks(
        self, 
        chunks_file: Path,
        num_queries: int = 40
    ) -> List[Dict[str, Any]]:
        """Process all chunks at once and generate synthetic dataset."""
        
        # Load chunks
        with open(chunks_file, 'r') as f:
            all_chunks = json.load(f)
        
        logger.info(f"Loaded {len(all_chunks)} chunks")
        
        # Get unique titles (should be just one based on the data)
        titles = list(set(chunk.get('title', 'Unknown') for chunk in all_chunks))
        
        all_queries = []
        
        # Process all chunks at once for each title
        for title in titles:
            logger.info(f"Processing all chunks for: {title}")
            
            # Get all chunks for this title
            title_chunks = [chunk for chunk in all_chunks if chunk.get('title') == title]
            logger.info(f"Found {len(title_chunks)} chunks for this title")
            
            # Generate all queries in one shot
            queries = self.generate_queries_for_chunks(
                title_chunks, 
                title,
                num_queries=num_queries
            )
            
            # Add to results
            for query in queries:
                all_queries.append({
                    'title': title,
                    'query': query.query,
                    'query_type': 'practical',  # All queries are practical type
                    'difficulty': query.difficulty,
                    'chunk_ids': query.chunk_ids,
                    'expected_answer': query.expected_answer,
                    'timestamp': datetime.now().isoformat()
                })
        
        return all_queries
    
    def format_for_phoenix(self, queries: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> pd.DataFrame:
        """Format the synthetic dataset for Arize Phoenix evaluation."""
        
        # Create chunk lookup
        chunk_lookup = {chunk['id']: chunk for chunk in chunks}
        
        phoenix_data = []
        
        for query_data in queries:
            # Get the actual chunk texts
            contexts = []
            for chunk_id in query_data['chunk_ids']:
                if chunk_id in chunk_lookup:
                    contexts.append(chunk_lookup[chunk_id]['text'])
            
            # Create Phoenix-compatible record
            phoenix_record = {
                'question': query_data['query'],
                'answer': query_data['expected_answer'],  # This would be replaced by actual RAG output
                'contexts': contexts,
                'ground_truth': query_data['expected_answer'],
                # Additional metadata
                'query_type': query_data['query_type'],
                'difficulty': query_data['difficulty'],
                'title': query_data['title'],
                'chunk_ids': json.dumps(query_data['chunk_ids']),
                'timestamp': query_data['timestamp']
            }
            
            phoenix_data.append(phoenix_record)
        
        return pd.DataFrame(phoenix_data)


def main():
    """Main execution function."""
    
    # Paths
    base_dir = Path(__file__).parent
    chunks_file = base_dir.parent / "retrieve-chunks" / "raw_chunks_from_db.json"
    output_dir = base_dir
    
    # Initialize generator
    generator = SyntheticDatasetGenerator()
    
    # Generate synthetic queries
    logger.info("Generating synthetic queries...")
    synthetic_queries = generator.process_all_chunks(
        chunks_file,
        num_queries=40  # Generate 40 practical queries in one shot
    )
    
    logger.info(f"Generated {len(synthetic_queries)} synthetic queries")
    
    # Save raw synthetic queries
    raw_output = output_dir / "synthetic_queries_raw.json"
    with open(raw_output, 'w') as f:
        json.dump(synthetic_queries, f, indent=2)
    logger.info(f"Saved raw queries to {raw_output}")
    
    # Load chunks for Phoenix formatting
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)
    
    # Format for Phoenix
    phoenix_df = generator.format_for_phoenix(synthetic_queries, chunks)
    
    # Save Phoenix-formatted dataset
    phoenix_csv = output_dir / "synthetic_dataset_phoenix.csv"
    phoenix_df.to_csv(phoenix_csv, index=False)
    logger.info(f"Saved Phoenix dataset to {phoenix_csv}")
    
    # Save as JSON for easier loading
    phoenix_json = output_dir / "synthetic_dataset_phoenix.json"
    phoenix_df.to_json(phoenix_json, orient='records', indent=2)
    logger.info(f"Saved Phoenix JSON to {phoenix_json}")
    
    # Print summary statistics
    print("\n=== Dataset Summary ===")
    print(f"Total queries: {len(synthetic_queries)}")
    print(f"Query types distribution:")
    query_types = pd.Series([q['query_type'] for q in synthetic_queries]).value_counts()
    for qtype, count in query_types.items():
        print(f"  {qtype}: {count} ({count/len(synthetic_queries)*100:.1f}%)")
    print(f"\nDifficulty distribution:")
    difficulties = pd.Series([q['difficulty'] for q in synthetic_queries]).value_counts()
    for diff, count in difficulties.items():
        print(f"  {diff}: {count} ({count/len(synthetic_queries)*100:.1f}%)")


if __name__ == "__main__":
    main()