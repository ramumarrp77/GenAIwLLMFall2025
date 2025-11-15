"""
News Tools - SerpAPI Operations
Uses requests library (matching your existing pattern)
"""

import requests

class NewsTools:
    """
    News operations tools
    Handles SerpAPI news retrieval using raw requests
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("[NEWS TOOLS] Initialized with SerpAPI")
    
    def get_latest_news(self, topic: str) -> dict:
        """Get latest news about a topic"""
        print(f"\n[NEWS TOOL] get_latest_news")
        print(f"[NEWS TOOL] Topic: {topic}")
        
        if not self.api_key:
            print(f"[NEWS TOOL] ❌ API key not configured")
            return {"success": False, "error": "SerpAPI key not configured"}
        
        try:
            query = f"{topic} iPhone news recent"
            
            params = {
                "api_key": self.api_key,
                "engine": "google",
                "q": query,
                "num": 5,
                "gl": "us",
                "hl": "en",
                "tbm": "nws"  # News search
            }
            
            print(f"[NEWS TOOL] Calling SerpAPI...")
            response = requests.get("https://serpapi.com/search", params=params)
            
            if response.status_code != 200:
                print(f"[NEWS TOOL] ❌ SerpAPI Error: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            # Extract news results
            formatted_results = []
            
            if "news_results" in data:
                for article in data["news_results"][:5]:
                    formatted_results.append({
                        "title": article.get("title", ""),
                        "snippet": article.get("snippet", ""),
                        "source": article.get("source", ""),
                        "date": article.get("date", ""),
                        "link": article.get("link", "")
                    })
            
            print(f"[NEWS TOOL] ✅ Found {len(formatted_results)} news articles")
            for i, article in enumerate(formatted_results, 1):
                print(f"[NEWS TOOL]    {i}. {article['title'][:60]}...")
            
            return {
                "success": True,
                "articles": formatted_results,
                "count": len(formatted_results)
            }
            
        except Exception as e:
            print(f"[NEWS TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_news(self, keyword: str, time_range: str = "past_week") -> dict:
        """Search news with specific time range"""
        print(f"\n[NEWS TOOL] search_news")
        print(f"[NEWS TOOL] Keyword: {keyword}")
        print(f"[NEWS TOOL] Time Range: {time_range}")
        
        if not self.api_key:
            print(f"[NEWS TOOL] ❌ API key not configured")
            return {"success": False, "error": "SerpAPI key not configured"}
        
        try:
            params = {
                "api_key": self.api_key,
                "engine": "google",
                "q": keyword,
                "num": 5,
                "gl": "us",
                "hl": "en",
                "tbm": "nws",
                "tbs": f"qdr:{time_range.replace('past_', '')}"
            }
            
            print(f"[NEWS TOOL] Calling SerpAPI with time filter...")
            response = requests.get("https://serpapi.com/search", params=params)
            
            if response.status_code != 200:
                print(f"[NEWS TOOL] ❌ SerpAPI Error: HTTP {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            formatted_results = []
            
            if "news_results" in data:
                for article in data["news_results"][:5]:
                    formatted_results.append({
                        "title": article.get("title", ""),
                        "snippet": article.get("snippet", ""),
                        "source": article.get("source", ""),
                        "date": article.get("date", ""),
                        "link": article.get("link", "")
                    })
            
            print(f"[NEWS TOOL] ✅ Found {len(formatted_results)} articles")
            for i, article in enumerate(formatted_results, 1):
                print(f"[NEWS TOOL]    {i}. {article['title'][:60]}...")
            
            return {
                "success": True,
                "articles": formatted_results,
                "count": len(formatted_results)
            }
            
        except Exception as e:
            print(f"[NEWS TOOL] ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}