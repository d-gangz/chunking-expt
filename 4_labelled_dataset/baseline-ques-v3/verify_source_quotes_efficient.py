"""
Enhanced verification script to check if all source quotes from insights.json exist in Jake's data.json.
Features advanced ellipsis handling, clean chunk extraction, and multiple search strategies.

Input data sources: 4_labelled_dataset/insights.json, 1_transcripts/jake/data.json
Output destinations: Console output and verification report
Dependencies: json, re (for text cleaning and ellipsis handling)
Key exports: verify_quotes(), generate_report(), extract_clean_chunks()
Side effects: Prints detailed verification report with debug info for problem quotes
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class QuoteMatch:
    """Represents the result of matching a source quote."""
    insight_id: str
    transcript_title: str
    quoted_text: str
    found: bool
    match_type: str  # "exact", "partial", "not_found"
    confidence: str  # "high", "medium", "low"


def clean_text_for_matching(text: str) -> str:
    """Clean text by removing extra whitespace and normalizing punctuation."""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Normalize common punctuation variations
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('–', '-').replace('—', '-')
    
    return text


def extract_clean_chunks(quote: str) -> List[str]:
    """
    Extract clean searchable chunks from a quote, handling ellipsis properly.
    Returns list of clean text chunks without ellipsis.
    """
    quote = clean_text_for_matching(quote)
    
    # Handle leading ellipsis - remove and get content after (both Unicode … and ASCII ...)
    if quote.startswith('…'):
        quote = quote[1:].strip()
    elif quote.startswith('...'):
        quote = quote[3:].strip()
    
    # Split by ellipsis to get clean chunks (handle both types)
    chunks = re.split(r'[\.]{3,}|…', quote)
    clean_chunks = []
    
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk.split()) >= 5:  # Only keep chunks with at least 5 words
            clean_chunks.append(chunk)
    
    return clean_chunks


def get_search_phrases(quote: str) -> List[Tuple[str, str]]:
    """
    Generate search phrases from quote with different strategies.
    Returns list of (phrase, strategy_name) tuples.
    """
    phrases = []
    clean_chunks = extract_clean_chunks(quote)
    
    # Strategy 1: First 10-20 words from each clean chunk
    for chunk in clean_chunks:
        words = chunk.split()
        if len(words) >= 10:
            # First 10 words
            phrase_10 = ' '.join(words[:10])
            phrases.append((phrase_10, "first_10_words"))
            
            # First 15 words if available
            if len(words) >= 15:
                phrase_15 = ' '.join(words[:15])
                phrases.append((phrase_15, "first_15_words"))
                
            # First 20 words if available
            if len(words) >= 20:
                phrase_20 = ' '.join(words[:20])
                phrases.append((phrase_20, "first_20_words"))
    
    # Strategy 2: Complete clean chunks (without ellipsis)
    for chunk in clean_chunks:
        if 20 <= len(chunk) <= 200:  # Reasonable length chunks
            phrases.append((chunk, "clean_chunk"))
    
    # Strategy 3: Middle portions of longer chunks
    for chunk in clean_chunks:
        words = chunk.split()
        if len(words) >= 20:
            # Middle 15 words
            start_idx = len(words) // 4
            middle_phrase = ' '.join(words[start_idx:start_idx+15])
            phrases.append((middle_phrase, "middle_portion"))
    
    return phrases


def find_best_match(quote: str, transcript: str) -> Tuple[bool, str, str]:
    """
    Find the best match for a quote in transcript using efficient string matching.
    Enhanced with ellipsis handling and chunk-based searching.
    Returns (found, match_type, confidence).
    """
    quote_clean = clean_text_for_matching(quote).lower()
    transcript_clean = clean_text_for_matching(transcript).lower()
    
    # 1. Try exact match (fastest)
    if quote_clean in transcript_clean:
        return True, "exact", "high"
    
    # 2. Try without ellipsis and common variations (handle both Unicode … and ASCII ...)
    quote_no_ellipsis = re.sub(r'[\.]{3,}|…', '', quote_clean)
    quote_no_ellipsis = re.sub(r'\s+', ' ', quote_no_ellipsis.strip())
    
    if len(quote_no_ellipsis) > 20 and quote_no_ellipsis in transcript_clean:
        return True, "partial", "high"
    
    # 3. NEW: Enhanced ellipsis handling with clean chunks
    search_phrases = get_search_phrases(quote)
    for phrase, strategy in search_phrases:
        phrase_clean = phrase.lower()
        if phrase_clean in transcript_clean:
            # Determine confidence based on phrase length and strategy
            if strategy in ["first_20_words", "clean_chunk"] and len(phrase) > 50:
                return True, "partial", "high"
            elif strategy in ["first_15_words", "middle_portion"] and len(phrase) > 30:
                return True, "partial", "medium"
            elif len(phrase) > 20:
                return True, "partial", "medium"
    
    # 4. For longer quotes, try finding significant portions
    if len(quote_clean) > 100:
        # Split quote into sentences and try to find most of them
        sentences = [s.strip() for s in quote_clean.split('.') if len(s.strip()) > 10]
        found_sentences = 0
        
        for sentence in sentences:
            # Clean sentence of ellipsis for better matching (both types)
            sentence_clean = re.sub(r'[\.]{3,}|…', '', sentence).strip()
            if len(sentence_clean) > 10 and sentence_clean in transcript_clean:
                found_sentences += 1
        
        if found_sentences >= len(sentences) * 0.7:  # 70% of sentences found
            return True, "partial", "medium"
    
    # 5. Try finding key phrases (for shorter quotes)
    if 20 <= len(quote_clean) <= 100:
        # Split into meaningful chunks
        words = quote_clean.split()
        if len(words) >= 5:
            # Try to find consecutive 5-word phrases
            for i in range(len(words) - 4):
                phrase = ' '.join(words[i:i+5])
                # Skip phrases that are just ellipsis
                if '...' not in phrase and phrase in transcript_clean:
                    return True, "partial", "medium"
    
    # 6. Last resort: check for very distinctive phrases
    # Look for quoted speech or very specific terms
    distinctive_patterns = re.findall(r'"[^"]{10,}"', quote_clean)
    for pattern in distinctive_patterns:
        if pattern in transcript_clean:
            return True, "partial", "low"
    
    return False, "not_found", "low"


def extract_source_quotes(insights_path: Path) -> List[Tuple[str, str, str]]:
    """Extract all source quotes from insights.json."""
    with open(insights_path, 'r', encoding='utf-8') as f:
        insights_data = json.load(f)
    
    quotes = []
    for insight in insights_data['insights']:
        insight_id = insight['insight_id']
        for quote in insight['source_quotes']:
            quotes.append((
                insight_id,
                quote['transcript_title'],
                quote['quoted_text']
            ))
    
    return quotes


def load_transcript_data(data_path: Path) -> Dict[str, str]:
    """Load transcript data from Jake's data.json."""
    print("📚 Loading transcript data...")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data['transcripts'])} transcripts")
    return data['transcripts']


