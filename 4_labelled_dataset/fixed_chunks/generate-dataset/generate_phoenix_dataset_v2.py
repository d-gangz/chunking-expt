"""
Generate Phoenix-compatible dataset for fixed chunks evaluation - Version 2.
This version only includes chunks where quotes BEGIN, not all chunks that contain parts of quotes.

Input:
- Base ground truth: 4_labelled_dataset/baseline-questions/base_ground_truth.json
- Fixed chunks from DB: 4_labelled_dataset/fixed_chunks/retrieve-chunks/raw_chunks_from_db.json

Output:
- Phoenix dataset: 4_labelled_dataset/fixed_chunks/generate-dataset/phoenix_dataset_fixed_chunks_v2.json
"""

import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize text for comparison by removing extra whitespace and punctuation."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Convert to lowercase for comparison
    text = text.lower()
    return text


def find_quote_start_chunks(quoted_text: str, chunks: List[Dict], transcript_title: str, min_start_words: int = 10) -> List[int]:
    """
    Find chunks where the quote BEGINS (not just contains).
    
    Returns list of chunk IDs where the quote starts.
    """
    matches = []
    
    # Normalize transcript title for comparison (remove colons, extra spaces)
    normalized_title = transcript_title.lower().replace(':', '').replace('  ', ' ').strip()
    
    # Get the beginning of the quote for matching
    quoted_normalized = normalize_text(quoted_text)
    quote_words = quoted_normalized.split()
    
    if len(quote_words) < min_start_words:
        min_start_words = len(quote_words)
    
    # Create search pattern from beginning of quote
    search_start = ' '.join(quote_words[:min_start_words])
    
    for chunk in chunks:
        # Normalize chunk title for comparison
        chunk_title = chunk.get('title', '').lower().replace(':', '').replace('  ', ' ').strip()
        
        # Match transcript title (with flexible matching)
        if normalized_title in chunk_title or chunk_title in normalized_title:
            chunk_normalized = normalize_text(chunk.get('text', ''))
            
            # Check if chunk contains the beginning of the quote
            if search_start in chunk_normalized:
                matches.append(chunk['id'])
    
    return matches


def create_phoenix_dataset_entry(question_entry: Dict, chunk_mappings: List[int]) -> Dict:
    """
    Create a Phoenix-compatible dataset entry.
    
    Phoenix expects:
    - input: The query/question text
    - expected: Array of chunk IDs that should be retrieved
    - metadata: Dictionary containing additional information
    """
    return {
        "input": question_entry["question"],
        "expected": chunk_mappings,  # Array of chunk IDs that should be retrieved
        "metadata": {
            "question_id": question_entry["question_id"],
            "difficulty": question_entry.get("difficulty", "medium"),
            "comprehensive_answer": question_entry["comprehensive_answer"],
            "source_quotes": question_entry.get("source_quotes", []),
            "source_quotes_count": len(question_entry.get("source_quotes", []))
        }
    }


