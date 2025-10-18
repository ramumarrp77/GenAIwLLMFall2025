# Turn Planner - Strict conversation flow

from utils.snowflake_connection import call_llm
import json
import re

def plan_turn(state):
    """
    Planning agent with strict flow control
    """
    
    # Get what we have
    attendees = state.get('attendees', [])
    date_pref = state.get('date_preference')
    venue_pref = state.get('venue_preference')
    tools_done = state.get('tools_executed', [])
    
    # STRICT DECISION TREE
    
    # Step 1: Need attendees first
    if not attendees:
        return {
            'tools_to_use': [],
            'next_question': 'Who would you like to invite? (Ram, Saliba, Gabriel)',
            'ready_to_finalize': False
        }
    
    # Step 2: Have attendees, check calendar (only once)
    if 'calendar_tool' not in tools_done:
        return {
            'tools_to_use': ['calendar_tool'],
            'next_question': None,  # Calendar tool will show availability
            'ready_to_finalize': False
        }
    
    # Step 3: Calendar done, need date confirmation
    if not date_pref:
        return {
            'tools_to_use': [],
            'next_question': 'Which date and time works best for you?',
            'ready_to_finalize': False
        }
    
    # Step 4: Have date, need venue preference
    if not venue_pref:
        return {
            'tools_to_use': [],
            'next_question': 'Would you prefer an indoor or outdoor venue?',
            'ready_to_finalize': False
        }
    
    # Step 5: Have venue pref, check weather and search venues (only once)
    if 'weather_tool' not in tools_done or 'places_tool' not in tools_done:
        tools_needed = []
        if 'weather_tool' not in tools_done:
            tools_needed.append('weather_tool')
        if 'places_tool' not in tools_done:
            tools_needed.append('places_tool')
        
        return {
            'tools_to_use': tools_needed,
            'next_question': None,  # Tools will provide info
            'ready_to_finalize': False
        }
    
    # Step 6: Everything done, ready to finalize
    return {
        'tools_to_use': [],
        'next_question': 'Would you like me to finalize and send the meeting invite?',
        'ready_to_finalize': True
    }