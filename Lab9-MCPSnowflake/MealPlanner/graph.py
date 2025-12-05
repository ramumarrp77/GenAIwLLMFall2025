"""LangGraph state machine for nutrition MCP agent."""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import logging
import time

from mcp_client import SnowflakeMCPClient
from llm import SnowflakeCortexLLM
from tools import ToolMapper, ToolIntent

logger = logging.getLogger(__name__)

# Define state
class NutritionState(TypedDict):
    """State for nutrition MCP agent."""
    messages: List[BaseMessage]
    user_query: str
    discovered_tools: List[Dict[str, Any]]
    detected_intent: str
    selected_tool: str
    tool_args: Dict[str, Any]
    tool_result: Any
    analysis: str
    conversation_history: List[Dict[str, Any]]
    should_continue: bool
    execution_steps: List[Dict[str, Any]]

class NutritionMCPAgent:
    """LangGraph-based agent using MCP tools."""
    
    def __init__(self, mcp_client: SnowflakeMCPClient):
        self.mcp_client = mcp_client
        self.llm = SnowflakeCortexLLM(model="llama3.1-70b")
        self.graph = self._build_graph()
    
    def _log_step(self, state: NutritionState, step_name: str, status: str, details: str = "") -> NutritionState:
        """Log execution step."""
        step_info = {
            "step": step_name,
            "status": status,  # "running", "completed", "error"
            "details": details,
            "timestamp": time.time()
        }
        
        # Add to state
        steps = state.get("execution_steps", [])
        steps.append(step_info)
        
        logger.info(f"{step_name}: {status} - {details}")
        
        return {**state, "execution_steps": steps}
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine."""
        
        workflow = StateGraph(NutritionState)
        
        # Add nodes
        workflow.add_node("initialize_mcp", self.initialize_mcp)
        workflow.add_node("understand_query", self.understand_query)
        workflow.add_node("select_tool", self.select_tool)
        workflow.add_node("prepare_arguments", self.prepare_arguments)
        workflow.add_node("execute_tool", self.execute_tool)
        workflow.add_node("format_response", self.format_response)
        
        # Define edges
        workflow.add_edge(START, "initialize_mcp")
        workflow.add_edge("initialize_mcp", "understand_query")
        workflow.add_edge("understand_query", "select_tool")
        workflow.add_edge("select_tool", "prepare_arguments")
        workflow.add_edge("prepare_arguments", "execute_tool")
        workflow.add_edge("execute_tool", "format_response")
        
        # Conditional edge
        workflow.add_conditional_edges(
            "format_response",
            self.should_continue_routing,
            {
                "continue": "understand_query",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def initialize_mcp(self, state: NutritionState) -> NutritionState:
        """Initialize MCP connection and discover tools."""
        state = self._log_step(state, "Initialize MCP", "running", "Connecting to Snowflake MCP server...")
        
        try:
            self.mcp_client.initialize()
            tools = self.mcp_client.list_tools()
            
            discovered_tools = [
                {
                    "name": tool.name,
                    "title": tool.title,
                    "description": tool.description,
                    "input_schema": tool.input_schema
                }
                for tool in tools
            ]
            
            tool_names = ', '.join([t.name for t in tools])
            state = self._log_step(
                state, 
                "Initialize MCP", 
                "completed", 
                f"Discovered {len(tools)} tools: {tool_names}"
            )
            
            return {
                **state,
                "discovered_tools": discovered_tools
            }
            
        except Exception as e:
            state = self._log_step(state, "Initialize MCP", "error", str(e))
            return {
                **state,
                "analysis": f"Error: Failed to initialize MCP - {str(e)}",
                "should_continue": False
            }
    
    def understand_query(self, state: NutritionState) -> NutritionState:
        """Parse user query to understand intent."""
        query = state["user_query"]
        state = self._log_step(state, "Understand Query", "running", f"Analyzing: '{query}'")
        
        intent = ToolMapper.detect_intent(query)
        
        state = self._log_step(
            state, 
            "Understand Query", 
            "completed", 
            f"Detected intent: {intent.value}"
        )
        
        return {
            **state,
            "detected_intent": intent.value
        }
    
    def select_tool(self, state: NutritionState) -> NutritionState:
        """Select appropriate MCP tool based on intent."""
        state = self._log_step(state, "Select Tool", "running", "Mapping intent to MCP tool...")
        
        intent = ToolIntent(state["detected_intent"])
        tool_name = ToolMapper.get_tool_name(intent)
        
        state = self._log_step(
            state, 
            "Select Tool", 
            "completed", 
            f"Selected: {tool_name}"
        )
        
        return {
            **state,
            "selected_tool": tool_name
        }
    
    def prepare_arguments(self, state: NutritionState) -> NutritionState:
        """Prepare arguments for tool execution."""
        state = self._log_step(state, "Prepare Arguments", "running", "Extracting parameters from query...")
        
        query = state["user_query"]
        intent = ToolIntent(state["detected_intent"])
        
        # Extract parameters based on intent
        if intent == ToolIntent.SEARCH:
            args = ToolMapper.extract_search_params(query)
        elif intent == ToolIntent.CALCULATE:
            args = ToolMapper.extract_macro_params(query)
        elif intent == ToolIntent.SCORE:
            args = ToolMapper.extract_score_params(query)
        elif intent == ToolIntent.FILTER:
            args = ToolMapper.extract_filter_params(query)
        else:
            args = {"query": query}
        
        args_str = str(args)[:100] + "..." if len(str(args)) > 100 else str(args)
        state = self._log_step(
            state, 
            "Prepare Arguments", 
            "completed", 
            f"Arguments: {args_str}"
        )
        
        return {
            **state,
            "tool_args": args
        }
    
    def execute_tool(self, state: NutritionState) -> NutritionState:
        """Execute the selected MCP tool."""
        tool_name = state['selected_tool']
        state = self._log_step(
            state, 
            "Execute Tool", 
            "running", 
            f"Calling MCP tool '{tool_name}' via JSON-RPC 2.0..."
        )
        
        try:
            result = self.mcp_client.call_tool(
                state["selected_tool"],
                state["tool_args"]
            )
            
            if result.success:
                state = self._log_step(
                    state, 
                    "Execute Tool", 
                    "completed", 
                    f"Tool '{tool_name}' executed successfully"
                )
            else:
                state = self._log_step(
                    state, 
                    "Execute Tool", 
                    "error", 
                    f"Tool failed: {result.error}"
                )
            
            # Update conversation history
            history = state.get("conversation_history", [])
            history.append({
                "tool": state["selected_tool"],
                "args": state["tool_args"],
                "result": result.content if result.success else result.error,
                "success": result.success
            })
            
            return {
                **state,
                "tool_result": result,
                "conversation_history": history
            }
            
        except Exception as e:
            state = self._log_step(state, "Execute Tool", "error", str(e))
            return {
                **state,
                "tool_result": {"error": str(e)},
                "analysis": f"Error executing tool: {str(e)}",
                "should_continue": False
            }
    
    def format_response(self, state: NutritionState) -> NutritionState:
        """Format the response for user using Cortex LLM."""
        state = self._log_step(state, "Format Response", "running", "Using Cortex LLM to format results...")
        
        tool_result = state["tool_result"]
        
        if not tool_result.success:
            analysis = f"⚠️ Tool execution failed: {tool_result.error}"
        else:
            # Use LLM to format all responses in a friendly way
            analysis = self._format_with_llm(
                state["selected_tool"],
                tool_result.content,
                state["user_query"]
            )
        
        state = self._log_step(state, "Format Response", "completed", "Response formatted by LLM")
        
        return {
            **state,
            "analysis": analysis,
            "should_continue": False
        }
    
    def _format_with_llm(self, tool_name: str, tool_result: Any, user_query: str) -> str:
        """Use Cortex LLM to format results in a friendly way."""
        try:
            import json
            
            # Convert result to string for LLM
            if isinstance(tool_result, str):
                result_str = tool_result
            else:
                result_str = json.dumps(tool_result, indent=2)
            
            # Create prompt for formatting
            prompt = f"""You are a friendly nutrition assistant. The user asked: "{user_query}"

The system executed the '{tool_name}' tool and got these results:

{result_str}

Please format this data in a clear, friendly, and helpful way for the user. Include:
- A brief summary of what was found
- Key nutritional information presented clearly
- Relevant details from the results
- Any insights or recommendations

Keep it concise and easy to read."""

            # Call Cortex to format
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error formatting with LLM: {e}")
            return str(tool_result)
    
    def should_continue_routing(self, state: NutritionState) -> Literal["continue", "end"]:
        """Decide whether to continue or end."""
        return "continue" if state.get("should_continue", False) else "end"
    
    def run(self, query: str) -> Dict[str, Any]:
        """Execute the agent with a query."""
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "user_query": query,
            "discovered_tools": [],
            "detected_intent": "",
            "selected_tool": "",
            "tool_args": {},
            "tool_result": None,
            "analysis": "",
            "conversation_history": [],
            "should_continue": False,
            "execution_steps": []
        }
        
        final_state = self.graph.invoke(initial_state)
        return final_state