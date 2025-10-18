# Tool Orchestrator - Executes tools using 3-stage pattern

from tools import check_availability, get_weather_forecast, search_venues, send_meeting_invite

def orchestrate_tools(tools_to_use, state):
    """
    Execute selected tools using 3-stage pattern
    Each tool: LLM extracts params → API call → LLM formats result
    
    Args:
        tools_to_use: List of tool names to execute
        state: Current state (used as context)
        
    Returns:
        Dict with tool results
    """
    
    # Get user query from messages
    messages = state.get('messages', [])
    user_query = ""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            user_query = msg.get('content', '')
            break
    
    results = {}
    
    for tool_name in tools_to_use:
        
        print(f"\nExecuting {tool_name}...")
        
        if tool_name == 'calendar_tool':
            # 3-stage: extract → call → format
            result = check_availability(user_query, state)
            results['calendar_results'] = result
        
        elif tool_name == 'weather_tool':
            # 3-stage: extract → call → format
            result = get_weather_forecast(user_query, state)
            results['weather_results'] = result
        
        elif tool_name == 'places_tool':
            # 3-stage: extract → call → format
            result = search_venues(user_query, state)
            results['venue_results'] = result
        
        elif tool_name == 'email_tool':
            # 3-stage: extract → call → format
            result = send_meeting_invite(user_query, state)
            results['email_sent'] = result
    
    return results