# Synthesizer - Generate final meeting recommendation

from utils.snowflake_connection import call_llm

def synthesize_recommendation(state):
    """
    Synthesize all collected info and tool results into final recommendation
    
    Args:
        state: Complete state with all information and tool results
        
    Returns:
        String with final meeting recommendation
    """
    
    # Build context from all collected data
    attendees_text = ', '.join(state.get('attendees', []))
    
    calendar_info = state.get('calendar_results', {})
    slots_text = '\n'.join([
        f"- {slot['start_time']} to {slot['end_time']}"
        for slot in calendar_info.get('common_slots', [])
    ])
    
    weather_info = state.get('weather_results', {})
    weather_text = f"{weather_info.get('temperature', 'N/A')}, {weather_info.get('condition', 'N/A')}"
    
    venues_info = state.get('venue_results', {})
    venues_text = '\n'.join([
        f"- {venue['name']} ({venue['address']})"
        for venue in venues_info.get('venues', [])[:3]
    ])
    
    prompt = f"""Generate a final meeting recommendation based on all collected information.

Meeting Requirements:
- Attendees: {attendees_text}
- Date: {state.get('date_preference', 'Not specified')}
- Duration: {state.get('duration', '1 hour')}
- Venue preference: {state.get('venue_preference', 'any')}

Available Time Slots:
{slots_text}

Weather Forecast:
{weather_text}

Available Venues:
{venues_text}

Provide a clear, concise meeting recommendation that includes:
1. Recommended date and time
2. Recommended venue (pick the best one)
3. Brief justification

Keep it conversational and friendly.

Recommendation:"""

    recommendation = call_llm(prompt)
    
    return recommendation