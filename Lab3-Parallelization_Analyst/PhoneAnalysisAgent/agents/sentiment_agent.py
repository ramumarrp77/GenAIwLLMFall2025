import streamlit as st
from utils.snowflake_connection import execute_sentiment_analysis

class SentimentAgent:
    def __init__(self):
        self.name = "Sentiment Analysis Specialist"
        self.icon = "😊"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Execute sentiment analysis using Snowflake SENTIMENT() function"""
        
        if show_backend:
            with st.expander("🔧 Sentiment Agent - Backend Process", expanded=False):
                st.write("**Method:** Snowflake CORTEX.SENTIMENT()")
                st.write("**Query:**")
                st.code(f"""
SELECT 
    SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION) as sentiment_score,
    RATINGSCORE,
    COUNT(*) as review_count
FROM LAB_DB.PUBLIC.IPHONE_TABLE
WHERE REVIEWDESCRIPTION ILIKE '%{user_query}%'
GROUP BY SNOWFLAKE.CORTEX.SENTIMENT(REVIEWDESCRIPTION), RATINGSCORE
ORDER BY sentiment_score DESC
""", language="sql")
        
        result = execute_sentiment_analysis(user_query)
        
        if show_backend:
            with st.expander("🔧 Sentiment Agent - Backend Process", expanded=False):
                st.write("**Raw Sentiment Results:**")
                st.text_area("Sentiment Data:", result[:300] + "..." if len(result) > 300 else result, height=150)
        
        return result