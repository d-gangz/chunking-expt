"""
Process raw transcript CSV files into clean text-only Markdown files without timestamps.

This script:
1. Reads CSV transcript files from the raw/ folder
2. Groups rows by title (same title = same transcript)
3. Concatenates text in chronological order without timestamps
4. Outputs formatted .md files with title, duration, and speaker information at the top
5. Saves cleaned transcripts to cleaned-full/ folder

Input: Reads CSV files from 1_transcripts/raw/
Output: Saves cleaned transcripts to 1_transcripts/cleaned-full/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List


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
    """Convert seconds to readable timestamp format (HH:MM:SS)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def create_markdown_transcript(title: str, segments: List[Dict]) -> str:
    """
    Create a formatted markdown transcript without timestamps.
    
    Args:
        title: The transcript title
        segments: List of transcript segments with timestamps and text
        
    Returns:
        Formatted markdown string
    """
    lines = [f"# {title}\n"]
    
    # Add metadata
    total_duration = segments[-1]['cue_end']
    lines.append(f"**Total Duration:** {format_timestamp(total_duration)}\n")
    
    # Check if there are speakers and list them
    speakers = [seg.get('vimeo_generated_speaker', '') for seg in segments]
    # Filter out nan values and empty strings
    valid_speakers = []
    for s in speakers:
        if pd.notna(s) and str(s) != '' and str(s) != 'nan':
            valid_speakers.append(str(s))
    
    unique_speakers = sorted(set(valid_speakers))
    
    if unique_speakers:
        has_speakers = True
        lines.append(f"**Speakers:** {', '.join(f'Speaker {s}' for s in unique_speakers)}\n")
    else:
        has_speakers = False
    
    lines.append("\n---\n")
    
    # Process segments - concatenate text by speaker
    if has_speakers:
        current_speaker = None
        speaker_text = []
        
        for segment in segments:
            speaker = segment.get('vimeo_generated_speaker', '')
            text = segment['text'].strip()
            
            # Treat nan values as no speaker
            if pd.isna(speaker) or str(speaker) == 'nan' or str(speaker) == '':
                speaker = ''
            else:
                speaker = str(speaker)
            
            # If speaker changes, output accumulated text
            if speaker != current_speaker:
                if current_speaker is not None and speaker_text:
                    lines.append(f"\n**[Speaker {current_speaker}]**\n")
                    lines.append(' '.join(speaker_text))
                    lines.append("")
                
                current_speaker = speaker
                speaker_text = [text]
            else:
                speaker_text.append(text)
        
        # Don't forget the last speaker's text
        if current_speaker is not None and speaker_text:
            lines.append(f"\n**[Speaker {current_speaker}]**\n")
            lines.append(' '.join(speaker_text))
    else:
        # No speakers, just concatenate all text
        all_text = ' '.join(segment['text'].strip() for segment in segments)
        lines.append(all_text)
    
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
    cleaned_dir = Path(__file__).parent / "cleaned-full"
    
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