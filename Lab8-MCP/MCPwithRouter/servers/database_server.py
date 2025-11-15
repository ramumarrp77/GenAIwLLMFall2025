"""
Database MCP Server - Thin MCP Protocol Wrapper
Only handles: Registration, Description, Routing
Business logic is in tools/database_tools.py
"""

from tools import DatabaseTools

class DatabaseMCPServer:
    """
    MCP Server for Database operations
    Thin wrapper - delegates to DatabaseTools class
    """
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.db_tools = DatabaseTools(config)
        self._register_tools()
        
        print(f"\n[{self.name.upper()}] Server initializing...")
        print(f"[{self.name.upper()}] Registered {len(self.tools)} tools")
    
    def _register_tools(self):
        """Register tools from DatabaseTools class"""
        self.tools = {
            "search_reviews_rag": self.db_tools.search_reviews_rag,
            "analyze_sentiment": self.db_tools.analyze_sentiment,
            "get_table_info": self.db_tools.get_table_info,
            "query_database": self.db_tools.query_database
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
                "name": "search_reviews_rag",
                "description": "Search iPhone reviews using semantic/vector search. Best for questions about features, quality, user opinions.",
                "parameters": {"query": "string - what to search for in reviews"}
            },
            {
                "name": "analyze_sentiment",
                "description": "Analyze overall sentiment of reviews for a specific topic",
                "parameters": {"topic": "string - topic to analyze sentiment for"}
            },
            {
                "name": "get_table_info",
                "description": "Get information about available tables and their structure",
                "parameters": {}
            },
            {
                "name": "query_database",
                "description": "Execute direct SQL query on database",
                "parameters": {"sql": "string - SQL query to execute"}
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