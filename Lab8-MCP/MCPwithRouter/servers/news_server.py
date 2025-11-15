"""
News MCP Server - Thin MCP Protocol Wrapper
Only handles: Registration, Description, Routing
Business logic is in tools/news_tools.py
"""

import os
from tools import NewsTools

class NewsMCPServer:
    """
    MCP Server for News operations
    Thin wrapper - delegates to NewsTools class
    """
    
    def __init__(self, name: str = "news-server"):
        self.name = name
        api_key = os.getenv('SERPAPI_API_KEY')
        self.news_tools = NewsTools(api_key)
        self._register_tools()
        
        print(f"\n[{self.name.upper()}] Server initializing...")
        print(f"[{self.name.upper()}] Registered {len(self.tools)} tools")
    
    def _register_tools(self):
        """Register tools from NewsTools class"""
        self.tools = {
            "get_latest_news": self.news_tools.get_latest_news,
            "search_news": self.news_tools.search_news
        }
    
    def get_tool_descriptions(self) -> list:
        """
        MCP Protocol: Expose tool capabilities
        Client calls this during discovery phase
        """
        print(f"[{self.name.upper()}] Responding to discovery request...")
        print(f"[{self.name.upper()}] Exposing {len(self.tools)} tool descriptions")
        
        return [
            {
                "name": "get_latest_news",
                "description": "Get latest news articles about iPhones or Apple products",
                "parameters": {"topic": "string - what news to search for"}
            },
            {
                "name": "search_news",
                "description": "Search for news articles with specific keywords and time range",
                "parameters": {
                    "keyword": "string - search term",
                    "time_range": "string - e.g., 'past_day', 'past_week', 'past_month'"
                }
            }
        ]
    
    def call_tool(self, tool_name: str, **kwargs):
        """
        MCP Protocol: Execute a tool by name
        Server routes request to the actual tool function
        """
        print(f"\n[{self.name.upper()}] Received tool call: {tool_name}")
        print(f"[{self.name.upper()}] Arguments: {kwargs}")
        
        if tool_name not in self.tools:
            print(f"[{self.name.upper()}] ❌ Tool not found")
            return {"error": f"Tool {tool_name} not found"}
        
        print(f"[{self.name.upper()}] Routing to tool function...")
        result = self.tools[tool_name](**kwargs)
        
        print(f"[{self.name.upper()}] Tool execution complete")
        return result