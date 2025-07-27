"""
Verify Chunk Timings Script

This script verifies the timing accuracy of processed chunks against raw transcripts
by comparing both text content and timestamp alignment. It provides detailed analysis
of timing differences and generates accuracy metrics.

Usage:
    python verify_chunk_timings.py

The script will:
1. Load chunk JSON files and corresponding transcript CSV files
2. Find text matches in transcripts for chunk content
3. Calculate timing differences for start and end timestamps
4. Generate accuracy statistics and summaries
5. Identify chunks with significant timing discrepancies
"""

import json
import csv
import pandas as pd
from pathlib import Path
import re

def load_chunks(chunk_file):
    """Load chunks from JSON file"""
    with open(chunk_file, 'r') as f:
        return json.load(f)

def load_transcript(csv_file):
    """Load transcript from CSV file"""
    df = pd.read_csv(csv_file)
    return df

def find_text_in_transcript(transcript_df, search_text, window_size=50):
    """Find text in transcript and return matching rows with timing"""
    search_text = search_text[:window_size].strip()
    
    # Combine consecutive transcript rows to search across boundaries
    combined_texts = []
    for i in range(len(transcript_df)):
        combined = ""
        for j in range(i, min(i+10, len(transcript_df))):
            combined += " " + transcript_df.iloc[j]['text']
        combined_texts.append((i, combined.strip()))
    
    # Search for the text
    matches = []
    for idx, combined in combined_texts:
        if search_text.lower() in combined.lower():
            matches.append({
                'row_idx': idx,
                'cue_start': transcript_df.iloc[idx]['cue_start'],
                'cue_end': transcript_df.iloc[min(idx+9, len(transcript_df)-1)]['cue_end'],
                'text_preview': combined[:200]
            })
    
    return matches

def verify_chunk_timings(chunk_file, transcript_file):
    """Verify the timing accuracy of chunks against raw transcript"""
    chunks = load_chunks(chunk_file)
    transcript_df = load_transcript(transcript_file)
    
    print(f"\nVerifying: {Path(chunk_file).name}")
    print(f"Against transcript: {Path(transcript_file).name}")
    print("="*80)
    
    results = []
    
    for i, chunk in enumerate(chunks[:5]):  # Check first 5 chunks
        print(f"\nChunk {chunk['chunk_index']}:")
        print(f"  Chunk timing: {chunk['cue_start']:.3f} - {chunk['cue_end']:.3f}")
        
        # Get start and end text snippets
        chunk_text_start = chunk['text'][:100].strip()
        chunk_text_end = chunk['text'][-100:].strip()
        
        # Find start text in transcript
        start_matches = find_text_in_transcript(transcript_df, chunk_text_start)
        
        # Find rows within chunk time range
        time_range_rows = transcript_df[
            (transcript_df['cue_start'] >= chunk['cue_start'] - 5) & 
            (transcript_df['cue_start'] <= chunk['cue_start'] + 5)
        ]
        
        if len(start_matches) > 0:
            best_match = start_matches[0]
            timing_diff = abs(best_match['cue_start'] - chunk['cue_start'])
            print(f"  Start text found at: {best_match['cue_start']:.3f}")
            print(f"  Timing difference: {timing_diff:.3f}s")
            
            # Check end timing
            end_time_rows = transcript_df[
                (transcript_df['cue_end'] >= chunk['cue_end'] - 5) & 
                (transcript_df['cue_end'] <= chunk['cue_end'] + 5)
            ]
            
            if len(end_time_rows) > 0:
                actual_end = end_time_rows.iloc[-1]['cue_end']
                end_diff = abs(actual_end - chunk['cue_end'])
                print(f"  End timing difference: {end_diff:.3f}s")
                
                results.append({
                    'chunk_index': chunk['chunk_index'],
                    'start_diff': timing_diff,
                    'end_diff': end_diff,
                    'accurate': timing_diff < 1.0 and end_diff < 1.0
                })
            else:
                print(f"  Could not verify end timing")
        else:
            print(f"  WARNING: Could not find chunk start text in transcript!")
            
        # Show transcript text at chunk start time
        print(f"\n  Transcript at chunk start time ({chunk['cue_start']}s):")
        if len(time_range_rows) > 0:
            for _, row in time_range_rows.head(3).iterrows():
                print(f"    [{row['cue_start']:.1f}-{row['cue_end']:.1f}] {row['text']}")
    
    # Summary
    if results:
        accurate_chunks = sum(1 for r in results if r['accurate'])
        avg_start_diff = sum(r['start_diff'] for r in results) / len(results)
        avg_end_diff = sum(r['end_diff'] for r in results) / len(results)
        
        print(f"\n{'='*80}")
        print(f"SUMMARY:")
        print(f"  Chunks verified: {len(results)}")
        print(f"  Accurate chunks (< 1s difference): {accurate_chunks}/{len(results)}")
        print(f"  Average start timing difference: {avg_start_diff:.3f}s")
        print(f"  Average end timing difference: {avg_end_diff:.3f}s")
    
    return results

# Define file mappings
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

# Run verification
for mapping in file_mappings:
    try:
        verify_chunk_timings(mapping['chunk_file'], mapping['transcript_file'])
    except Exception as e:
        print(f"\nError processing {mapping['chunk_file']}: {e}")