# Base Ground Truth Dataset Generation Plan

## Overview

Generate a transcript-agnostic ground truth dataset for evaluating different chunking strategies by analyzing all 5 transcripts and creating questions with comprehensive answers backed by exact quotes.

## Definition of Insight

An insight is a clear, deep, and sometimes sudden understanding of a complicated problem, situation, or the true nature of something. It involves:

- **Penetrating understanding**: Seeing beyond surface details to underlying principles or motivations
- **Pattern recognition**: Identifying connections across different contexts
- **Practical value**: Driving actions or innovations in business and legal contexts
- **Deeper meaning**: Understanding implications beyond just facts

## Dataset Structure

```json
{
    "question_id": "q_001",
    "question": "How does legal expertise intersect with technology adoption in modern corporate governance?",
    "comprehensive_answer": "The intersection reveals a fundamental shift where legal professionals must balance traditional risk management with innovation enablement...",
    "source_quotes": [
        {
            "quoted_text": "Quote from one transcript about legal tech adoption...",
            "transcript_title": "Prompting with Precision: Leveraging AI Responsibly as In-House Counsel"
        },
        {
            "quoted_text": "Quote from another transcript about board governance...",
            "transcript_title": "TechGC Virtual Dinner: Level Up Your Board"
        }
    ],
    "question_type": "synthesis",  # factual, inference, synthesis
    "difficulty": "hard"
}
```

## Implementation Steps

### Step 1: Extract Insights as Comprehensive Answers

```
Analyze these 5 legal/business transcripts:
1. Laying the Groundwork - Employee & Early Shareholder Equity Best Practices
2. Prompting with Precision: Leveraging AI Responsibly as In-House Counsel
3. TechGC Virtual Dinner: Level Up Your Board
4. The Art of Professionalism: Navigating Ethical Conduct in Legal Practice
5. The Role of Legal in Building an Effective Diversity & Inclusion Program

Extract 20-30 INSIGHTS that serve as COMPREHENSIVE ANSWERS:
- Each insight should be a complete, self-contained answer (2-4 sentences)
- Must reveal deep understanding, patterns, or principles
- PRIORITY: Create insights that connect concepts ACROSS DIFFERENT transcripts
- Must be fully supported by quoted text from the transcripts

For each insight/comprehensive answer:
- Write the complete insight as you would answer a question
- Include 2-4 SUBSTANTIAL quotes (50-150 words each, capturing complete thoughts)
- IMPORTANT: Draw quotes from MULTIPLE transcripts whenever possible
- Avoid fragmentary quotes - capture full sentences or complete ideas
- Ensure quotes provide rich context, not just keywords
```

### Step 2: Generate Questions FROM the Comprehensive Answers

```
For each comprehensive answer (insight), generate 2-3 questions that it answers:

The questions should vary by DIFFICULTY (how the user asks):
- Easy: Direct, straightforward phrasing
- Medium: Requires some interpretation or uses business jargon
- Hard: Indirect phrasing, multi-part, or requires inference

Example:
If the comprehensive answer is about "AI bias risks in legal practice"...
- Easy: "What are the risks of using AI in legal work?"
- Medium: "How should in-house counsel approach AI tool validation?"
- Hard: "What parallels exist between algorithmic decision-making challenges and traditional legal precedent biases?"

All three questions should be answerable by the SAME comprehensive answer.
```

### Step 3: Structure and Validate

```
For each entry:
1. The insight IS the comprehensive answer
2. Questions are different ways users might ask for this information
3. Source quotes prove the answer is grounded in the transcripts
4. Difficulty reflects question phrasing complexity, not content complexity
```

## Example Entry - Cross-Transcript Insight About Human-Centered Decision Making

```json
{
  "question_id": "q_001",
  "question": "Why is human judgment still critical when using AI tools?",
  "comprehensive_answer": "Human judgment remains essential when using AI tools because these systems lack true understanding and can produce misleading outputs that appear credible. Just as building human connections and understanding individual circumstances is core to effective business practices, evaluating AI outputs requires human expertise to verify accuracy and consider context that machines cannot grasp. The key is maintaining the ability to falsify and validate outputs rather than blindly trusting automated results.",
  "source_quotes": [
    {
      "quoted_text": "So I think first off, a lot of people are treating these tools as if they're subject matter experts in areas that they don't understand. And I think that's inherently problematic and dangerous. I feel like a broken record, but I keep going to the, you need to be able, you need to be capable of falsifying the output in order for it to be safe for you to rely on the output without bringing in other humans.",
      "transcript_title": "Prompting with Precision: Leveraging AI Responsibly as In-House Counsel"
    },
    {
      "quoted_text": "And so this began a larger process in the company. We came up with a new mission, and we, our new mission is, is to keep commerce human. And what does that really mean? It means that we're a company that's really about human connections. And if anyone's ever bought anything on Etsy, you know, that you're buying from like some quirky Mary Sue in Kansas City, and she's gonna, you know, send it with a little note and maybe a little piece of candy. And that's like a very human thing in today's modern world.",
      "transcript_title": "The Role of Legal in Building an Effective Diversity & Inclusion Program"
    }
  ],
  "question_type": "analysis",
  "difficulty": "easy"
}
```

## Another Example - Early Stage Awareness and Communication

