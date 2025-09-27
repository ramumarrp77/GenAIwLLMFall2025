import streamlit as st
import requests
import os
from snowflake_connection import call_cortex_complete

class NewsAgent:
    def __init__(self):
        self.name = "iPhone News Analyst"
        self.model = "mixtral-8x7b"
        self.icon = "📰"
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Get latest iPhone news using SerpAPI"""
        
        if show_backend:
            st.write(f"{self.icon} **{self.name}** (SerpAPI)")
        else:
            st.write(f"{self.icon} **{self.name}** (SerpAPI)")
        
        # Step 1: Extract search terms from user query
        search_extraction_prompt = f"""You are a Search Query Specialist. Extract iPhone-related search keywords from this query.

User query: {user_query}

Extract search terms for finding recent iPhone news and information.
Return ONLY the search keywords, no additional text."""

        search_terms = call_cortex_complete(search_extraction_prompt, self.model)
        
        # Step 2: Call SerpAPI for recent news
        news_data = self._fetch_news_from_serpapi(search_terms)
        
        if show_backend:
            with st.expander("🔧 News Agent - Backend Process", expanded=False):
                st.write("**Step 1: Search Term Extraction**")
                st.code(search_extraction_prompt, language="text")
                st.write(f"**Extracted Search Terms:** {search_terms}")
                st.write("**Step 2: SerpAPI Call**")
                st.code(f"SerpAPI Query: iPhone {search_terms} news recent", language="text")
                st.write("**Raw News Data:**")
                st.text_area("SerpAPI Results:", str(news_data)[:500] + "..." if len(str(news_data)) > 500 else str(news_data), height=150)
        
        # Step 3: Analyze and structure the news data
        analysis_prompt = f"""You are an iPhone News Analyst. Analyze this news data and provide structured summary.

Search query: {user_query}
News data from web: {news_data}

Provide structured news summary:
- Latest Updates: [Recent iPhone developments from the data]
- Key Information: [Important details found]
- Source Summary: [Brief summary of news sources]

Return ONLY the structured news summary, no additional text."""

        with st.spinner(f"{self.icon} News Agent analyzing latest information..."):
            news_result = call_cortex_complete(analysis_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 News Agent - Backend Process", expanded=False):
                st.write("**Step 3: News Analysis**")
                st.code(analysis_prompt, language="text")
                st.write("**Generated News Analysis:**")
                st.text_area("News Analysis Output:", news_result, height=200)
        
        st.success(f"✅ {self.name} completed news analysis")
        return news_result
    
    def _fetch_news_from_serpapi(self, search_terms: str) -> str:
        """Fetch news using SerpAPI"""
        if not self.serpapi_key:
            return "SerpAPI key not configured"
        
        try:
            # Construct search query
            query = f"iPhone {search_terms} news recent"
            
            params = {
                "api_key": self.serpapi_key,
                "engine": "google",
                "q": query,
                "num": 5,
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            
            if response.status_code != 200:
                return f"SerpAPI Error: HTTP {response.status_code}"
            
            data = response.json()
            news_snippets = []
            
            # Extract news snippets
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    if "snippet" in result:
                        news_snippets.append(f"Title: {result.get('title', 'No title')} - {result['snippet']}")
            
            return " | ".join(news_snippets) if news_snippets else "No recent news found"
            
        except Exception as e:
            return f"Error fetching news: {str(e)}"