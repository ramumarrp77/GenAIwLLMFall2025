import streamlit as st
import requests
import os
from utils.snowflake_connection import call_cortex_complete

class NewsAgent:
    def __init__(self):
        self.name = "News Context Specialist"
        self.icon = "📰"
        self.model = "mixtral-8x7b"
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Fetch recent iPhone news using SerpAPI"""
        
        # Extract search terms
        search_prompt = f"""Extract iPhone-related search keywords from: {user_query}
Return ONLY the search keywords, no additional text."""
        
        search_terms = call_cortex_complete(search_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 News Agent - Backend Process", expanded=False):
                st.write("**Step 1: Search Term Extraction**")
                st.write(f"Extracted terms: {search_terms}")
                st.write("**Step 2: SerpAPI Call**")
                st.code(f"Query: iPhone {search_terms} news recent")
        
        # Fetch news from SerpAPI
        news_data = self._fetch_news(search_terms)
        
        # Analyze news with LLM
        analysis_prompt = f"""You are a News Context Specialist. Summarize this iPhone news data.

News data: {news_data}
User query: {user_query}

Provide brief news summary:
- Recent Updates: [Key news points]
- Relevant Context: [How this relates to user query]

Return ONLY the news summary, no additional text."""

        result = call_cortex_complete(analysis_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 News Agent - Backend Process", expanded=False):
                st.write("**Raw News Data:**")
                st.text_area("SerpAPI Results:", news_data[:300] + "...", height=100)
                st.write("**News Analysis:**")
                st.text_area("Analysis:", result, height=150)
        
        return result
    
    def _fetch_news(self, search_terms: str) -> str:
        """Fetch news from SerpAPI"""
        if not self.serpapi_key:
            return "SerpAPI key not configured"
        
        try:
            params = {
                "api_key": self.serpapi_key,
                "engine": "google",
                "q": f"iPhone {search_terms} news recent",
                "num": 5,
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            
            if response.status_code != 200:
                return f"SerpAPI Error: {response.status_code}"
            
            data = response.json()
            news_items = []
            
            if "organic_results" in data:
                for result in data["organic_results"][:5]:
                    if "snippet" in result:
                        news_items.append(f"{result.get('title', 'No title')}: {result['snippet']}")
            
            return " | ".join(news_items) if news_items else "No news found"
        except Exception as e:
            return f"Error: {e}"