```json
{
  "question_id": "q_002",
  "question": "What challenges do companies face in getting employees to understand complex benefits early?",
  "comprehensive_answer": "A fundamental challenge in corporate benefits communication is that employees often don't engage with complex topics like equity compensation or legal risks until they become immediately relevant, such as approaching an IPO or encountering a specific issue. This delayed awareness creates rushed education scenarios where companies must quickly bring employees up to speed on nuanced topics they've ignored for years. Proactive, ongoing education programs are essential but face the hurdle of capturing attention before urgency forces engagement.",
  "source_quotes": [
    {
      "quoted_text": "Well, I mean one of the things you'll discover most likely is that the vast majority of employees don't even think about their Equity until they get close to IPO or to a liquidity event. And so if you're doing an IPO in a",
      "transcript_title": "Laying the Groundwork - Employee & Early Shareholder Equity Best Practices"
    },
    {
      "quoted_text": "Like we're we're talking about prompting, we're talking about giving context, we're talking about how you get better at asking the right question so you get the right outputs, but in reality there are still some risks. And, um, what do you think is most likely to cause something misleading or to cause a risky output?",
      "transcript_title": "Prompting with Precision: Leveraging AI Responsibly as In-House Counsel"
    }
  ],
  "question_type": "factual",
  "difficulty": "easy"
}
```

## Validation Criteria

- Each insight must reveal deeper understanding, not just summarize facts
- Quotes from multiple transcripts should genuinely support the same insight
- Questions must require understanding the insight, not just recalling information
- Coverage across all 5 transcripts with emphasis on cross-transcript connections

## Next Steps

1. Analyze all 5 transcripts for deep insights and patterns
2. Generate 50-75 ground truth entries with multi-source insights
3. Validate quotes are verbatim from transcripts
4. Create mapping function to match quotes to chunks for any chunking strategy

## Creating Chunking-Method-Specific Ground Truth Datasets

Once the base ground truth dataset is generated, use it to create specific ground truth datasets for each chunking method:

### Mapping Process

```python
def calculate_overlap_percentage(quoted_text, chunk_content):
    """
    Calculate what percentage of the quoted text is present in the chunk
    """
    # Tokenize for more accurate word-level matching
    quoted_words = quoted_text.split()
    found_words = 0

    # Check each word from quoted text
    for word in quoted_words:
        if word in chunk_content:
            found_words += 1

    return (found_words / len(quoted_words)) * 100 if quoted_words else 0

def map_quotes_to_chunks(base_ground_truth, chunking_method_chunks, threshold=80):
    """
    Maps quoted text from base ground truth to chunk IDs for any chunking method

    Args:
        base_ground_truth: The base dataset with questions and quoted text
        chunking_method_chunks: Chunks from a specific chunking strategy
        threshold: Minimum percentage of quoted text that must be in chunk (default 80%)

    Returns:
        Ground truth dataset with chunk IDs specific to this chunking method
    """
    method_ground_truth = []

    for entry in base_ground_truth:
        mapped_entry = entry.copy()
        mapped_entry['relevant_chunk_ids'] = []
        mapped_entry['chunk_mappings'] = []  # For debugging/validation

        for quote in entry['source_quotes']:
            quoted_text = quote['quoted_text']
            transcript_title = quote['transcript_title']

            # Find chunks with sufficient overlap
            for chunk in chunking_method_chunks:
                if chunk['transcript_title'] == transcript_title:
                    overlap_pct = calculate_overlap_percentage(quoted_text, chunk['content'])

                    if overlap_pct >= threshold:
                        mapped_entry['relevant_chunk_ids'].append(chunk['chunk_id'])
                        mapped_entry['chunk_mappings'].append({
                            'chunk_id': chunk['chunk_id'],
                            'overlap_percentage': overlap_pct,
                            'quoted_text': quoted_text[:50] + '...'  # Preview
                        })

        # Remove duplicates
        mapped_entry['relevant_chunk_ids'] = list(set(mapped_entry['relevant_chunk_ids']))
        method_ground_truth.append(mapped_entry)

    return method_ground_truth
```

### Usage Example

```python
# Load base ground truth
base_ground_truth = load_json('base_ground_truth.json')

# For each chunking method
for method_name in ['fixed_size', 'semantic', 'topic_based', 'sliding_window']:
    # Load chunks for this method
    chunks = load_chunks(f'{method_name}_chunks.json')

    # Create method-specific ground truth
    method_ground_truth = map_quotes_to_chunks(
        base_ground_truth,
        chunks,
        threshold=80  # Require 80% overlap
    )

    # Save method-specific ground truth
    save_json(f'{method_name}_ground_truth.json', method_ground_truth)
```

### Key Benefits

1. **Fair Comparison**: All chunking methods are evaluated on the same questions and insights
2. **Flexible Matching**: The overlap threshold handles cases where quotes span chunk boundaries
3. **Validation Support**: The `chunk_mappings` field helps debug and validate the mapping quality
4. **Edge Case Handling**: Works when quotes are split across multiple chunks

### Threshold Guidelines

- **80-100%**: Strict matching for high-precision evaluation
- **60-80%**: Balanced matching allowing for some chunk boundary effects
- **40-60%**: Loose matching for methods with smaller chunk sizes

This approach ensures that each chunking method is evaluated fairly on its ability to preserve the context needed to answer insight-based questions.
