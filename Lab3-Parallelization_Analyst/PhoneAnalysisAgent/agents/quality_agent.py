import streamlit as st
from utils.snowflake_connection import call_cortex_complete, execute_quality_search

class QualityAgent:
    def __init__(self):
        self.name = "Quality Issues Specialist"
        self.icon = "⚠️"
        self.model = "llama4-maverick"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Detect quality issues and problems in reviews"""
        
        # Get reviews related to query
        quality_reviews = execute_quality_search(user_query)
        
        if show_backend:
            with st.expander("🔧 Quality Agent - Backend Process", expanded=False):
                st.write("**Method:** LLM Problem Detection")
                st.write("**Retrieved Reviews:**")
                st.text_area("Review Data:", quality_reviews[:300] + "...", height=100)
        
        # Analyze for quality issues
        quality_prompt = f"""You are a Quality Issues Specialist. Identify problems and defects from these iPhone reviews.

Reviews: {quality_reviews}
User query: {user_query}

Analyze and extract:
- Common Problems: [Most frequently mentioned issues]
- Severity: [Critical/Moderate/Minor issues]
- Affected Features: [Which features have problems]
- Frequency: [How often each issue appears]

Return ONLY the structured quality analysis, no additional text."""

        result = call_cortex_complete(quality_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Quality Agent - Backend Process", expanded=False):
                st.write("**Quality Analysis Prompt:**")
                st.code(quality_prompt, language="text")
                st.write("**Model:** llama4-maverick")
                st.write("**Quality Issues Found:**")
                st.text_area("Analysis:", result, height=150)
        
        return result