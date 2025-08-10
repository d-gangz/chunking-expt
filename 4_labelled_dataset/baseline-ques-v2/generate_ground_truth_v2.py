"""
Script to generate ground truth dataset from 5 legal/business transcripts using dimension-based question generation.

Input data sources: 1_transcripts/cleaned-full/, 00_threads/threads/sl-dimensions.json
Output destinations: 4_labelled_dataset/baseline-ques-v2/
Dependencies: OpenAI API key in .env file, langchain packages
Key exports: generate_insights(), generate_dimension_question(), main()
Side effects: Creates insights.json and base_ground_truth.json files

Uses a two-step LLM approach:
1. First generates 40 insights from transcripts (same as v1)
2. Then generates 1 question per insight using sl-dimensions.json for context

The dimensions (Request Intent Category, Request Specificity, User Persona) are systematically
cycled through to ensure balanced representation across all generated questions.
"""

import os
import json
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path
from itertools import cycle

from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()


# Step 1: Pydantic schemas for insights generation (same as v1)
class InsightQuote(BaseModel):
    """A substantial quote supporting an insight."""

    quoted_text: str = Field(
        description="Verbatim quote from the transcript (50-150 words, capturing complete thoughts)"
    )
    transcript_title: str = Field(
        description="Exact title of the transcript this quote comes from"
    )


class Insight(BaseModel):
    """An insight with supporting quotes from transcripts."""

    insight_id: str = Field(description="Unique identifier (e.g., insight_001)")
    comprehensive_answer: str = Field(
        description="The insight as a complete answer (2-4 sentences revealing deep understanding, patterns, or principles)"
    )
    source_quotes: List[InsightQuote] = Field(
        description="2-4 substantial quotes supporting this insight, preferably from different transcripts",
        min_length=2,
        max_length=4,
    )


class InsightsList(BaseModel):
    """List of insights extracted from transcripts."""

    insights: List[Insight] = Field(
        description="Exactly 30 insights extracted from the transcripts",
        min_length=30,
        max_length=30,
    )


# Step 2: Pydantic schemas for dimension-based question generation
class DimensionUsed(BaseModel):
    """Tracks which dimension values were used for question generation."""

    request_intent_category: str = Field(
        description="The dimension value used from Request Intent Category"
    )
    request_specificity: str = Field(
        description="The dimension value used from Request Specificity"
    )
    user_persona: str = Field(description="The dimension value used from User Persona")


class DimensionQuestion(BaseModel):
    """A single question generated using specific dimensions."""

    question: str = Field(description="The generated question text")
    dimensions_used: DimensionUsed = Field(
        description="The specific dimension values used to generate this question"
    )


def load_transcripts(transcript_dir: str) -> Dict[str, str]:
    """Load all transcript files from the cleaned directory."""
    transcripts = {}
    transcript_path = Path(transcript_dir)

    for file_path in transcript_path.glob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract clean title from filename
            title = file_path.stem.replace("_", " ").replace("  ", " ")
            transcripts[title] = content

    return transcripts


def load_dimensions(dimensions_path: str) -> Dict[str, List[Dict]]:
    """Load the sl-dimensions.json file."""
    with open(dimensions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_transcripts_for_prompt(transcripts: Dict[str, str]) -> str:
    """Format transcripts for inclusion in the prompt."""
    formatted = []
    for i, (title, content) in enumerate(transcripts.items(), 1):
        formatted.append(
            f"TRANSCRIPT {i}: {title}\n{'-' * 80}\n{content}\n{'=' * 80}\n"
        )
    return "\n".join(formatted)


def create_dimension_combinations(
    dimensions: Dict[str, List[Dict]]
) -> List[Tuple[Dict, Dict, Dict]]:
    """Create all possible combinations of dimensions for systematic cycling."""
    request_intent = dimensions["Request Intent Category"]
    request_specificity = dimensions["Request Specificity"]
    user_persona = dimensions["User Persona"]

    combinations = []
    for intent in request_intent:
        for specificity in request_specificity:
            for persona in user_persona:
                combinations.append((intent, specificity, persona))

    return combinations


def generate_insights(transcripts: Dict[str, str]) -> List[Insight]:
    """Step 1: Generate insights from transcripts."""
    print("\n🎯 Step 1: Generating insights from transcripts...")

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)

    # Create structured LLM
    structured_llm = llm.with_structured_output(InsightsList)

    # Create prompt (modified to generate 40 insights)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert at analyzing legal and business transcripts to extract deep insights.

