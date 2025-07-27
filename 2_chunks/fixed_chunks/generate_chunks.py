"""
Generate fixed-size chunks from raw transcript CSV files using LangChain's RecursiveCharacterTextSplitter.

This implements the FIXED-SIZE CHUNKING STRATEGY:
- Uses RecursiveCharacterTextSplitter with chunk_size=3000, chunk_overlap=1500
- Splits text based on text while trying to maintain semantic boundaries
- Maintains accurate cue_start/cue_end times for each chunk through interpolation
- Outputs JSON files with chunk metadata

This script:
1. Reads transcript CSVs and creates chunks with accurate timestamp mapping
2. Uses RecursiveCharacterTextSplitter with fixed size parameters
3. Maintains accurate cue_start/cue_end times for each chunk
4. Outputs JSON files with chunk metadata
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class TranscriptSegment:
    """Represents a single transcript segment with timing information."""
    text: str
    cue_start: float
    cue_end: float
    speaker: Optional[str] = None
    
    
@dataclass
class Chunk:
    """Represents a processed chunk with metadata."""
    chunk_id: str
    text: str
    title: str
    cue_start: float
    cue_end: float
    chunk_index: int
    total_chunks: int


class TimestampAwareTextSplitter:
    """
    Custom wrapper around RecursiveCharacterTextSplitter that maintains timestamp information when splitting text.
    """
    
    def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 1500):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
    def split_with_timestamps(
        self, 
        segments: List[TranscriptSegment], 
        title: str
    ) -> List[Chunk]:
        """
        Split transcript segments into chunks while maintaining timestamp accuracy.
        
        Args:
            segments: List of transcript segments with timestamps
            title: Title of the transcript
            
        Returns:
            List of chunks with accurate timestamp information
        """
        # Build full text and character-to-timestamp mapping
        full_text = ""
        char_to_time = []  # List of (char_index, timestamp) tuples
        
        for segment in segments:
            start_char = len(full_text)
            full_text += segment.text + " "  # Add space between segments
            end_char = len(full_text)
            
            # Map character positions to timestamps
            # We'll interpolate linearly within each segment
            segment_length = end_char - start_char
            for i in range(segment_length):
                # Calculate interpolated timestamp
                progress = i / max(segment_length - 1, 1)
                timestamp = segment.cue_start + progress * (segment.cue_end - segment.cue_start)
                char_to_time.append((start_char + i, timestamp))
        
        # Split text into chunks
        text_chunks = self.splitter.split_text(full_text)
        
        # Find timestamps for each chunk
        chunks = []
        current_pos = 0
        
        for idx, chunk_text in enumerate(text_chunks):
            # Find where this chunk starts in the original text
            chunk_start_pos = full_text.find(chunk_text, current_pos)
            if chunk_start_pos == -1:
                # If exact match not found, try to find overlap
                # This can happen due to the chunk_overlap parameter
                chunk_start_pos = self._find_chunk_position(full_text, chunk_text, current_pos)
            
            chunk_end_pos = chunk_start_pos + len(chunk_text)
            
            # Get timestamps for chunk boundaries
            chunk_start_time = self._get_timestamp_at_position(char_to_time, chunk_start_pos)
            chunk_end_time = self._get_timestamp_at_position(char_to_time, chunk_end_pos - 1)
            
            # Create chunk object with rounded timestamps (3 decimal places)
            chunk = Chunk(
                chunk_id=f"{self._sanitize_title(title)}_chunk_{idx + 1}",
                text=chunk_text.strip(),
                title=title,
                cue_start=round(chunk_start_time, 3),
                cue_end=round(chunk_end_time, 3),
                chunk_index=idx + 1,
                total_chunks=len(text_chunks)
            )
            chunks.append(chunk)
            
            # Update position for next search
            current_pos = chunk_start_pos + 1
        
        return chunks
    
    def _find_chunk_position(self, full_text: str, chunk_text: str, start_pos: int) -> int:
        """Find the position of a chunk considering potential overlap."""
        # Try to find a substantial portion of the chunk
        min_match_length = min(50, len(chunk_text) // 2)
        for i in range(len(chunk_text) - min_match_length):
            substring = chunk_text[i:i + min_match_length]
            pos = full_text.find(substring, start_pos)
            if pos != -1:
                return pos - i
        # If still not found, return the current position
        return start_pos
    
    def _get_timestamp_at_position(self, char_to_time: List[Tuple[int, float]], pos: int) -> float:
        """Get the timestamp corresponding to a character position."""
        if not char_to_time:
            return 0.0
        
        # Find the closest timestamp
        for i, (char_pos, timestamp) in enumerate(char_to_time):
            if char_pos >= pos:
                return timestamp
        
        # If position is beyond the last character, return the last timestamp
        return char_to_time[-1][1]
    
    def _sanitize_title(self, title: str) -> str:
        """Convert title to a valid identifier."""
        # Replace spaces and special characters with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', title)
        # Remove leading/trailing underscores and limit length
        return sanitized.strip('_')[:100]


def process_transcript_csv(csv_path: Path) -> Dict[str, List[TranscriptSegment]]:
    """
    Read a transcript CSV and convert to TranscriptSegment objects grouped by title.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Dictionary mapping titles to lists of TranscriptSegment objects
    """
    df = pd.read_csv(csv_path)
    
    grouped_transcripts = {}
    for title in df['title'].unique():
        title_df = df[df['title'] == title].copy()
        title_df = title_df.sort_values('cue_start')
        
        segments = []
        for _, row in title_df.iterrows():
            segment = TranscriptSegment(
                text=row['text'].strip(),
                cue_start=row['cue_start'],
                cue_end=row['cue_end'],
                speaker=row.get('vimeo_generated_speaker')
            )
            segments.append(segment)
        
        grouped_transcripts[title] = segments
    
    return grouped_transcripts


def save_chunks_to_json(chunks: List[Chunk], output_path: Path):
    """Save chunks to a JSON file."""
    # Convert dataclass objects to dictionaries
    chunks_dict = [asdict(chunk) for chunk in chunks]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks_dict, f, indent=2, ensure_ascii=False)


def main():
    """Process all CSV files and generate chunks."""
    # Setup directories
    raw_dir = Path(__file__).parent.parent.parent / "1_transcripts" / "raw"
    output_dir = Path(__file__).parent / "chunks"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize splitter
    splitter = TimestampAwareTextSplitter(chunk_size=3000, chunk_overlap=1500)
    
    # Process each CSV file
    csv_files = list(raw_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in the raw/ directory.")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process.")
    print(f"Using chunk_size=3000, chunk_overlap=1500")
    
    total_chunks = 0
    all_chunks = []  # Collect all chunks for a combined output
    
    for csv_file in csv_files:
        print(f"\nProcessing: {csv_file.name}")
        
        try:
            # Process the CSV file
            grouped_transcripts = process_transcript_csv(csv_file)
            
            # Process each transcript
            for title, segments in grouped_transcripts.items():
                print(f"  - Chunking: {title}")
                
                # Generate chunks with timestamps
                chunks = splitter.split_with_timestamps(segments, title)
                
                # Save individual transcript chunks
                safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
                safe_title = safe_title.strip()[:200]
                output_path = output_dir / f"{safe_title}_chunks.json"
                save_chunks_to_json(chunks, output_path)
                
                print(f"    Created {len(chunks)} chunks -> {output_path.name}")
                total_chunks += len(chunks)
                all_chunks.extend(chunks)
                
        except Exception as e:
            print(f"  - Error processing {csv_file.name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Save all chunks to a combined file
    if all_chunks:
        combined_output = output_dir / "all_chunks_combined.json"
        save_chunks_to_json(all_chunks, combined_output)
        print(f"\nCreated combined chunks file: {combined_output.name}")
    
    print(f"\nProcessing complete! Generated {total_chunks} total chunks in {output_dir}")


if __name__ == "__main__":
    main()