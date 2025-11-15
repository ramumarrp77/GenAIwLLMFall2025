"""
Location MCP Server - Thin MCP Protocol Wrapper
Only handles: Registration, Description, Routing
Business logic is in tools/location_tools.py
"""

import os
from tools import LocationTools

class LocationMCPServer:
    """
    MCP Server for Location operations
    Thin wrapper - delegates to LocationTools class
    """
    
    def __init__(self, name: str = "location-server"):
        self.name = name
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.location_tools = LocationTools(api_key)
        self._register_tools()
        
        print(f"\n[{self.name.upper()}] Server initializing...")
        print(f"[{self.name.upper()}] Registered {len(self.tools)} tools")
    
    def _register_tools(self):
        """Register tools from LocationTools class"""
        self.tools = {
            "find_nearest_store": self.location_tools.find_nearest_store,
            "get_directions": self.location_tools.get_directions,
            "get_store_details": self.location_tools.get_store_details
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
                "name": "find_nearest_store",
                "description": "Find nearest Apple Store to a location",
                "parameters": {"location": "string - city or address"}
            },
            {
                "name": "get_directions",
                "description": "Get directions from one place to another",
                "parameters": {
                    "origin": "string - starting location",
                    "destination": "string - ending location"
                }
            },
            {
                "name": "get_store_details",
                "description": "Get detailed information about an Apple Store",
                "parameters": {"store_name": "string - name of the store"}
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