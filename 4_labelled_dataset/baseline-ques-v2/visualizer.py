"""
Streamlit app for visualizing ground truth questions and dimensions data.

Input data sources: base_ground_truth.json
Output destinations: Interactive web interface
Dependencies: streamlit, json
Key exports: Streamlit app interface
Side effects: Displays interactive web interface
"""

import streamlit as st
import json
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Ground Truth Data Visualizer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling and scrollable columns
st.markdown("""
<style>
    .main-container {
        padding-top: 1rem;
    }
    
    .navigation-bar {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
    }
    
    .entry-counter {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    .element-container {
        max-height: 80vh;
        overflow-y: auto;
    }
    
    div[data-testid="column"] > div {
        max-height: 80vh;
        overflow-y: auto;
        padding-right: 10px;
    }
    
    .question-box {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid #1976d2;
        color: #000 !important;
    }
    
    .question-box h3, .question-box p, .question-box small {
        color: #000 !important;
    }
    
    .answer-box {
        background-color: #f3e5f5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border-left: 5px solid #7b1fa2;
        color: #000 !important;
    }
    
    .answer-box h3, .answer-box p {
        color: #000 !important;
    }
    
    .quote-box {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 3px solid #ff9800;
        font-style: italic;
        color: #000 !important;
    }
    
    .quote-box p {
        color: #000 !important;
    }
    
    .transcript-title {
        font-size: 0.9rem;
        color: #333 !important;
        margin-top: 0.5rem;
        font-weight: bold;
    }
    
    .dimension-box {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 3px solid #4caf50;
        color: #000 !important;
    }
    
    .dimension-title {
        font-weight: bold;
        color: #2e7d32 !important;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .dimension-description {
        color: #000 !important;
        margin-bottom: 1rem;
        line-height: 1.4;
    }
    
    
    .example-item {
        background-color: #f5f5f5;
        padding: 0.8rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        border-left: 2px solid #9e9e9e;
        font-size: 0.9rem;
        line-height: 1.3;
        color: #000 !important;
    }
    
    .metadata-box {
        background-color: #fff9c4;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border-left: 3px solid #fbc02d;
        color: #000 !important;
    }
    
    .metadata-box h4, .metadata-box p, .metadata-box strong {
        color: #000 !important;
    }
    
    .toggle-button-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        height: 60px;
        padding-top: 10px;
    }
    
    .stButton > button {
        background-color: #f0f2f6;
        color: #1976d2;
        border: 1px solid #1976d2;
        border-radius: 0.3rem;
        padding: 0.25rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 500;
        min-height: 35px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #1976d2;
        color: white;
        border-color: #1976d2;
    }
    
    .stButton > button:active, .stButton > button:focus {
        background-color: #1565c0 !important;
        color: white !important;
        border-color: #1565c0 !important;
        box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load the ground truth data from JSON file."""
    try:
        file_path = Path(__file__).parent / "base_ground_truth.json"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ Could not find base_ground_truth.json in the same directory as this script.")
        st.stop()
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format in base_ground_truth.json")
        st.stop()

@st.cache_data
def calculate_dimension_stats(entries):
    """Calculate statistics for each dimension category."""
    dimension_stats = {
        'request_intent_category': {},
        'request_specificity': {},
        'user_persona': {}
    }
    
    for entry in entries:
        dimensions = entry.get('dimensions_used', {})
        
        for dim_key, dim_data in dimensions.items():
            if dim_key in dimension_stats:
                dimension_value = dim_data.get('dimension', 'Unknown')
                dimension_stats[dim_key][dimension_value] = dimension_stats[dim_key].get(dimension_value, 0) + 1
    
    return dimension_stats

@st.cache_data
def analyze_dimension_combinations(entries):
    """Analyze dimension combinations and find duplicates."""
    combination_groups = {}
    
    for entry in entries:
        dimensions = entry.get('dimensions_used', {})
        
        # Create a combination key from all dimension values
        combination_key = tuple(sorted([
            (dim_key, dim_data.get('dimension', 'Unknown'))
            for dim_key, dim_data in dimensions.items()
        ]))
        
        # Group entries by their combination
        if combination_key not in combination_groups:
            combination_groups[combination_key] = []
        
        combination_groups[combination_key].append({
            'question_id': entry.get('question_id', 'N/A'),
            'question': entry.get('question', 'N/A')[:100] + ('...' if len(entry.get('question', '')) > 100 else '')
        })
    
    # Sort by number of questions per combination (descending)
    sorted_combinations = sorted(
        combination_groups.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    return sorted_combinations, combination_groups

def display_navigation(current_index, total_entries):
    """Display navigation controls."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_index == 0)):
            st.session_state.current_entry_index -= 1
            st.rerun()
    
    with col2:
        st.markdown(f"<div class='entry-counter'>Entry {current_index + 1} of {total_entries}</div>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("➡️ Next", disabled=(current_index == total_entries - 1)):
            st.session_state.current_entry_index += 1
            st.rerun()

def display_left_column(entry):
    """Display question, answer, and source quotes in the left column."""
    # Question
    st.markdown(f"""
    <div class='question-box'>
        <h3>❓ Question</h3>
        <p><strong>{entry['question']}</strong></p>
        <small>ID: {entry['question_id']}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Comprehensive Answer
    st.markdown(f"""
    <div class='answer-box'>
        <h3>💡 Comprehensive Answer</h3>
        <p>{entry['comprehensive_answer']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Source Quotes
    st.markdown("### 📜 Source Quotes")
    for quote in entry['source_quotes']:
        st.markdown(f"""
        <div class='quote-box'>
            <p>"{quote['quoted_text']}"</p>
            <div class='transcript-title'>📺 Source: {quote['transcript_title']}</div>
        </div>
        """, unsafe_allow_html=True)

def display_right_column(entry):
    """Display dimensions and their details in the right column."""
    dimensions = entry['dimensions_used']
    
    # Get the global toggle state
    show_examples = st.session_state.get('show_all_examples', False)
    
    for dim_key, dim_data in dimensions.items():
        # Format dimension key for display
        display_key = dim_key.replace('_', ' ').title()
        
        # Display the dimension with compact view
        st.markdown(f"""
        <div class='dimension-box'>
            <div class='dimension-title'>{display_key}: {dim_data['dimension']}</div>
            <div class='dimension-description'>{dim_data['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Examples in expandable section, controlled by global toggle
        with st.expander(f"📋 Examples for {display_key}", expanded=show_examples):
            for example in dim_data['examples']:
                st.markdown(f"""
                <div class='example-item'>
                    {example}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

def display_metadata(metadata, dimension_stats):
    """Display metadata information with dimension statistics."""
    st.markdown(f"""
    <div class='metadata-box'>
        <h4>📊 Dataset Metadata</h4>
        <p><strong>Version:</strong> {metadata.get('version', 'N/A')}</p>
        <p><strong>Generated:</strong> {metadata.get('generated_at', 'N/A')}</p>
        <p><strong>Total Questions:</strong> {metadata.get('total_questions', 'N/A')}</p>
        <p><strong>Total Insights:</strong> {metadata.get('total_insights', 'N/A')}</p>
        <p><strong>Dimension Combinations:</strong> {metadata.get('dimension_combinations_available', 'N/A')}</p>
        <p><strong>Validation Errors:</strong> {metadata.get('validation_errors', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dimension Statistics
    st.markdown("### 📈 Dimension Distribution")
    
    # Request Intent Category Statistics
    st.markdown("#### 🎯 Request Intent Category")
    intent_stats = dimension_stats.get('request_intent_category', {})
    if intent_stats:
        for category, count in sorted(intent_stats.items()):
            percentage = (count / sum(intent_stats.values())) * 100
            st.markdown(f"• **{category}**: {count} entries ({percentage:.1f}%)")
    else:
        st.markdown("• No data available")
    
    st.markdown("---")
    
    # Request Specificity Statistics
    st.markdown("#### 🔍 Request Specificity")
    specificity_stats = dimension_stats.get('request_specificity', {})
    if specificity_stats:
        for category, count in sorted(specificity_stats.items()):
            percentage = (count / sum(specificity_stats.values())) * 100
            st.markdown(f"• **{category}**: {count} entries ({percentage:.1f}%)")
    else:
        st.markdown("• No data available")
    
    st.markdown("---")
    
    # User Persona Statistics
    st.markdown("#### 👤 User Persona")
    persona_stats = dimension_stats.get('user_persona', {})
    if persona_stats:
        for category, count in sorted(persona_stats.items()):
            percentage = (count / sum(persona_stats.values())) * 100
            st.markdown(f"• **{category}**: {count} entries ({percentage:.1f}%)")
    else:
        st.markdown("• No data available")
    
    # Overall Statistics Summary
    st.markdown("---")
    st.markdown("#### 📋 Summary")
    total_intent_types = len(intent_stats)
    total_specificity_types = len(specificity_stats)
    total_persona_types = len(persona_stats)
    
    st.markdown(f"""
    • **Unique Intent Categories**: {total_intent_types}  
    • **Unique Specificity Levels**: {total_specificity_types}  
    • **Unique User Personas**: {total_persona_types}  
    • **Total Dimension Combinations**: {metadata.get('dimension_combinations_available', 'N/A')}
    """)

def display_combination_analysis(sorted_combinations, combination_groups):
    """Display analysis of dimension combinations."""
    st.markdown("### 🔄 Dimension Combination Analysis")
    
    total_combinations = len(combination_groups)
    total_questions = sum(len(questions) for questions in combination_groups.values())
    duplicate_combinations = sum(1 for questions in combination_groups.values() if len(questions) > 1)
    duplicate_questions = sum(len(questions) for questions in combination_groups.values() if len(questions) > 1)
    
    # Summary stats
    st.markdown(f"""
    **📊 Combination Overview:**
    • **Total Unique Combinations**: {total_combinations}
    • **Combinations with Multiple Questions**: {duplicate_combinations}
    • **Questions in Duplicate Combinations**: {duplicate_questions} out of {total_questions}
    • **Uniqueness Rate**: {((total_combinations - duplicate_combinations) / total_combinations * 100):.1f}%
    """)
    
    st.markdown("---")
    
    # Show combinations with multiple questions
    st.markdown("#### 🔍 Combinations with Multiple Questions")
    
    if duplicate_combinations > 0:
        for combination, questions in sorted_combinations:
            if len(questions) > 1:
                # Format the combination for display
                combination_display = []
                for dim_key, dim_value in combination:
                    clean_key = dim_key.replace('_', ' ').title()
                    combination_display.append(f"**{clean_key}**: {dim_value}")
                
                with st.expander(f"🔗 **{len(questions)} questions** with same combination", expanded=False):
                    st.markdown("**Dimension Combination:**")
                    for dim_display in combination_display:
                        st.markdown(f"• {dim_display}")
                    
                    st.markdown("**Questions:**")
                    for i, question in enumerate(questions, 1):
                        st.markdown(f"{i}. **{question['question_id']}**: {question['question']}")
                    
                    st.markdown("---")
    else:
        st.markdown("✅ **All questions have unique dimension combinations!**")
    
    # Show some unique combinations as examples
    st.markdown("#### ✨ Sample Unique Combinations")
    unique_combinations = [(combo, questions) for combo, questions in sorted_combinations if len(questions) == 1]
    
    if unique_combinations:
        # Show first 3 unique combinations as examples
        for combination, questions in unique_combinations[:3]:
            combination_display = []
            for dim_key, dim_value in combination:
                clean_key = dim_key.replace('_', ' ').title()
                combination_display.append(f"**{clean_key}**: {dim_value}")
            
            question = questions[0]
            with st.expander(f"💎 **{question['question_id']}** - Unique combination", expanded=False):
                st.markdown("**Dimension Combination:**")
                for dim_display in combination_display:
                    st.markdown(f"• {dim_display}")
                
                st.markdown(f"**Question**: {question['question']}")
    else:
        st.markdown("No unique combinations found (all combinations have multiple questions).")

def main():
    """Main application function."""
    # Load data
    data = load_data()
    entries = data['entries']
    metadata = data.get('metadata', {})
    
    # Calculate dimension statistics and combinations
    dimension_stats = calculate_dimension_stats(entries)
    sorted_combinations, combination_groups = analyze_dimension_combinations(entries)
    
    # Initialize session state
    if 'current_entry_index' not in st.session_state:
        st.session_state.current_entry_index = 0
    
    # Ensure index is within bounds
    if st.session_state.current_entry_index >= len(entries):
        st.session_state.current_entry_index = 0
    elif st.session_state.current_entry_index < 0:
        st.session_state.current_entry_index = len(entries) - 1
    
    # App title
    st.title("🔍 Ground Truth Data Visualizer")
    st.markdown("---")
    
    # Display metadata
    with st.expander("📊 Dataset Information & Statistics", expanded=False):
        display_metadata(metadata, dimension_stats)
    
    # Display combination analysis
    with st.expander("🔄 Dimension Combination Analysis", expanded=False):
        display_combination_analysis(sorted_combinations, combination_groups)
    
    # Navigation
    display_navigation(st.session_state.current_entry_index, len(entries))
    st.markdown("---")
    
    # Get current entry
    current_entry = entries[st.session_state.current_entry_index]
    
    # Two-column layout
    left_col, right_col = st.columns([1, 1], gap="large")
    
    with left_col:
        st.markdown("## 📝 Question & Answer")
        with st.container():
            display_left_column(current_entry)
    
    with right_col:
        # Create header with toggle button
        header_col1, header_col2 = st.columns([3, 1])
        
        with header_col1:
            st.markdown("## 🎯 Dimensions & Categories")
        
        with header_col2:
            # Initialize session state for toggle
            if 'show_all_examples' not in st.session_state:
                st.session_state.show_all_examples = False
            
            # Toggle button with proper styling
            st.markdown('<div class="toggle-button-container">', unsafe_allow_html=True)
            button_text = "🔽 Show All" if not st.session_state.show_all_examples else "🔼 Hide All"
            if st.button(button_text, key="toggle_examples"):
                st.session_state.show_all_examples = not st.session_state.show_all_examples
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            display_right_column(current_entry)
    
    # Keyboard shortcuts info
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        st.markdown("""
        - **Left Arrow (←)**: Previous entry
        - **Right Arrow (→)**: Next entry
        - **Home**: Go to first entry
        - **End**: Go to last entry
        """)

# Keyboard navigation support
if __name__ == "__main__":
    main()