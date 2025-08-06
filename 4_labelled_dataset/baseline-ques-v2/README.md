# Baseline Questions v2 - Dimension-Based Generation

This directory contains version 2 of the baseline question generation system that incorporates the three-dimensional framework from `00_threads/sl-dimensions.json`.

## Key Changes from v1

1. **30 Insights**: Generates 30 insights (optimized for token limits)
2. **2 Questions per Insight**: Creates exactly 2 questions per insight (60 total)
3. **Dimension-Based Questions**: Uses `sl-dimensions.json` to shape question generation
4. **Systematic Cycling**: Rotates through dimension combinations systematically
5. **Enhanced Output**: Includes `dimensions_used` field for traceability

## Dimension Framework

Each question is generated using one value from each of the three dimensions:

### Request Intent Category
- **Resource Acquisition**: Seeking recommendations, referrals, or introductions
- **Knowledge Sharing**: Benchmarking practices, understanding trends, learning from peers
- **Problem Resolution**: Facing specific challenges needing expert guidance

### Request Specificity  
- **Highly Targeted**: Very specific requirements, jurisdictions, or parameters
- **Exploratory**: Broad requests seeking general guidance or best practices
- **Multi-faceted**: Complex requests involving multiple jurisdictions or practice areas

### User Persona
- **Growth-stage Executive**: Startups/high-growth companies with scaling challenges
- **Enterprise Executive**: Established companies with complex operational issues  
- **Specialized Role Holder**: Specific functional expertise (privacy, compliance, ops)

## Usage

```bash
# Run the dimension-based generation
uv run python generate_ground_truth_v2.py
```

## Output Format

The output includes full dimension details for complete traceability:

```json
{
  "question_id": "q_001",
  "question": "Generated question text",
  "comprehensive_answer": "The insight as complete answer",
  "source_quotes": [
    {
      "quoted_text": "Verbatim quote from transcript",
      "transcript_title": "Source transcript name"
    }
  ],
  "dimensions_used": {
    "request_intent_category": {
      "dimension": "Resource Acquisition",
      "description": "Seeking recommendations, referrals, or introductions",
      "examples": ["Can anyone recommend...", "Looking for referrals to..."]
    },
    "request_specificity": {
      "dimension": "Highly Targeted", 
      "description": "Very specific requirements, jurisdictions, or parameters",
      "examples": ["Need Series A lawyer in Delaware...", "GDPR compliance for SaaS..."]
    },
    "user_persona": {
      "dimension": "Growth-stage Executive",
      "description": "Startups/high-growth companies with scaling challenges", 
      "examples": ["Series B startup needing...", "High-growth company facing..."]
    }
  }
}
```

## Generation Process

The script follows a 2-step approach:

1. **Step 1**: Generate 30 insights from 5 legal/business transcripts
   - Each insight is a comprehensive answer (3-5 sentences)
   - Supported by 2-4 substantial quotes from transcripts
   - Emphasizes cross-transcript connections

2. **Step 2**: Generate 2 questions per insight using dimension cycling
   - Each insight generates exactly 2 different questions (60 total)
   - Questions use different dimension combinations via systematic rotation
   - Each question reflects authentic style from dimension examples

## Files Generated

- `insights.json`: 30 insights with quotes (step 1 output)
- `base_ground_truth.json`: Final dataset with 60 dimension-based questions (step 2 output)