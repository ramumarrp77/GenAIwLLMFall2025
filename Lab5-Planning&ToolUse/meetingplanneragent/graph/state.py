# State definition for Meeting Planner (Multi-tool support)

from typing import Annotated, Dict, List, Optional, TypedDict, Any
from langgraph.graph.message import add_messages

class State(TypedDict):
    """State for the meeting planner chatbot agent"""
    
    # Conversation history
    messages: Annotated[List, add_messages]
    
    # Collected information (builds up over conversation)
    attendees: Optional[List[str]]  # Email addresses
    date_preference: Optional[str]  # Date or day name
    duration: Optional[str]  # Duration in hours
    venue_preference: Optional[str]  # indoor/outdoor/any
    location: Optional[str]  # City/area (default: Boston, MA)
    
    # Tool orchestration (multi-tool support)
    tools_to_call: Optional[List[str]]  # Tools planned for THIS turn
    tools_called: Optional[List[str]]  # Tools called across ALL turns (history)
    tools_done_this_turn: Optional[List[str]]  # Tools completed THIS turn
    current_tool: Optional[str]  # Current active tool being processed
    tool_results: Optional[Dict]  # Results from all tools
    
    # Control flags
    need_final_answer: Optional[bool]  # Ready to generate final response
    ready_to_finalize: Optional[bool]  # Ready to send meeting invite