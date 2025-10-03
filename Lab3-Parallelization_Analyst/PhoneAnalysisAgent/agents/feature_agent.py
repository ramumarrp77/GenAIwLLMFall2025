import streamlit as st
from utils.snowflake_connection import execute_feature_search, call_cortex_complete

class FeatureAgent:
    def __init__(self):
        self.name = "Feature Extraction Specialist"
        self.icon = "🔍"
        self.model = "claude-3-5-sonnet"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Extract features using RAG vector search"""
        
        if show_backend:
            with st.expander("🔧 Feature Agent - Backend Process", expanded=False):
                st.write("**Method:** Vector Similarity Search")
                st.write("**Search Query:**")
                st.code(f"Extract iPhone features mentioned in: {user_query}", language="text")
        
        # Use vector search to find feature-related reviews
        feature_reviews = execute_feature_search(user_query)
        
        # Extract and categorize features using LLM
        extraction_prompt = f"""You are a Feature Extraction Specialist. Analyze these iPhone reviews and extract mentioned features.

Reviews: {feature_reviews}

User focus: {user_query}

Extract and categorize features mentioned:
- Camera: [What customers say about camera]
- Battery: [What customers say about battery]
- Screen: [What customers say about screen/display]
- Performance: [What customers say about speed/performance]
- Design: [What customers say about physical design]

Return ONLY the structured feature analysis, no additional text."""

        result = call_cortex_complete(extraction_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Feature Agent - Backend Process", expanded=False):
                st.write("**Retrieved Reviews:**")
                st.text_area("Review Data:", feature_reviews[:300] + "...", height=100)
                st.write("**Extraction Prompt:**")
                st.code(extraction_prompt, language="text")
                st.write("**Feature Analysis:**")
                st.text_area("Extracted Features:", result, height=150)
        
        return result