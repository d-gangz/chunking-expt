"""
Detailed Timing Analysis Script

This script performs an in-depth analysis of timing patterns between processed chunks 
and raw transcripts. It uses text matching algorithms to find exact positions of chunk 
content in the original transcripts and calculates timing offset statistics.

Usage:
    python detailed_timing_analysis.py

The script will:
1. Load chunks and transcripts for multiple videos
2. Use word-level matching to find chunk text in transcripts
3. Calculate timing offsets for each chunk
4. Provide statistical analysis of timing consistency
5. Generate recommendations for timing corrections
"""

import json
import csv
import pandas as pd
import numpy as np
from pathlib import Path

def load_chunks(chunk_file):
    """Load chunks from JSON file"""
    with open(chunk_file, 'r') as f:
        return json.load(f)

def load_transcript(csv_file):
    """Load transcript from CSV file"""
    df = pd.read_csv(csv_file)
    return df

def find_exact_text_match(transcript_df, search_text, tolerance=0.8):
    """Find exact text match in transcript by building continuous text"""
    # Clean search text
    search_words = search_text.lower().split()[:20]  # First 20 words
    
    best_match = None
    best_score = 0
    
    for i in range(len(transcript_df) - 10):
        # Build continuous text from multiple rows
        continuous_text = ""
        row_indices = []
        
        for j in range(i, min(i + 20, len(transcript_df))):
            continuous_text += " " + transcript_df.iloc[j]['text']
            row_indices.append(j)
            
            # Check if we have enough words
            continuous_words = continuous_text.lower().split()
            
            if len(continuous_words) >= len(search_words):
                # Calculate match score
                matches = 0
                for k, word in enumerate(search_words):
                    if k < len(continuous_words) and word == continuous_words[k]:
                        matches += 1
                
                score = matches / len(search_words)
                
                if score > best_score and score >= tolerance:
                    best_score = score
                    best_match = {
                        'start_idx': i,
                        'start_time': transcript_df.iloc[i]['cue_start'],
                        'end_time': transcript_df.iloc[j]['cue_end'],
                        'score': score,
                        'matched_text': ' '.join(continuous_words[:len(search_words)])
                    }
    
    return best_match

def analyze_timing_patterns(chunk_file, transcript_file):
    """Analyze timing patterns between chunks and transcripts"""
    chunks = load_chunks(chunk_file)
    transcript_df = load_transcript(transcript_file)
    
    video_name = Path(chunk_file).stem.replace('_chunks', '')
    print(f"\nDetailed Timing Analysis for: {video_name}")
    print("="*100)
    
    timing_data = []
    
    # Analyze each chunk
    for chunk in chunks[:10]:  # Analyze first 10 chunks
        print(f"\nChunk {chunk['chunk_index']}:")
        print(f"  Reported timing: {chunk['cue_start']:.3f} - {chunk['cue_end']:.3f} (duration: {chunk['cue_end'] - chunk['cue_start']:.3f}s)")
        
        # Find the actual position of chunk text
        chunk_start_text = ' '.join(chunk['text'].split()[:30])
        match = find_exact_text_match(transcript_df, chunk_start_text)
        
        if match:
            time_offset = chunk['cue_start'] - match['start_time']
            print(f"  Actual timing: {match['start_time']:.3f}s (match score: {match['score']:.2f})")
            print(f"  Time offset: {time_offset:+.3f}s")
            print(f"  First words matched: \"{' '.join(chunk_start_text.split()[:10])}...\"")
            
            timing_data.append({
                'chunk_index': chunk['chunk_index'],
                'reported_start': chunk['cue_start'],
                'actual_start': match['start_time'],
                'offset': time_offset,
                'match_score': match['score']
            })
        else:
            print(f"  WARNING: Could not find matching text in transcript!")
    
    # Calculate statistics
    if timing_data:
        offsets = [t['offset'] for t in timing_data]
        print(f"\n{'='*100}")
        print("TIMING OFFSET STATISTICS:")
        print(f"  Average offset: {np.mean(offsets):+.3f}s")
        print(f"  Median offset: {np.median(offsets):+.3f}s")
        print(f"  Std deviation: {np.std(offsets):.3f}s")
        print(f"  Min offset: {np.min(offsets):+.3f}s")
        print(f"  Max offset: {np.max(offsets):+.3f}s")
        
        # Check if offset is consistent
        if np.std(offsets) < 5:
            print(f"\n  ✓ Offset appears CONSISTENT across chunks")
            print(f"    Suggested correction: subtract {abs(np.mean(offsets)):.3f}s from all chunk timestamps")
        else:
            print(f"\n  ✗ Offset is INCONSISTENT across chunks")
            print(f"    Individual chunk timing verification needed")
    
    return timing_data

# Run detailed analysis
file_mappings = [
    {
        'chunk_file': '/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/Laying the Groundwork - Employee _ Early Shareholder Equity Best Practices _Louisa Daniels_ Recursion_ Jeff Le Sage_ Liquid Stock__chunks.json',
        'transcript_file': '/Users/gang/suite-work/chunking-expt/1_transcripts/raw/export (15).csv'
    },
    {
        'chunk_file': '/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/Prompting with Precision_ Leveraging AI Responsibly as In-House Counsel_chunks.json',
        'transcript_file': '/Users/gang/suite-work/chunking-expt/1_transcripts/raw/export (14).csv'
    }
]

all_results = {}
for mapping in file_mappings:
    try:
        video_name = Path(mapping['chunk_file']).stem.replace('_chunks', '')
        results = analyze_timing_patterns(mapping['chunk_file'], mapping['transcript_file'])
        all_results[video_name] = results
    except Exception as e:
        print(f"\nError: {e}")

# Create summary report
print("\n" + "="*100)
print("FINAL SUMMARY REPORT")
print("="*100)

for video_name, timing_data in all_results.items():
    if timing_data:
        offsets = [t['offset'] for t in timing_data]
        print(f"\n{video_name}:")
        print(f"  Average timing offset: {np.mean(offsets):+.3f} seconds")
        print(f"  Consistency: {'GOOD' if np.std(offsets) < 5 else 'POOR'} (std: {np.std(offsets):.3f}s)")
        print(f"  Recommendation: {'Apply uniform correction' if np.std(offsets) < 5 else 'Review individual chunks'}")