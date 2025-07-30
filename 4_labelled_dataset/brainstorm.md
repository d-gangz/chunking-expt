# Labeled Dataset Brainstorm

## Query Types for Synthetic Query Generation

### Level 1: Factual/Direct Queries
**Purpose:** Test basic information retrieval
**Examples:**
- "What is the expiration period for RSU plans?"
- "How long was Etsy's parental leave policy?"
- "What percentage of Etsy sellers identify as women?"

**Characteristics:**
- Single fact retrieval
- Clear, unambiguous answer
- Usually found in 1-2 consecutive chunks

### Level 2: Conceptual/Understanding Queries
**Purpose:** Test comprehension of concepts and ideas
**Examples:**
- "What are the risks of using AI for legal research?"
- "How do you balance being ethical with business pressures in crypto?"
- "What's the difference between gender diversity and racial diversity challenges?"

**Characteristics:**
- Requires understanding of abstract concepts
- May need multiple chunks for complete answer
- Tests system's ability to identify related discussions

### Level 3: Practical/Application Queries ⭐ (INSIGHT QUERIES)
**Purpose:** Test ability to extract actionable advice
**Examples:**
- "How should I prepare my company for an IPO from an equity perspective?"
- "What's the best way to prompt ChatGPT for legal research?"
- "How can legal departments drive D&I initiatives?"

**Characteristics:**
- Requires synthesis across multiple chunks
- Needs to extract actionable steps/recommendations
- Most valuable for end users
- Tests true "insight extraction" capability

### Level 4: Cross-Reference Queries
**Purpose:** Test retrieval across multiple segments/speakers
**Examples:**
- "What are all the best practices mentioned for board management?"
- "What tools and techniques were discussed for AI in legal work?"
- "What were the key challenges faced by companies going public?"

**Characteristics:**
- Requires comprehensive retrieval
- Tests system's ability to aggregate information
- May span entire transcript or multiple transcripts

### Level 5: Speaker/Context-Specific Queries
**Purpose:** Test metadata and context understanding
**Examples:**
- "What was Louisa Daniels' experience with IPO preparation?"
- "Which companies were mentioned as examples in the panels?"
- "What law firms sponsored these events?"

**Characteristics:**
- Tests speaker attribution
- Requires understanding of context/metadata
- Important for credibility and source tracking

## Why Level 3 Queries Are Critical for "Insights"

### Definition of Insights
Insights are not just facts or information, but **actionable understanding** that users can apply to their own situations. They answer "What should I do?" not just "What is true?"

### Why Level 3 Best Captures Insights:

1. **Synthesis Requirement**: These queries force the system to combine information from multiple sources to create a coherent action plan

2. **Practical Application**: They mirror real user needs - people don't just want to know facts, they want to know how to apply them

3. **Value Generation**: The difference between a good and great Q&A system is whether it can provide actionable guidance, not just information retrieval

4. **Complex Reasoning**: These queries test if the system can:
   - Identify relevant experiences/examples
   - Extract principles from specific cases
   - Generalize advice appropriately
   - Present information in an actionable format

### Example Breakdown:

**Query:** "How should I prepare my company for an IPO from an equity perspective?"

**Required Chunks Might Include:**
- Louisa's experience joining 3 months before IPO
- Discussion of RSU plan expiration issues
- 409A valuation timing
- Employee communication strategies
- Timeline considerations (4-month preparation)

**Good Insight Answer Would:**
- Synthesize timeline recommendations
- Highlight key risk areas (RSU expiration, accounting charges)
- Provide actionable checklist
- Include real examples from the speakers

## Evaluation Strategy

### For Level 3 Queries Specifically:

1. **Retrieval Evaluation:**
   - Did it find all the relevant experience/example chunks?
   - Did it identify the advice/recommendation segments?
   - Did it avoid irrelevant but keyword-similar chunks?

2. **Generation Evaluation:**
   - Does the answer provide clear action items?
   - Is advice properly contextualized?
   - Are examples used effectively?
   - Is the synthesis coherent and complete?

### Proposed Query Distribution:
- Level 1: 15% (baseline testing)
- Level 2: 20% (concept understanding)
- **Level 3: 40% (core insight extraction)**
- Level 4: 15% (comprehensive retrieval)
- Level 5: 10% (metadata/attribution)

## Next Steps

1. Create 10-15 Level 3 queries per transcript
2. Manually identify all chunks that contribute to answering each query
3. Rank chunks by importance (primary vs supporting)
4. Create "ideal answer" templates that demonstrate good insight extraction
5. Test different chunking strategies to see which best preserves actionable advice

## Key Insight: The Chunking Challenge

Level 3 queries reveal a critical challenge: actionable insights often span multiple segments in transcripts because:
- Speakers build up to recommendations
- Examples and principles are separated
- Q&A sections add crucial details
- Context is established early, advice comes later

This suggests we need chunking strategies that preserve these relationships.