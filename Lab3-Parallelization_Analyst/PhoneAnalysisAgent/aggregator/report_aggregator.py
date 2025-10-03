import streamlit as st
from utils.snowflake_connection import call_cortex_complete

class ReportAggregator:
    def __init__(self):
        self.name = "Report Synthesis Specialist"
        self.icon = "📊"
        self.model = "claude-3-5-sonnet"
        
    def aggregate(self, parallel_results: dict, user_query: str, show_backend: bool = False) -> str:
        """Aggregate all parallel agent results into comprehensive report"""
        
        aggregation_prompt = f"""You are a Report Synthesis Specialist. Combine these parallel analyses into a comprehensive iPhone review report.

User Query: {user_query}

Parallel Analysis Results:
- Sentiment Analysis: {parallel_results.get('sentiment', 'N/A')}
- Feature Extraction: {parallel_results.get('features', 'N/A')}
- News Context: {parallel_results.get('news', 'N/A')}
- Quality Issues: {parallel_results.get('quality', 'N/A')}

Create comprehensive report with:
- Executive Summary: [Overall findings]
- Sentiment Overview: [Key sentiment insights]
- Feature Analysis: [Feature-specific findings]
- Quality Concerns: [Main issues identified]
- Market Context: [Relevant news context]
- Recommendations: [Actionable insights]

Return ONLY the comprehensive report, no additional text."""

        if show_backend:
            with st.expander("🔧 Aggregator - Backend Process", expanded=False):
                st.write("**Aggregation Prompt:**")
                st.code(aggregation_prompt, language="text")
                st.write("**Input from 4 Parallel Agents:**")
                st.write(f"- Sentiment: {parallel_results.get('sentiment', 'N/A')[:100]}...")
                st.write(f"- Features: {parallel_results.get('features', 'N/A')[:100]}...")
                st.write(f"- News: {parallel_results.get('news', 'N/A')[:100]}...")
                st.write(f"- Quality: {parallel_results.get('quality', 'N/A')[:100]}...")
        
        with st.spinner(f"{self.icon} Aggregator synthesizing final report..."):
            final_report = call_cortex_complete(aggregation_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Aggregator - Backend Process", expanded=False):
                st.write("**Final Comprehensive Report:**")
                st.text_area("Aggregated Report:", final_report, height=250)
        
        return final_report