def generate_phoenix_dataset():
    """Generate Phoenix-compatible dataset for fixed chunks."""
    
    # Define paths
    base_dir = Path("/Users/gang/suite-work/chunking-expt/4_labelled_dataset")
    base_ground_truth_path = base_dir / "baseline-questions" / "base_ground_truth.json"
    fixed_chunks_path = base_dir / "fixed_chunks" / "retrieve-chunks" / "raw_chunks_from_db.json"
    output_path = base_dir / "fixed_chunks" / "generate-dataset" / "phoenix_dataset_fixed_chunks_v2.json"
    
    # Load data
    print("Loading base ground truth dataset...")
    with open(base_ground_truth_path, 'r') as f:
        base_data = json.load(f)
    
    print("Loading fixed chunks from database...")
    with open(fixed_chunks_path, 'r') as f:
        fixed_chunks = json.load(f)
    
    print(f"Loaded {len(base_data['entries'])} questions and {len(fixed_chunks)} chunks")
    
    # Process each question entry
    phoenix_dataset = []
    mapping_stats = {
        "total_questions": 0,
        "questions_with_mappings": 0,
        "total_chunks_mapped": 0,
        "questions_without_mappings": []
    }
    
    for entry in base_data['entries']:
        mapping_stats["total_questions"] += 1
        
        # Collect all relevant chunk IDs for this question
        all_chunk_ids = set()
        chunk_details = []  # For debugging
        
        # Process each source quote
        for quote in entry.get('source_quotes', []):
            quoted_text = quote['quoted_text']
            transcript_title = quote['transcript_title']
            
            # Find chunks where this quote STARTS
            matches = find_quote_start_chunks(
                quoted_text, 
                fixed_chunks, 
                transcript_title
            )
            
            # Add chunk IDs to the set
            for chunk_id in matches:
                all_chunk_ids.add(chunk_id)
                chunk_details.append({
                    "chunk_id": chunk_id,
                    "quote_preview": quoted_text[:100] + "..."
                })
        
        # Convert to sorted list for consistency
        chunk_ids_list = sorted(list(all_chunk_ids))
        
        if chunk_ids_list:
            mapping_stats["questions_with_mappings"] += 1
            mapping_stats["total_chunks_mapped"] += len(chunk_ids_list)
            
            # Create Phoenix dataset entry
            phoenix_entry = create_phoenix_dataset_entry(entry, chunk_ids_list)
            
            # Add debugging information to metadata
            phoenix_entry["metadata"]["_debug"] = {
                "chunk_details": chunk_details,
                "total_chunks_mapped": len(chunk_ids_list)
            }
            
            phoenix_dataset.append(phoenix_entry)
        else:
            mapping_stats["questions_without_mappings"].append(entry["question_id"])
    
    # Prepare final output
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "chunking_method": "fixed_chunks",
            "matching_strategy": "quote_start_only",
            "total_entries": len(phoenix_dataset),
            "mapping_stats": mapping_stats,
            "phoenix_format": {
                "description": "Phoenix-compatible retrieval evaluation dataset (v2 - quote starts only)",
                "structure": {
                    "input": "The question/query text",
                    "expected": "Array of chunk IDs where quotes BEGIN",
                    "metadata": {
                        "question_id": "Unique identifier for the question",
                        "difficulty": "Question difficulty level",
                        "comprehensive_answer": "Complete answer text",
                        "source_quotes": "Array of source quotes with transcript titles",
                        "source_quotes_count": "Number of source quotes"
                    }
                }
            }
        },
        "data": phoenix_dataset
    }
    
    # Save the dataset
    print(f"\nSaving Phoenix dataset to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("\n=== Dataset Generation Summary ===")
    print(f"Total questions processed: {mapping_stats['total_questions']}")
    print(f"Questions with chunk mappings: {mapping_stats['questions_with_mappings']}")
    print(f"Total chunks mapped: {mapping_stats['total_chunks_mapped']}")
    print(f"Average chunks per question: {mapping_stats['total_chunks_mapped'] / mapping_stats['questions_with_mappings']:.2f}")
    
    if mapping_stats["questions_without_mappings"]:
        print(f"\nWarning: {len(mapping_stats['questions_without_mappings'])} questions had no chunk mappings:")
        for q_id in mapping_stats["questions_without_mappings"][:5]:
            print(f"  - {q_id}")
        if len(mapping_stats["questions_without_mappings"]) > 5:
            print(f"  ... and {len(mapping_stats['questions_without_mappings']) - 5} more")
    
    print(f"\nDataset saved to: {output_path}")
    
    # Create a simplified version for direct Phoenix upload
    simplified_path = base_dir / "fixed_chunks" / "generate-dataset" / "phoenix_dataset_simplified_v2.json"
    
    # Create cleaned entries without debug info and extra fields
    simplified_data = []
    for entry in phoenix_dataset:
        simplified_entry = {
            "input": entry["input"],
            "expected": entry["expected"],
            "metadata": {
                "question_id": entry["metadata"]["question_id"],
                "difficulty": entry["metadata"]["difficulty"],
                "comprehensive_answer": entry["metadata"]["comprehensive_answer"],
                "source_quotes": entry["metadata"]["source_quotes"]
            }
        }
        simplified_data.append(simplified_entry)
    
    with open(simplified_path, 'w') as f:
        json.dump(simplified_data, f, indent=2)
    
    print(f"Simplified dataset saved to: {simplified_path}")


if __name__ == "__main__":
    generate_phoenix_dataset()