# What This Does

Processes raw CSV transcript files into clean, readable Markdown formats - both with timestamps and text-only versions for different downstream processing needs.

# File Structure

```
├── raw/                              # Input CSV transcript files
│   ├── export (14).csv              # Raw transcript export
│   └── export (15).csv              # Raw transcript export
├── cleaned-timestamp/               # Output with timestamp formatting
│   └── [title].md                   # Cleaned transcripts with seconds timestamps
├── cleaned-full/                    # Output without timestamps
│   └── [title].md                   # Text-only transcripts with metadata header
├── clean_transcripts.py             # Generates timestamped transcripts
└── clean_transcripts_no_timestamp.py # Generates text-only transcripts
```

# Quick Start

- Entry point: Choose script based on output needs
- Run timestamped: `uv run python 1_transcripts/clean_transcripts.py`
- Run text-only: `uv run python 1_transcripts/clean_transcripts_no_timestamp.py`
- Output locations: `cleaned-timestamp/` or `cleaned-full/`

# How It Works

Both scripts read CSV files containing transcript segments, group them by title, sort by timestamp, and output formatted Markdown. The timestamp version preserves timing info in seconds format, while the text-only version creates continuous prose with metadata headers for cleaner chunking.

# Interfaces

```python
# Core processing function in both scripts
process_transcript_csv(csv_path: Path) -> Dict[str, List[Dict]]

# Required CSV columns:
- title: Video/transcript title
- text: Transcript segment text  
- cue_start: Start time in seconds
- cue_end: End time in seconds
- speaker (optional): Speaker name
```

# Dependencies

**Code Dependencies:**
- Uses pandas for CSV processing
- Uses pathlib for file operations

**Data Dependencies:**
- Reads from: `/raw/` - CSV transcript exports
- Writes to: `/cleaned-timestamp/` or `/cleaned-full/` - Markdown files

**Cross-Directory Usage:**
- Output used by: `/2_chunks/` - as input for chunking algorithms
- Provides: Clean transcript text for downstream processing

# Key Patterns

- Groups CSV rows by title to handle multi-segment transcripts
- Sorts segments by cue_start for chronological order
- Validates required columns and data types
- Handles speaker information when available

# Common Tasks

- Add new transcript: Place CSV in `raw/` and run either script
- Change output format: Modify markdown generation in script
- Process single file: Scripts process ALL CSVs in `raw/`

# Recent Updates

- Added timestamp-free cleaning for baseline evaluation (56a7386)
- Switched from MM:SS to raw seconds format (33f2127)
- Enhanced validation and error handling

# Watch Out For

- CSV must have required columns: title, text, cue_start, cue_end
- Numeric cue_start/cue_end values required
- Empty CSVs will raise errors
- Both scripts process ALL files in raw/ directory