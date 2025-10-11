# State definition for LangGraph

from typing import TypedDict, List, Dict, Any

class State(TypedDict):
    """State that flows through the LangGraph workflow"""
    
    # Inputs
    uploaded_file: Any
    job_url: str
    max_iterations: int
    quality_threshold: float
    
    # Extracted data
    resume_text: str
    job_text: str
    contact_info: Dict  # Automatically extracted from resume (name, email, phone, address)
    
    # Generated content (grows with each iteration)
    drafts: List[str]
    critiques: List[Dict]
    
    # Tracking
    current_iteration: int
    stop_reason: str