def map_transcript_titles(source_title: str, available_transcripts: Dict[str, str]) -> str:
    """Map source title to available transcript title."""
    # Clean the source title
    clean_source = source_title.replace("TRANSCRIPT ", "").split(": ", 1)[-1].strip()
    
    # Try exact match first
    for title in available_transcripts.keys():
        if clean_source.lower() == title.lower():
            return title
    
    # Try partial matches
    for title in available_transcripts.keys():
        if clean_source.lower() in title.lower() or title.lower() in clean_source.lower():
            return title
    
    return None


def verify_quotes(insights_path: Path, data_path: Path, debug_mode: bool = False) -> List[QuoteMatch]:
    """Verify all source quotes exist in transcript data."""
    print("🔍 Starting enhanced source quote verification...")
    
    # Load data
    source_quotes = extract_source_quotes(insights_path)
    transcript_data = load_transcript_data(data_path)
    
    print(f"📊 Analyzing {len(source_quotes)} source quotes across {len(transcript_data)} transcripts")
    if debug_mode:
        print("🐞 Debug mode enabled - showing detailed analysis")
    print("=" * 60)
    
    results = []
    previously_failed = ["insight_004", "insight_018", "insight_029", "insight_030"]
    
    for i, (insight_id, transcript_title, quoted_text) in enumerate(source_quotes, 1):
        is_debug_target = insight_id in previously_failed or debug_mode
        
        if is_debug_target:
            print(f"\n[{i:2d}/{len(source_quotes)}] 🔍 DETAILED ANALYSIS: {insight_id}")
            print(f"Quote preview: \"{quoted_text[:100]}{'...' if len(quoted_text) > 100 else ''}\"")
        else:
            print(f"[{i:2d}/{len(source_quotes)}] {insight_id}...", end=" ")
        
        # Map transcript title
        mapped_title = map_transcript_titles(transcript_title, transcript_data)
        
        if not mapped_title:
            print("❌ Transcript not found")
            results.append(QuoteMatch(
                insight_id=insight_id,
                transcript_title=transcript_title,
                quoted_text=quoted_text[:100] + "..." if len(quoted_text) > 100 else quoted_text,
                found=False,
                match_type="transcript_not_found",
                confidence="low"
            ))
            continue
        
        if is_debug_target:
            print(f"Mapped to transcript: \"{mapped_title}\"")
            
            # Show what clean chunks we're extracting
            clean_chunks = extract_clean_chunks(quoted_text)
            print(f"Clean chunks extracted: {len(clean_chunks)}")
            for j, chunk in enumerate(clean_chunks, 1):
                print(f"  Chunk {j}: \"{chunk[:80]}{'...' if len(chunk) > 80 else ''}\"")
            
            # Show search phrases we'll try
            search_phrases = get_search_phrases(quoted_text)
            print(f"Search phrases generated: {len(search_phrases)}")
            for phrase, strategy in search_phrases[:3]:  # Show first 3
                print(f"  {strategy}: \"{phrase[:60]}{'...' if len(phrase) > 60 else ''}\"")
        
        # Search for quote in transcript
        transcript_text = transcript_data[mapped_title]
        found, match_type, confidence = find_best_match(quoted_text, transcript_text)
        
        # Print result
        if found:
            if match_type == "exact":
                status = "✅ Exact match"
            else:
                status = f"⚠️  {match_type.title()} match ({confidence} confidence)"
            
            if is_debug_target:
                print(f"🎉 SUCCESS: {status}")
            else:
                print(status)
        else:
            if is_debug_target:
                print("🚨 FAILED: Still not found after enhanced matching")
                # Show a sample of the transcript for debugging
                print(f"Transcript sample: \"{transcript_text[:200]}...\"")
            else:
                print("❌ Not found")
        
        results.append(QuoteMatch(
            insight_id=insight_id,
            transcript_title=mapped_title,
            quoted_text=quoted_text[:100] + "..." if len(quoted_text) > 100 else quoted_text,
            found=found,
            match_type=match_type,
            confidence=confidence
        ))
    
    return results


