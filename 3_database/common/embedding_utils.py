"""
Utilities for generating OpenAI embeddings with retry logic and batch processing.
Handles rate limits with exponential backoff and provides cost estimation.
"""

import os
import time
from typing import List, Optional, Tuple
import tiktoken
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

class EmbeddingGenerator:
    def __init__(self, model: str = "text-embedding-3-large", dimensions: int = 1024):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.dimensions = dimensions
        self.encoding = tiktoken.encoding_for_model("text-embedding-3-large")
        self.max_tokens_per_request = 8192
        self.batch_size = 100
        self.cost_per_million_tokens = 0.13
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string using tiktoken."""
        return len(self.encoding.encode(text))
    
    def estimate_cost(self, texts: List[str]) -> Tuple[int, float]:
        """Estimate the total tokens and cost for embedding a list of texts."""
        total_tokens = sum(self.count_tokens(text) for text in texts)
        cost = (total_tokens / 1_000_000) * self.cost_per_million_tokens
        return total_tokens, cost
    
    def create_embeddings_with_retry(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """
        Create embeddings for a batch of texts with retry logic for rate limits.
        Implements exponential backoff: 5, 10, 20 seconds.
        """
        retry_delays = [5, 10, 20]
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimensions
                )
                return [data.embedding for data in response.data]
                
            except Exception as e:
                error_message = str(e)
                if "rate_limit_exceeded" in error_message or "429" in error_message:
                    if attempt < max_retries:
                        delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                        print(f"Rate limit hit. Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                raise e
                
        raise Exception(f"Failed to create embeddings after {max_retries} retries")
    
    def process_batches(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """
        Process texts in batches to generate embeddings efficiently.
        Default batch size is 100 for optimal throughput.
        """
        if batch_size is None:
            batch_size = self.batch_size
            
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"Processing {len(texts)} texts in {total_batches} batches...")
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.create_embeddings_with_retry(batch)
            embeddings.extend(batch_embeddings)
            
        return embeddings
    
    def validate_texts(self, texts: List[str]) -> List[Tuple[int, int]]:
        """
        Validate texts and return indices of texts that exceed token limits.
        Returns list of tuples (index, token_count) for texts that are too long.
        """
        issues = []
        for i, text in enumerate(texts):
            token_count = self.count_tokens(text)
            if token_count > self.max_tokens_per_request:
                issues.append((i, token_count))
        return issues


if __name__ == "__main__":
    # Example usage
    generator = EmbeddingGenerator()
    
    sample_texts = [
        "This is a sample text for embedding generation.",
        "OpenAI's text-embedding-3-large model supports up to 8192 tokens.",
        "We're using 1024 dimensions for optimal performance and storage."
    ]
    
    # Estimate cost
    total_tokens, cost = generator.estimate_cost(sample_texts)
    print(f"Total tokens: {total_tokens}")
    print(f"Estimated cost: ${cost:.6f}")
    
    # Validate texts
    issues = generator.validate_texts(sample_texts)
    if issues:
        print(f"Warning: {len(issues)} texts exceed token limit")
    
    # Generate embeddings
    embeddings = generator.process_batches(sample_texts)
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimensions: {len(embeddings[0])}")