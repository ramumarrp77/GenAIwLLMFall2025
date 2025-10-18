# Conversation Analyzer - Extract information from user messages
# (Simplified version - most logic now in workflow._update_state_from_conversation)

from utils.snowflake_connection import call_llm
import json
import re

# Map names to emails
NAME_TO_EMAIL = {
    'ram': 'ramkumarrp16077@gmail.com',
    'saliba': 'ramasamypandiaraj.r@northeastern.edu',
    'salliba': 'ramasamypandiaraj.r@northeastern.edu',
    'gabriel': 'ramgeon243@gmail.com'
}

def analyze_user_input(user_message, current_state):
    """
    Analyze user message and extract meeting information.
    
    This function is kept for backward compatibility but most extraction
    logic now happens in the controller and workflow nodes.
    
    Args:
        user_message: Latest user message
        current_state: Current conversation state
        
    Returns:
        Dict with extracted information
    """
    
    prompt = f"""Analyze this user message and extract meeting-related information.

User message: "{user_message}"

Current collected info:
- Attendees: {current_state.get('attendees', [])}
- Date: {current_state.get('date_preference', 'Not set')}
- Duration: {current_state.get('duration', 'Not set')}
- Venue preference: {current_state.get('venue_preference', 'Not set')}

Extract any NEW information from the user message. Return ONLY a JSON object:
{{
  "attendee_names": ["name1", "name2"] or null (extract just first names),
  "date_preference": "date string or day name" or null,
  "duration": "X hour(s)" or null,
  "venue_preference": "indoor/outdoor/any" or null
}}

If user is confirming/saying yes, return all nulls.

Response:"""

    response = call_llm(prompt)
    
    # Parse JSON
    try:
        if "```" in response:
            response = response.replace("```json", "").replace("```", "").strip()
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group())
        else:
            extracted = json.loads(response)
        
        # Convert names to emails
        if extracted.get('attendee_names'):
            emails = []
            for name in extracted['attendee_names']:
                email = NAME_TO_EMAIL.get(name.lower(), f"{name.lower()}@email.com")
                emails.append(email)
            extracted['attendees'] = emails
        else:
            extracted['attendees'] = None
        
        return extracted
    
    except Exception as e:
        return {
            'attendees': None,
            'date_preference': None,
            'duration': None,
            'venue_preference': None
        }