def generate_report(results: List[QuoteMatch]) -> None:
    """Generate a comprehensive verification report."""
    print("\n" + "=" * 80)
    print("📋 SOURCE QUOTE VERIFICATION REPORT")
    print("=" * 80)
    
    # Summary statistics
    total_quotes = len(results)
    exact_matches = sum(1 for r in results if r.match_type == "exact")
    partial_matches = sum(1 for r in results if r.match_type == "partial")
    not_found = sum(1 for r in results if r.match_type == "not_found")
    transcript_not_found = sum(1 for r in results if r.match_type == "transcript_not_found")
    
    found_quotes = exact_matches + partial_matches
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total source quotes analyzed: {total_quotes}")
    print(f"  ✅ Exact matches: {exact_matches} ({exact_matches/total_quotes*100:.1f}%)")
    print(f"  ⚠️  Partial matches: {partial_matches} ({partial_matches/total_quotes*100:.1f}%)")
    print(f"  ❌ Not found in transcript: {not_found} ({not_found/total_quotes*100:.1f}%)")
    print(f"  📚 Transcript not available: {transcript_not_found}")
    
    success_rate = found_quotes / total_quotes * 100
    print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1f}% ({found_quotes}/{total_quotes})")
    
    # Confidence breakdown for partial matches
    if partial_matches > 0:
        high_conf = sum(1 for r in results if r.match_type == "partial" and r.confidence == "high")
        med_conf = sum(1 for r in results if r.match_type == "partial" and r.confidence == "medium")
        low_conf = sum(1 for r in results if r.match_type == "partial" and r.confidence == "low")
        
        print(f"\n⚠️  PARTIAL MATCH CONFIDENCE BREAKDOWN:")
        print(f"  🔴 High confidence: {high_conf}")
        print(f"  🟡 Medium confidence: {med_conf}") 
        print(f"  🟠 Low confidence: {low_conf}")
    
    # Detailed issues
    if not_found > 0:
        print(f"\n❌ QUOTES NOT FOUND ({not_found}):")
        not_found_results = [r for r in results if r.match_type == "not_found"]
        for result in not_found_results:
            print(f"  • {result.insight_id}")
            print(f"    \"{result.quoted_text}\"")
            print()
    
    if transcript_not_found > 0:
        print(f"\n📚 TRANSCRIPTS NOT AVAILABLE ({transcript_not_found}):")
        missing_transcripts = [r for r in results if r.match_type == "transcript_not_found"]
        for result in missing_transcripts:
            print(f"  • {result.insight_id}: {result.transcript_title}")
    
    # Overall assessment
    print("\n💡 ASSESSMENT:")
    if success_rate >= 95:
        print("  🎉 EXCELLENT: Almost all source quotes verified successfully!")
    elif success_rate >= 85:
        print("  👍 GOOD: Most source quotes are verified. Minor gaps present.")
    elif success_rate >= 70:
        print("  ⚠️  FAIR: Majority of quotes found, but significant gaps exist.")
    else:
        print("  🚨 POOR: Major verification issues. Investigation required.")
    
    if exact_matches / total_quotes >= 0.8:
        print("  ✨ High exact match rate indicates excellent data alignment.")
    elif partial_matches > exact_matches:
        print("  🔍 Many partial matches suggest possible formatting differences.")
    
    print()


def main():
    """Main execution function."""
    # Set up paths
    base_path = Path(__file__).parent.parent.parent
    insights_path = base_path / "4_labelled_dataset" / "baseline-ques-v3" / "insights.json"
    data_path = base_path / "1_transcripts" / "jake" / "data.json"
    
    print("🚀 EFFICIENT Source Quote Verification Tool")
    print(f"📖 Insights: {insights_path.name}")
    print(f"📚 Transcripts: {data_path}")
    print()
    
    # Verify files exist
    if not insights_path.exists():
        print(f"❌ Insights file not found: {insights_path}")
        return
    
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        return
    
    # Run verification (enable debug mode for previously failing quotes)
    results = verify_quotes(insights_path, data_path, debug_mode=False)
    
    # Generate report
    generate_report(results)
    
    print("🏁 Verification complete!")


if __name__ == "__main__":
    main()