# Calendar Tool - 3-Stage Pattern

from utils.snowflake_connection import call_llm
from utils.mock_data import get_mock_calendar_data, find_common_slots
import json
import re

# STAGE 1: Parameter Extraction
def extract_calendar_parameters(user_query, context):
    """
    LLM extracts attendees and date from user query
    """
    
    prompt = f"""Extract calendar check parameters from this query.

User query: "{user_query}"

Context:
- Current attendees: {context.get('attendees', [])}
- Date preference: {context.get('date_preference', 'not set')}

Extract attendee emails and date. Return ONLY JSON:
{{
  "attendees": ["email1", "email2"],
  "date": "date string"
}}

Response:"""

    response = call_llm(prompt)
    
    # Parse JSON
    if "```" in response:
        response = response.replace("```json", "").replace("```", "").strip()
    
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        params = json.loads(json_match.group())
    else:
        params = {
            "attendees": context.get('attendees', []),
            "date": context.get('date_preference', 'October 19')
        }
    
    return params


# STAGE 2: API Call (Mock)
def call_calendar_api(params):
    """
    Check calendar availability using mock data
    """
    
    attendees = params.get('attendees', [])
    date = params.get('date')
    
    availability_data = find_common_slots(attendees, date)
    
    return availability_data


# STAGE 3: Format Result
def format_calendar_result(api_response, user_query):
    """
    LLM formats calendar data to natural language
    """
    
    prompt = f"""Format this calendar availability data naturally.

Calendar data: {json.dumps(api_response, indent=2)}
User asked: "{user_query}"

Write a friendly summary showing:
1. Individual busy times
2. Common free slots
3. Recommended time

Response:"""

    formatted = call_llm(prompt)
    return formatted


# MAIN FUNCTION: Executes all 3 stages
def check_availability(user_query, context):
    """
    Complete 3-stage calendar check
    
    Stage 1: Extract params
    Stage 2: Call API
    Stage 3: Format result
    """
    
    # Stage 1
    params = extract_calendar_parameters(user_query, context)
    
    # Stage 2
    api_result = call_calendar_api(params)
    
    # Stage 3
    formatted_result = format_calendar_result(api_result, user_query)
    
    return {
        'raw': api_result,
        'formatted': formatted_result,
        'params_used': params
    }