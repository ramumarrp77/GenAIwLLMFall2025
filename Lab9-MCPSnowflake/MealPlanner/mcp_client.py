"""MCP Client for Snowflake MCP Server integration."""

import requests
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from config import SnowflakeConfig

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    title: str
    description: str
    input_schema: Dict[str, Any]
    type: Optional[str] = None

@dataclass
class MCPToolResult:
    """Result from MCP tool execution."""
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class SnowflakeMCPClient:
    """Client for interacting with Snowflake MCP Server via JSON-RPC 2.0."""
    
    def __init__(self, config: SnowflakeConfig):
        self.config = config
        self.endpoint = config.mcp_endpoint
        self.session = requests.Session()
        
        # Use PAT as Bearer token
        self.session.headers.update({
            'Authorization': f'Bearer {config.password}',
            'Content-Type': 'application/json'
        })
        
        self._request_id = 0
        self._initialized = False
        self._tools_cache: Optional[List[MCPTool]] = None
    
    def _next_request_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id
    
    def _make_rpc_call(
        self, 
        method: str, 
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make JSON-RPC 2.0 call to MCP server.
        
        Args:
            method: RPC method name (e.g., "initialize", "tools/list")
            params: Optional parameters for the method
            
        Returns:
            JSON-RPC response result
            
        Raises:
            Exception: If RPC call fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params or {}
        }
        
        logger.debug(f"MCP Request: {method}")
        
        try:
            response = self.session.post(
                self.endpoint,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Log the full response for debugging
            logger.debug(f"MCP Response: {json.dumps(result, indent=2)}")
            
            if "error" in result:
                error_msg = result['error'].get('message', 'Unknown error')
                error_code = result['error'].get('code', 'N/A')
                error_data = result['error'].get('data', {})
                logger.error(f"MCP Error Response: {json.dumps(result['error'], indent=2)}")
                raise Exception(f"MCP Error [{error_code}]: {error_msg} | Data: {error_data}")
            
            return result.get("result", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP request failed: {e}")
            raise Exception(f"Failed to call MCP server: {str(e)}")
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize MCP connection and negotiate protocol version.
        
        Returns:
            Server capabilities and info
        """
        if self._initialized:
            return {"status": "already_initialized"}
        
        result = self._make_rpc_call(
            "initialize",
            {"protocolVersion": "2025-06-18"}
        )
        
        self._initialized = True
        server_name = result.get('serverInfo', {}).get('name', 'Unknown')
        logger.info(f"MCP Server initialized: {server_name}")
        
        return result
    
    def list_tools(self, force_refresh: bool = False) -> List[MCPTool]:
        """
        Discover available MCP tools.
        
        Args:
            force_refresh: Force refresh of tool cache
            
        Returns:
            List of available tools
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache
        
        result = self._make_rpc_call("tools/list", {})
        
        tools = []
        for tool_data in result.get("tools", []):
            tool = MCPTool(
                name=tool_data.get("name", ""),
                title=tool_data.get("title", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                type=tool_data.get("type")
            )
            tools.append(tool)
        
        self._tools_cache = tools
        logger.info(f"Discovered {len(tools)} MCP tools")
        
        return tools
    
    def call_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """
        Invoke an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            result = self._make_rpc_call(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            # Parse result content
            content = result.get("content", [])
            is_error = result.get("isError", False)
            
            # Extract content based on type
            parsed_content = None
            
            # Try to extract text content first
            text_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_content.append(item.get("text", ""))
            
            if text_content:
                # Combine text content
                combined_text = "\n".join(text_content)
                # Try to parse as JSON if it looks like JSON
                try:
                    parsed_content = json.loads(combined_text)
                except:
                    parsed_content = combined_text
            else:
                # No text content, return the full result
                parsed_content = result
            
            return MCPToolResult(
                success=not is_error,
                content=parsed_content,
                error=str(parsed_content) if is_error else None,
                metadata={"raw_result": result}
            )
            
        except Exception as e:
            error_details = str(e)
            logger.error(f"Tool execution failed: {error_details}")
            
            # Try to extract more details from the error
            try:
                import traceback
                full_traceback = traceback.format_exc()
                logger.error(f"Full traceback: {full_traceback}")
            except:
                pass
            
            return MCPToolResult(
                success=False,
                content=None,
                error=f"MCP Error: {error_details}"
            )
    
    def get_tool_by_name(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool definition by name."""
        tools = self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def close(self):
        """Close MCP client session."""
        self.session.close()
        logger.info("MCP client session closed")