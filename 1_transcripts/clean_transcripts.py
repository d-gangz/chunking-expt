"""
Process raw transcript CSV files into clean, readable Markdown files.

This script:
1. Reads CSV transcript files from the raw/ folder
2. Groups rows by title (same title = same transcript)
3. Concatenates text in chronological order
4. Outputs formatted .md files with timestamps and speaker information
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple


def process_transcript_csv(csv_path: Path) -> Dict[str, List[Dict]]:
    """
    Read a transcript CSV and group rows by title.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary mapping titles to lists of transcript segments
    """
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file {csv_path} is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Failed to parse CSV {csv_path}: {str(e)}")
    
    # Validate required columns
    required_columns = ['title', 'text', 'cue_start', 'cue_end']
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"CSV missing required columns: {missing_columns}")
    
    # Validate data types
    if not pd.api.types.is_numeric_dtype(df['cue_start']):
        raise ValueError("cue_start column must be numeric")
    if not pd.api.types.is_numeric_dtype(df['cue_end']):
        raise ValueError("cue_end column must be numeric")
    
    # Validate that we have data
    if df.empty:
        raise ValueError(f"CSV file {csv_path} contains no data rows")
    
    # Group by title
    grouped_transcripts = {}
    for title in df['title'].unique():
        title_df = df[df['title'] == title].copy()
        # Sort by cue_start to ensure chronological order
        title_df = title_df.sort_values('cue_start')
        
        # Convert to list of dictionaries for easier processing
        segments = title_df.to_dict('records')
        grouped_transcripts[title] = segments
    
    return grouped_transcripts


def format_timestamp(seconds: float) -> str:
    """Convert seconds to readable timestamp format (MM:SS)."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_raw_timestamp(seconds: float) -> str:
    """Return the raw timestamp value as string, preserving original format."""
    # Convert to string while preserving the exact decimal representation
    # This avoids any floating point conversion issues
    return f"{seconds:g}"


def create_markdown_transcript(title: str, segments: List[Dict]) -> str:
    """
    Create a formatted markdown transcript from segments.
    
    Args:
        title: The transcript title
        segments: List of transcript segments with timestamps and text
        
    Returns:
        Formatted markdown string
    """
    lines = [f"# {title}\n"]
    lines.append(f"**Total Duration:** {format_timestamp(segments[-1]['cue_end'])}\n")
    lines.append(f"**Number of Segments:** {len(segments)}\n")
    
    # Check if there are speakers
    has_speakers = any(seg.get('vimeo_generated_speaker') for seg in segments)
    if has_speakers:
        unique_speakers = set(seg.get('vimeo_generated_speaker', '') for seg in segments)
        unique_speakers.discard('')  # Remove empty strings
        lines.append(f"**Speakers:** {len(unique_speakers)}\n")
    
    lines.append("\n---\n")
    
    # Process segments
    current_speaker = None
    for segment in segments:
        speaker = segment.get('vimeo_generated_speaker', '')
        text = segment['text'].strip()
        start_time = format_timestamp(segment['cue_start'])
        end_time = format_timestamp(segment['cue_end'])
        
        # Add speaker change indicator if applicable
        if has_speakers and speaker != current_speaker:
            current_speaker = speaker
            lines.append(f"\n**[Speaker {speaker}]**\n")
        
        # Add timestamp and text with raw seconds format
        raw_start = format_raw_timestamp(segment['cue_start'])
        raw_end = format_raw_timestamp(segment['cue_end'])
        lines.append(f"\n[{raw_start} - {raw_end}] {text}")
    
    return '\n'.join(lines)


def clean_filename(title: str) -> str:
    """Clean title to create a valid filename."""
    # Remove path traversal attempts first
    title = title.replace('..', '_')
    title = title.replace('/', '_')
    title = title.replace('\\', '_')
    
    # Remove or replace invalid filename characters
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    
    # Remove control characters
    title = ''.join(char for char in title if ord(char) >= 32)
    
    # Limit length and remove trailing dots/spaces
    title = title[:200].strip('. ')
    
    # Ensure non-empty filename
    if not title:
        title = "untitled"
    
    return title


def main():
    """Process all CSV files in the raw folder."""
    raw_dir = Path(__file__).parent / "raw"
    cleaned_dir = Path(__file__).parent / "cleaned"
    
    # Create cleaned directory if it doesn't exist
    cleaned_dir.mkdir(exist_ok=True)
    
    # Process each CSV file
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in the raw/ directory.")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process.")
    
    total_transcripts = 0
    
    for csv_file in csv_files:
        print(f"\nProcessing: {csv_file.name}")
        
        try:
            # Process the CSV file
            grouped_transcripts = process_transcript_csv(csv_file)
            
            # Create markdown file for each unique transcript
            for title, segments in grouped_transcripts.items():
                # Create clean filename
                clean_title = clean_filename(title)
                output_path = cleaned_dir / f"{clean_title}.md"
                
                # Generate markdown content
                markdown_content = create_markdown_transcript(title, segments)
                
                # Write to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                print(f"  - Created: {output_path.name}")
                total_transcripts += 1
                
        except Exception as e:
            print(f"  - Error processing {csv_file.name}: {str(e)}")
    
    print(f"\nProcessing complete! Created {total_transcripts} transcript(s) in {cleaned_dir}")


if __name__ == "__main__":
    main()