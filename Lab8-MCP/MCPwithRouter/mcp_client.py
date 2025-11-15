"""
MCP Client - Discovery & Routing Layer
Discovers tools from servers and routes requests
"""

from servers import DatabaseMCPServer, NewsMCPServer, LocationMCPServer
from utils import SNOWFLAKE_CONFIG
import os

class MCPClient:
    """
    MCP Client - Routes requests to appropriate servers
    Does NOT make decisions, just delivers messages
    """
    
    def __init__(self):
        self.servers = {}
        print("\n" + "="*70)
        print("[MCP CLIENT] Initializing...")
        print("="*70)
        self._initialize_servers()
    
    def _initialize_servers(self):
        """Initialize all MCP servers"""
        print("[MCP CLIENT] Creating and connecting to servers...")
        
        # Create servers
        database_server = DatabaseMCPServer("database-server", SNOWFLAKE_CONFIG)
        news_server = NewsMCPServer("news-server")
        location_server = LocationMCPServer("location-server")
        
        # Register servers
        self.servers = {
            "database-server": database_server,
            "news-server": news_server,
            "location-server": location_server
        }
        
        print(f"\n[MCP CLIENT] ✅ Connected to {len(self.servers)} servers")
        for server_name in self.servers.keys():
            print(f"[MCP CLIENT]    - {server_name}")
    
    def get_all_tools(self) -> list:
        """
        Discover all tools from all connected servers
        🌟 KEY METHOD: Dynamic discovery happens here!
        """
        print("\n" + "="*70)
        print("[MCP CLIENT] 🔍 DISCOVERY PHASE - Asking servers for capabilities")
        print("="*70)
        
        all_tools = []
        
        for server_name, server in self.servers.items():
            print(f"\n[MCP CLIENT] 📞 Querying {server_name}...")
            
            # Ask server what it can do
            tools = server.get_tool_descriptions()
            
            print(f"[MCP CLIENT] 📥 {server_name} responded with {len(tools)} tools:")
            
            for tool in tools:
                tool['server'] = server_name
                all_tools.append(tool)
                print(f"[MCP CLIENT]    ✓ {tool['name']}: {tool['description'][:50]}...")
        
        print(f"\n{'='*70}")
        print(f"[MCP CLIENT] 🎉 DISCOVERY COMPLETE")
        print(f"[MCP CLIENT] Total tools discovered: {len(all_tools)} from {len(self.servers)} servers")
        print("="*70)
        
        return all_tools
    
    def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> dict:
        """
        Route tool call to the appropriate server
        Client doesn't decide - just delivers the message
        """
        print("\n" + "="*70)
        print("[MCP CLIENT] 📤 ROUTING REQUEST")
        print("="*70)
        print(f"[MCP CLIENT] Target Server: {server_name}")
        print(f"[MCP CLIENT] Target Tool: {tool_name}")
        print(f"[MCP CLIENT] Arguments: {arguments}")
        
        # Check if server exists
        if server_name not in self.servers:
            print(f"[MCP CLIENT] ❌ Server {server_name} not found")
            return {"error": f"Server {server_name} not found"}
        
        # Get the server
        server = self.servers[server_name]
        
        # Call the tool on the server
        print(f"[MCP CLIENT] ⚙️ Forwarding request to {server_name}...")
        result = server.call_tool(tool_name, **arguments)
        
        print(f"\n[MCP CLIENT] 📥 Received response from {server_name}")
        if result.get('success'):
            print(f"[MCP CLIENT] ✅ Tool execution successful")
        else:
            print(f"[MCP CLIENT] ❌ Tool execution failed: {result.get('error', 'Unknown')}")
        
        return result
    
    def get_server_info(self) -> dict:
        """Get information about connected servers"""
        return {
            "total_servers": len(self.servers),
            "servers": list(self.servers.keys()),
            "total_tools": len(self.get_all_tools())
        }