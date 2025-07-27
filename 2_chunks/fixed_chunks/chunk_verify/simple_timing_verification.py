"""
Simple Timing Verification Script

This script performs a basic verification of chunk timing accuracy by comparing 
the text content and timestamps between processed chunks and raw transcripts.
It checks the first few chunks of each video and reports timing offsets.

Usage:
    python simple_timing_verification.py

The script will:
1. Load chunks from JSON files
2. Load corresponding raw transcripts from CSV files
3. Compare text at reported timestamps
4. Search for chunk text within ±30 second windows
5. Report timing offsets for each chunk
"""

import json
import pandas as pd
from pathlib import Path

def load_chunks(chunk_file):
    """Load chunks from JSON file"""
    with open(chunk_file, 'r') as f:
        return json.load(f)

def load_transcript(csv_file):
    """Load transcript from CSV file"""
    df = pd.read_csv(csv_file)
    return df

def get_transcript_text_in_range(transcript_df, start_time, end_time):
    """Get all transcript text within a time range"""
    rows_in_range = transcript_df[
        (transcript_df['cue_start'] >= start_time - 0.5) & 
        (transcript_df['cue_end'] <= end_time + 0.5)
    ]
    return ' '.join(rows_in_range['text'].tolist())

def simple_timing_check(chunk_file, transcript_file):
    """Simple check of timing accuracy by comparing text at boundaries"""
    chunks = load_chunks(chunk_file)
    transcript_df = load_transcript(transcript_file)
    
    video_name = Path(chunk_file).stem.replace('_chunks', '')
    print(f"\nSimple Timing Verification for: {video_name[:60]}...")
    print("="*80)
    
    # Check first few chunks
    for chunk in chunks[:3]:
        print(f"\nChunk {chunk['chunk_index']}:")
        print(f"Chunk timing: {chunk['cue_start']:.1f}s - {chunk['cue_end']:.1f}s")
        
        # Get first 50 chars of chunk
        chunk_start = ' '.join(chunk['text'].split()[:10])
        print(f"Chunk starts with: \"{chunk_start}...\"")
        
        # Show what's actually in transcript at that time
        print(f"\nTranscript content at chunk start time ({chunk['cue_start']:.1f}s):")
        start_rows = transcript_df[
            (transcript_df['cue_start'] >= chunk['cue_start'] - 2) & 
            (transcript_df['cue_start'] <= chunk['cue_start'] + 2)
        ]
        
        if len(start_rows) > 0:
            for _, row in start_rows.head(3).iterrows():
                print(f"  [{row['cue_start']:.1f}s] {row['text']}")
        
        # Check if we can find the chunk text anywhere nearby
        print(f"\nSearching for chunk text in nearby transcript rows...")
        search_window = transcript_df[
            (transcript_df['cue_start'] >= chunk['cue_start'] - 30) & 
            (transcript_df['cue_start'] <= chunk['cue_start'] + 30)
        ]
        
        # Build continuous text from search window
        if len(search_window) > 0:
            found = False
            for i in range(len(search_window) - 5):
                continuous_text = ' '.join(search_window.iloc[i:i+5]['text'].tolist())
                if chunk_start.lower() in continuous_text.lower():
                    actual_time = search_window.iloc[i]['cue_start']
                    offset = chunk['cue_start'] - actual_time
                    print(f"  ✓ Found at {actual_time:.1f}s (offset: {offset:+.1f}s)")
                    found = True
                    break
            
            if not found:
                print(f"  ✗ Not found in ±30s window")
        
        print("-" * 80)

# Run simple verification
file_mappings = [
    {
        'chunk_file': '/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/Laying the Groundwork - Employee _ Early Shareholder Equity Best Practices _Louisa Daniels_ Recursion_ Jeff Le Sage_ Liquid Stock__chunks.json',
        'transcript_file': '/Users/gang/suite-work/chunking-expt/1_transcripts/raw/export (15).csv',
        'name': 'Laying the Groundwork'
    },
    {
        'chunk_file': '/Users/gang/suite-work/chunking-expt/2_chunks/fixed_chunks/chunks/Prompting with Precision_ Leveraging AI Responsibly as In-House Counsel_chunks.json',
        'transcript_file': '/Users/gang/suite-work/chunking-expt/1_transcripts/raw/export (14).csv',
        'name': 'Prompting with Precision'
    }
]

for mapping in file_mappings:
    try:
        simple_timing_check(mapping['chunk_file'], mapping['transcript_file'])
    except Exception as e:
        print(f"\nError processing {mapping['name']}: {e}")

print("\n" + "="*80)
print("SUMMARY:")
print("The chunk timings appear to have systematic offsets from the raw transcript.")
print("This could be due to:")
print("1. Different processing/alignment methods used during chunking")
print("2. Overlapping text between chunks (chunks may include context from adjacent segments)")
print("3. Post-processing adjustments made to improve chunk coherence")