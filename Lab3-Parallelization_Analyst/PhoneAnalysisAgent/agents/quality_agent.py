import streamlit as st
from utils.snowflake_connection import execute_cortex_search_quality, call_cortex_complete

class QualityAgent:
    def __init__(self):
        self.name = "Quality Issues Specialist"
        self.icon = "⚠️"
        self.model = "llama4-maverick"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Detect quality issues using Chain of Thought with Cortex Search"""
        
        # Step 1: Identify specific problems to investigate
        step1_prompt = f"""You are analyzing quality issues. What specific problems should we look for?

User query: {user_query}

List 3-5 specific quality problems or defects to investigate.
Return ONLY the problem keywords separated by commas."""

        problem_keywords = call_cortex_complete(step1_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Step 1: Problem Identification", expanded=False):
                st.write("**Problems to investigate:**", problem_keywords)
        
        # Step 2: Cortex Search for relevant problem reviews
        search_results = execute_cortex_search_quality(problem_keywords)
        
        if show_backend:
            with st.expander("🔧 Step 2: Cortex Search Retrieval", expanded=False):
                st.code(f"""SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'LAB_DB.PUBLIC.LAB3_CORTEX_SEARCH',
    '{{"query": "{problem_keywords}", "limit": 10}}'
)""", language="sql")
                st.text_area("Retrieved Reviews:", search_results[:300] + "...", height=100)
        
        # Step 3: Categorize problems
        step3_prompt = f"""Categorize these iPhone problems by type.

Reviews: {search_results}

Group problems into categories:
- Hardware Issues
- Software Issues  
- Design Issues
- Performance Issues

Return ONLY the categorized problems."""

        categorized_problems = call_cortex_complete(step3_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Step 3: Issue Categorization", expanded=False):
                st.text_area("Categorized Problems:", categorized_problems, height=120)
        
        # Step 4: Assess severity
        step4_prompt = f"""Assess severity of each problem category.

Categorized problems: {categorized_problems}

Rate each category:
- Critical (product-breaking)
- Moderate (annoying but usable)
- Minor (cosmetic/rare)

Return ONLY severity assessment."""

        severity_assessment = call_cortex_complete(step4_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Step 4: Severity Assessment", expanded=False):
                st.text_area("Severity Ratings:", severity_assessment, height=100)
        
        # Step 5: Analyze frequency
        step5_prompt = f"""Analyze how often each problem appears.

Problems: {categorized_problems}
Reviews analyzed: {search_results}

Determine frequency pattern.
Return ONLY frequency analysis."""

        frequency_analysis = call_cortex_complete(step5_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Step 5: Frequency Analysis", expanded=False):
                st.text_area("Frequency Patterns:", frequency_analysis, height=100)
        
        # Step 6: Final synthesis
        final_prompt = f"""Synthesize complete quality analysis.

Chain of thought results:
- Problems identified: {problem_keywords}
- Categories: {categorized_problems}
- Severity: {severity_assessment}
- Frequency: {frequency_analysis}

Create final quality report:
- Common Problems: [Main issues]
- Severity Assessment: [Critical/Moderate/Minor breakdown]
- Frequency: [How often problems occur]
- Recommendations: [What needs attention]

Return ONLY the structured quality report."""

        result = call_cortex_complete(final_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Step 6: Final Synthesis", expanded=False):
                st.code(final_prompt, language="text")
                st.text_area("Final Quality Report:", result, height=200)
        
        return result