# What This Does

Implements chunking strategies to split cleaned transcripts into retrievable segments, currently featuring a fixed-size chunking approach with timestamp preservation for accurate citation.

# File Structure

```
├── fixed_chunks/                    # Fixed-size chunking implementation
│   ├── generate_chunks.py          # Main chunking script using LangChain
│   ├── chunks/                     # Output directory for chunk JSONs
│   │   ├── [title]_chunks.json    # Individual transcript chunks
│   │   └── all_chunks_combined.json # All chunks merged for database loading
│   └── chunk_verify/              # Chunk validation tools
│       ├── verify_chunk_timings.py # Validates timestamp accuracy
│       ├── simple_timing_verification.py # Quick timing checks
│       ├── detailed_timing_analysis.py # Deep timing analysis
│       └── timing_verification_report.md # Timing analysis results
└── nuggestisation/                 # Placeholder for future nugget-based chunking
```

# Quick Start

- Entry point: `fixed_chunks/generate_chunks.py`
- Run: `uv run python 2_chunks/fixed_chunks/generate_chunks.py`
- Verify: `uv run python 2_chunks/fixed_chunks/chunk_verify/verify_chunk_timings.py`

# How It Works

The fixed-size chunker uses LangChain's RecursiveCharacterTextSplitter with 3000 char chunks and 1500 char overlap. It maintains accurate timestamps by interpolating based on character positions, ensuring each chunk knows its exact time range in the original video.

# Interfaces

```python
# Core data structures
@dataclass
class Chunk:
    chunk_id: str         # Unique identifier
    text: str            # Chunk content
    title: str           # Source transcript title
    cue_start: float     # Start time in seconds
    cue_end: float       # End time in seconds
    chunk_index: int     # Position in transcript
    total_chunks: int    # Total chunks from transcript

# Output format (JSON)
{
    "chunks": [Chunk, ...],
    "metadata": {
        "title": str,
        "total_chunks": int,
        "chunking_params": {...}
    }
}
```

# Dependencies

**Code Dependencies:**
- LangChain for text splitting algorithms
- pandas for CSV processing
- Uses custom TimestampAwareTextSplitter wrapper

**Data Dependencies:**
- Reads from: `/1_transcripts/raw/` - CSV transcript files
- Writes to: `/fixed_chunks/chunks/` - JSON chunk files

**Cross-Directory Usage:**
- Output used by: `/3_database/` - for embedding generation
- Output used by: `/4_labelled_dataset/` - for dataset creation
- Provides: Retrievable chunks with accurate timestamps

# Key Patterns

- Fixed-size chunking (3000 chars, 1500 overlap)
- Timestamp interpolation based on character positions
- Unique chunk IDs: `{title_slug}_{index}`
- Combines all chunks into single JSON for batch processing

# Common Tasks

- Generate chunks: Run generate_chunks.py (processes all CSVs)
- Verify timing: Run verification scripts in chunk_verify/
- Adjust chunk size: Modify CHUNK_SIZE and CHUNK_OVERLAP constants

# Recent Updates

- Switched from character-based to sentence-based chunking (d94ae40)
- Added comprehensive timing verification suite
- Created combined chunks file for easier database loading

# Watch Out For

- Timestamp accuracy depends on even text distribution assumption
- Large overlap (50%) increases storage but improves retrieval
- Chunk IDs must remain stable for evaluation consistency
- Verification scripts validate timing accuracy