Extract EXACTLY 30 INSIGHTS that serve as COMPREHENSIVE ANSWERS:
- Each insight should be a complete, self-contained comprehensive answer (3-5 sentences)
- Must reveal deep understanding, patterns, or principles
- PRIORITY: Create insights that connect concepts ACROSS DIFFERENT transcripts
- Must be fully supported by quoted text from the transcripts

For each insight:
- Write the complete insight as you would answer a question
- Include 2-4 SUBSTANTIAL quotes (100-200 words each, capturing complete thoughts)
- IMPORTANT: Draw quotes from MULTIPLE transcripts whenever possible
- Quotes must be VERBATIM from the transcripts (no modifications)
- Ensure quotes provide rich context, not just keywords

Cover all 5 transcripts with emphasis on cross-transcript connections""",
            ),
            (
                "human",
                """Analyze these 5 legal/business transcripts and extract 30 high-quality insights:

{transcripts}

Generate insights that reveal deep understanding and patterns across transcripts.""",
            ),
        ]
    )

    # Create chain and invoke
    chain = prompt | structured_llm
    formatted_transcripts = format_transcripts_for_prompt(transcripts)

    result = chain.invoke({"transcripts": formatted_transcripts})

    print(f"✅ Generated {len(result.insights)} insights")
    return result.insights


def generate_dimension_question(
    insight: Insight, dimension_combo: Tuple[Dict, Dict, Dict]
) -> DimensionQuestion:
    """Step 2: Generate a single question for an insight using specific dimensions."""
    intent_dim, specificity_dim, persona_dim = dimension_combo

    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)

    # Create structured LLM
    structured_llm = llm.with_structured_output(DimensionQuestion)

    # Create prompt with injected dimensions
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert at generating contextually relevant questions that can be answered by a given insight.

Generate 1 question that this comprehensive answer addresses, using the following dimensional context to shape the question:

**Request Intent Category - {intent_dimension}:**
Description: {intent_description}
Examples: {intent_examples}

**Request Specificity - {specificity_dimension}:**
Description: {specificity_description} 
Examples: {specificity_examples}

**User Persona - {persona_dimension}:**
Description: {persona_description}
Examples: {persona_examples}

CRITICAL INSTRUCTIONS FOR STYLE MATCHING:
- Capture the INTENT and CONTEXT of the examples while VARYING the phrasing
- Match the level of detail and specificity shown in the examples
- Include similar contextual details (company size, specific situations, etc.) that match the persona
- Use the same natural, peer-to-peer conversational tone as the examples

AVOID THESE REPETITIVE PATTERNS:
- Do NOT start every question with "For those of you..." or "For those..."
- Do NOT always use "For those leading..." or "For those at..."
- Do NOT always use "Curious to hear..." or "Has anyone..."
- Do NOT end every question with "Would love to hear..." or "much appreciated"
- AVOID using the exact same opening as previous questions

INSTEAD, VARY YOUR OPENINGS based on the intent:
- For Resource Acquisition: "Looking for recommendations on...", "Need help finding...", "Can anyone suggest...", "We need a consultant who..."
- For Knowledge Sharing: "What's your approach to...", "How do other companies handle...", "What strategies work for...", "Anyone have experience with..."
- For Problem Resolution: "We're struggling with...", "Running into issues with...", "Need guidance on...", "How do you solve..."
- For different personas: Adjust formality and technical depth appropriately

VARY YOUR CLOSINGS:
- Mix between: "Thanks!", "Any insights?", "Appreciate the help", or simply end without a closing
- Sometimes include context about urgency or specific needs
- Sometimes just end with the question

Your question should:
- Be answerable by the comprehensive answer provided
- Reflect the intent, specificity, and persona through CONTENT not just phrasing
- Sound authentic to someone in that role/situation
- Feel natural and varied, not formulaic

Generate a question that captures the essence of the dimensional context while sounding fresh and different from typical patterns.""",
            ),
            (
                "human",
                """Generate 1 question using the dimensional context above for this insight:

Insight ID: {insight_id}
Comprehensive Answer: {comprehensive_answer}

The question should be answerable by the comprehensive answer and reflect the dimensional context provided.""",
            ),
        ]
    )

    # Create chain and invoke
    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "insight_id": insight.insight_id,
            "comprehensive_answer": insight.comprehensive_answer,
            "intent_dimension": intent_dim["dimension"],
            "intent_description": intent_dim["description"],
            "intent_examples": "\n".join([f"- {ex}" for ex in intent_dim["examples"]]),
            "specificity_dimension": specificity_dim["dimension"],
            "specificity_description": specificity_dim["description"],
            "specificity_examples": "\n".join(
                [f"- {ex}" for ex in specificity_dim["examples"]]
            ),
            "persona_dimension": persona_dim["dimension"],
            "persona_description": persona_dim["description"],
            "persona_examples": "\n".join(
                [f"- {ex}" for ex in persona_dim["examples"]]
            ),
        }
    )

    return result


