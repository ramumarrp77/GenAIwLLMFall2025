import streamlit as st
from snowflake_connection import execute_rag_query, call_cortex_complete

class RAGAgent:
    def __init__(self):
        self.name = "Review Analysis Specialist"
        self.model = "claude-3-5-sonnet"
        self.icon = "📊"
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Execute RAG query on iPhone reviews"""
        
        # Step 1: Retrieve relevant reviews using vector similarity
        retrieved_reviews = execute_rag_query(user_query)
        
        if show_backend:
            st.write(f"{self.icon} **{self.name}** (RAG + Vector Search)")
            with st.expander("🔧 RAG Agent - Step 1: Vector Search", expanded=False):
                st.write("**Query Embedding Process:**")
                st.code(f"SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', '{user_query}')")
                st.write("**Vector Similarity Query:**")
                st.code(f"""
WITH user_query AS (
    SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024('snowflake-arctic-embed-l-v2.0', '{user_query}') as query_embedding
),
relevant_reviews AS (
    SELECT REVIEWTITLE, REVIEWDESCRIPTION, RATINGSCORE,
           VECTOR_COSINE_SIMILARITY(REVIEW_EMBEDDINGS::VECTOR(FLOAT, 1024), query_embedding) AS similarity
    FROM LAB_DB.PUBLIC.IPHONE_TABLE
    ORDER BY similarity DESC LIMIT 5
)""", language="sql")
                st.write("**Retrieved Reviews:**")
                st.text_area("Raw Retrieved Data:", retrieved_reviews[:500] + "..." if len(retrieved_reviews) > 500 else retrieved_reviews, height=150)
        else:
            st.write(f"{self.icon} **{self.name}** (RAG + Vector Search)")

        # Step 2: Generate analysis using retrieved context
        analysis_prompt = f"""You are a Review Analysis Specialist. Analyze customer feedback strictly based on retrieved data.

Retrieved iPhone reviews: {retrieved_reviews}

User question: {user_query}

Provide structured analysis:
- Summary: [Brief overview of customer sentiment]
- Key Issues: [Main problems mentioned]
- Positive Aspects: [What customers liked]  
- Overall Rating Trend: [Rating pattern from reviews]

Return ONLY the structured analysis, no additional text."""

        with st.spinner(f"{self.icon} RAG Agent analyzing reviews..."):
            analysis_result = call_cortex_complete(analysis_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 RAG Agent - Step 2: Analysis Generation", expanded=False):
                st.write("**Analysis Prompt:**")
                st.code(analysis_prompt, language="text")
                st.write("**Model Used:** claude-3-5-sonnet")
                st.write("**Analysis Result:**")
                st.text_area("Generated Analysis:", analysis_result, height=200)
        
        st.success(f"✅ {self.name} completed RAG analysis")
        return analysis_result