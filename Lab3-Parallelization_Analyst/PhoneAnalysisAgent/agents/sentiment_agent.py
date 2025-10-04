import streamlit as st
from utils.snowflake_connection import execute_sentiment_analysis, call_cortex_complete

class SentimentAgent:
    def __init__(self):
        self.name = "Sentiment Analysis Specialist"
        self.icon = "😊"
        self.model = "claude-3-5-sonnet"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Execute sentiment analysis using Snowflake SENTIMENT() function"""
        
        # Step 1: Extract keywords from user query using LLM
        keyword_extraction_prompt = f"""You are a Keyword Extraction Specialist. Extract iPhone-related keywords from this query.

User query: {user_query}

Extract 3-5 relevant keywords for searching iPhone reviews.
Return ONLY the keywords separated by commas, no additional text.

Example: "battery, performance, charging, life"
"""
        
        keywords = call_cortex_complete(keyword_extraction_prompt, self.model)
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        
        if show_backend:
            with st.expander("🔧 Sentiment Agent - Step 1: Keyword Extraction", expanded=False):
                st.write("**Keyword Extraction Prompt:**")
                st.code(keyword_extraction_prompt, language="text")
                st.write(f"**Extracted Keywords:** {keyword_list}")
        
        # Step 2: Execute sentiment analysis with multiple keywords
        result = execute_sentiment_analysis(user_query, keyword_list)
        
        if show_backend:
            with st.expander("🔧 Sentiment Agent - Step 2: Sentiment Analysis", expanded=False):
                st.write("**Snowflake SENTIMENT() Query:**")
                ilike_conditions = " OR ".join([f"REVIEWDESCRIPTION ILIKE '%{kw}%'" for kw in keyword_list])
                st.code(f"""
SELECT 
    SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) as sentiment_score,
    CASE 
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) > 0.3 THEN 'Positive'
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) < -0.3 THEN 'Negative'
        ELSE 'Neutral'
    END as sentiment_category,
    COUNT(*) as review_count
FROM LAB_DB.PUBLIC.IPHONE_TABLE
WHERE {ilike_conditions}
GROUP BY sentiment_score, sentiment_category
""", language="sql")
                st.write("**Sentiment Results:**")
                st.text_area("Analysis Output:", result, height=150)
        
        return result