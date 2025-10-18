# LangGraph workflow - MULTIPLE TOOLS PER TURN

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from .state import State
from .nodes import (
    controller_node,
    calendar_tool_node,
    weather_tool_node,
    places_tool_node,
    email_tool_node,
    answer_generator_node,
    _route_to_next_node,
    _check_more_tools_this_turn
)


def create_workflow():
    """
    Workflow supporting MULTIPLE tools per turn.
    
    Flow:
    controller → tool1 → [more tools?] → tool2 → [more tools?] → answer → END
    """
    
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("controller", controller_node)
    workflow.add_node("calendar_tool_node", calendar_tool_node)
    workflow.add_node("weather_tool_node", weather_tool_node)
    workflow.add_node("places_tool_node", places_tool_node)
    workflow.add_node("email_tool_node", email_tool_node)
    workflow.add_node("answer_generator", answer_generator_node)
    
    # START → controller
    workflow.add_edge(START, "controller")
    
    # Controller routes to first tool OR answer
    workflow.add_conditional_edges(
        "controller",
        _route_to_next_node,
        {
            "calendar_tool_node": "calendar_tool_node",
            "weather_tool_node": "weather_tool_node",
            "places_tool_node": "places_tool_node",
            "email_tool_node": "email_tool_node",
            "answer_generator": "answer_generator"
        }
    )
    
    # CRITICAL: After each tool, check if more tools needed THIS turn
    # All tools can route to any other tool or answer_generator
    all_tool_routes = {
        "calendar_tool_node": "calendar_tool_node",
        "weather_tool_node": "weather_tool_node",
        "places_tool_node": "places_tool_node",
        "email_tool_node": "email_tool_node",
        "answer_generator": "answer_generator"
    }
    
    workflow.add_conditional_edges("calendar_tool_node", _check_more_tools_this_turn, all_tool_routes)
    workflow.add_conditional_edges("weather_tool_node", _check_more_tools_this_turn, all_tool_routes)
    workflow.add_conditional_edges("places_tool_node", _check_more_tools_this_turn, all_tool_routes)
    workflow.add_conditional_edges("email_tool_node", _check_more_tools_this_turn, all_tool_routes)
    
    # Answer → END
    workflow.add_edge("answer_generator", END)
    
    return workflow.compile()


def run_conversation_turn(user_message, current_state):
    """Run one turn - extract info first, then execute graph"""
    
    print(f"\n{'='*60}")
    print(f"NEW TURN: {user_message[:50]}...")
    print(f"{'='*60}")
    
    # Preserve state
    preserved_state = {
        'messages': current_state.get('messages', []),
        'attendees': current_state.get('attendees'),
        'date_preference': current_state.get('date_preference'),
        'duration': current_state.get('duration'),
        'venue_preference': current_state.get('venue_preference'),
        'location': current_state.get('location', 'Boston, MA'),
        'tools_to_call': [],  # Reset each turn
        'tools_called': current_state.get('tools_called', []),  # Keep history
        'tools_done_this_turn': [],  # Reset each turn
        'current_tool': None,
        'tool_results': current_state.get('tool_results', {}),
        'need_final_answer': None,
        'ready_to_finalize': False
    }
    
    # Add user message
    preserved_state['messages'].append(HumanMessage(content=user_message))
    
    # Extract info BEFORE graph
    _extract_info_from_message(user_message, preserved_state)
    
    print(f"[DEBUG] State after extraction:")
    print(f"  Attendees: {preserved_state.get('attendees')}")
    print(f"  Date: {preserved_state.get('date_preference')}")
    print(f"  Venue: {preserved_state.get('venue_preference')}")
    print(f"  Tools called (all time): {preserved_state.get('tools_called')}")
    
    try:
        app = create_workflow()
        
        # Run graph
        final_state = app.invoke(preserved_state)
        
        # Merge results
        result_state = {**preserved_state, **final_state}
        
        # Safety checks
        if not result_state.get('tools_called'):
            result_state['tools_called'] = []
        if not result_state.get('tool_results'):
            result_state['tool_results'] = {}
        
        return result_state
    
    except Exception as e:
        print(f"[ERROR] Workflow: {e}")
        import traceback
        traceback.print_exc()
        
        preserved_state['messages'].append(
            AIMessage(content=f"Error: {str(e)}. Please try again.")
        )
        return preserved_state


def _extract_info_from_message(user_message, state):
    """Extract info from user message - updates state in-place"""
    from utils.snowflake_connection import call_llm
    import json
    import re
    
    NAME_TO_EMAIL = {
        'ram': 'ramkumarrp16077@gmail.com',
        'saliba': 'ramasamypandiaraj.r@northeastern.edu',
        'salliba': 'ramasamypandiaraj.r@northeastern.edu',
        'gabriel': 'ramgeon243@gmail.com'
    }
    
    prompt = f"""Extract meeting information from the user's message.

User: "{user_message}"

Current:
- Attendees: {state.get('attendees', 'None')}
- Date: {state.get('date_preference', 'None')}
- Duration: {state.get('duration', 'None')}
- Venue: {state.get('venue_preference', 'None')}

Extract NEW info. Return ONLY JSON:
{{
  "attendee_names": ["name1"] or null,
  "date_preference": "date/time" or null,
  "duration": "X hour(s)" or null,
  "venue_preference": "indoor/outdoor/any" or null
}}

Response:"""
    
    try:
        response = call_llm(prompt)
        
        if "```" in response:
            response = response.replace("```json", "").replace("```", "").strip()
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group())
        else:
            extracted = json.loads(response)
        
        # Update ONLY if new AND field empty
        if extracted.get('attendee_names') and not state.get('attendees'):
            emails = [NAME_TO_EMAIL.get(name.lower(), f"{name.lower()}@email.com") 
                     for name in extracted['attendee_names']]
            state['attendees'] = emails
            print(f"[DEBUG] Extracted attendees: {emails}")
        
        if extracted.get('date_preference') and not state.get('date_preference'):
            state['date_preference'] = extracted['date_preference']
            print(f"[DEBUG] Extracted date: {extracted['date_preference']}")
        
        if extracted.get('duration') and not state.get('duration'):
            state['duration'] = extracted['duration']
            print(f"[DEBUG] Extracted duration: {extracted['duration']}")
        
        if extracted.get('venue_preference') and not state.get('venue_preference'):
            state['venue_preference'] = extracted['venue_preference']
            print(f"[DEBUG] Extracted venue: {extracted['venue_preference']}")
    
    except Exception as e:
        print(f"[DEBUG] Extraction error: {e}")