def validate_quotes_in_transcripts(
    insights: List[Insight], transcripts: Dict[str, str]
) -> List[str]:
    """Validate that all quotes exist verbatim in the transcripts."""
    validation_errors = []

    for insight in insights:
        for quote in insight.source_quotes:
            # Find the transcript
            transcript_content = None
            for title, content in transcripts.items():
                if quote.transcript_title in title or title in quote.transcript_title:
                    transcript_content = content
                    break

            if transcript_content is None:
                validation_errors.append(
                    f"Insight {insight.insight_id}: Could not find transcript '{quote.transcript_title}'"
                )
                continue

            # Check if quote exists verbatim
            if quote.quoted_text not in transcript_content:
                # Try to find a close match
                quote_words = quote.quoted_text.split()[:10]  # First 10 words
                snippet = " ".join(quote_words)
                if snippet in transcript_content:
                    validation_errors.append(
                        f"Insight {insight.insight_id}: Quote partially found but not exact match"
                    )
                else:
                    validation_errors.append(
                        f"Insight {insight.insight_id}: Quote not found in transcript '{quote.transcript_title}'"
                    )

    return validation_errors


def convert_to_final_format(all_questions: List[Dict]) -> List[Dict]:
    """Convert question entries to the final output format."""
    output_entries = []
    question_counter = 1

    for question_entry in all_questions:
        dimension_question = question_entry['dimension_question']
        dimension_combo = question_entry['dimension_combo']
        intent_dim, specificity_dim, persona_dim = dimension_combo

        entry = {
            "question_id": f"q_{question_counter:03d}",
            "question": dimension_question.question,
            "comprehensive_answer": question_entry['comprehensive_answer'],
            "source_quotes": [
                {
                    "quoted_text": quote.quoted_text,
                    "transcript_title": quote.transcript_title,
                }
                for quote in question_entry['source_quotes']
            ],
            "dimensions_used": {
                "request_intent_category": {
                    "dimension": intent_dim["dimension"],
                    "description": intent_dim["description"],
                    "examples": intent_dim["examples"],
                },
                "request_specificity": {
                    "dimension": specificity_dim["dimension"],
                    "description": specificity_dim["description"],
                    "examples": specificity_dim["examples"],
                },
                "user_persona": {
                    "dimension": persona_dim["dimension"],
                    "description": persona_dim["description"],
                    "examples": persona_dim["examples"],
                },
            },
        }
        output_entries.append(entry)
        question_counter += 1

    return output_entries


def main():
    """Main function to generate the ground truth dataset."""
    print("🚀 Starting ground truth dataset generation (v2 with dimensions)...")

    # Load transcripts
    print("\n📄 Loading transcripts...")
    transcript_dir = "/Users/gang/suite-work/chunking-expt/1_transcripts/cleaned-full"
    transcripts = load_transcripts(transcript_dir)
    print(f"✅ Loaded {len(transcripts)} transcripts")

    # Load dimensions
    print("\n🎯 Loading sl-dimensions...")
    dimensions_path = (
        "/Users/gang/suite-work/chunking-expt/00_threads/threads/sl-dimensions.json"
    )
    dimensions = load_dimensions(dimensions_path)
    print(f"✅ Loaded {len(dimensions)} dimension categories")

    # Create dimension combinations for cycling
    combinations = create_dimension_combinations(dimensions)
    combination_cycle = cycle(combinations)
    print(f"✅ Created {len(combinations)} total dimension combinations")

    # Step 1: Generate insights
    print("\n🎯 Step 1: Generating 30 insights...")
    try:
        insights = generate_insights(transcripts)
    except Exception as e:
        print(f"❌ Error generating insights: {e}")
        return

    # Export insights to JSON
    print("\n💾 Saving insights to insights.json...")
    insights_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_insights": len(insights),
            "transcripts_analyzed": list(transcripts.keys()),
            "version": "v2_with_dimensions",
        },
        "insights": [
            {
                "insight_id": insight.insight_id,
                "comprehensive_answer": insight.comprehensive_answer,
                "source_quotes": [
                    {
                        "quoted_text": quote.quoted_text,
                        "transcript_title": quote.transcript_title,
                    }
                    for quote in insight.source_quotes
                ],
            }
            for insight in insights
        ],
    }
    insights_output_path = "/Users/gang/suite-work/chunking-expt/4_labelled_dataset/baseline-ques-v2/insights.json"
    with open(insights_output_path, "w", encoding="utf-8") as f:
        json.dump(insights_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Insights saved to {insights_output_path}")

    # Validate quotes
    print("\n🔍 Validating quotes against transcripts...")
    validation_errors = validate_quotes_in_transcripts(insights, transcripts)
    if validation_errors:
        print(f"⚠️ Found {len(validation_errors)} validation issues:")
        for error in validation_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(validation_errors) > 5:
            print(f"  ... and {len(validation_errors) - 5} more")
    else:
        print("✅ All quotes validated successfully")

    # Step 2: Generate dimension-based questions for each insight (2 per insight)
    print("\n🎯 Step 2: Generating dimension-based questions (2 per insight)...")
    all_questions = []
    
    for i, insight in enumerate(tqdm(insights, desc="Generating dimension questions")):
        try:
            # Generate 2 questions for this insight using different dimension combinations
            for q_num in range(2):
                # Get next dimension combination from cycle
                dimension_combo = next(combination_cycle)

                # Generate question using dimensions
                dimension_question = generate_dimension_question(insight, dimension_combo)
                
                # Store question with unique ID
                question_entry = {
                    'insight_id': insight.insight_id,
                    'question_num': q_num + 1,
                    'dimension_question': dimension_question,
                    'dimension_combo': dimension_combo,
                    'comprehensive_answer': insight.comprehensive_answer,
                    'source_quotes': insight.source_quotes
                }
                all_questions.append(question_entry)

            # Log which dimensions were used for first few insights
            if i < 3:  # Show first 3 for verification
                print(f"\n  Insight {insight.insight_id} - Generated 2 questions")

        except Exception as e:
            print(f"\n⚠️ Error generating questions for {insight.insight_id}: {e}")
            continue

    # Convert to final format
    print("\n📊 Converting to final output format...")
    output_entries = convert_to_final_format(all_questions)
    print(
        f"✅ Created {len(output_entries)} question entries from {len(insights)} insights"
    )

    # Add metadata
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_insights": len(insights),
            "total_questions": len(output_entries),
            "transcripts_analyzed": list(transcripts.keys()),
            "validation_errors": len(validation_errors),
            "version": "v2_with_dimensions",
            "dimension_combinations_available": len(combinations),
        },
        "entries": output_entries,
    }

    # Save to JSON
    output_path = "/Users/gang/suite-work/chunking-expt/4_labelled_dataset/baseline-ques-v2/base_ground_truth.json"
    print(f"\n💾 Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n✅ Ground truth dataset generation complete! (v2)")
    print(f"📈 Summary:")
    print(f"  - Total insights: {len(insights)}")
    print(f"  - Total questions: {len(output_entries)}")
    print(f"  - Questions per insight: 2 (using dimensions)")
    print(f"  - Validation issues: {len(validation_errors)}")
    print(f"  - Dimension combinations: {len(combinations)} available")


if __name__ == "__main__":
    main()
