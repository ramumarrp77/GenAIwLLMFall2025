# Places Tool - 3-Stage Pattern (Meeting Halls & Conference Rooms)

from utils.snowflake_connection import call_llm
from config import GOOGLE_MAPS_API_KEY
import requests
import json
import re

# STAGE 1: Parameter Extraction
def extract_places_parameters(user_query, context):
    """
    LLM extracts location and venue preferences.
    CRITICAL: Search for meeting rooms, conference centers, event venues.
    """
    
    prompt = f"""Extract venue search parameters from this query.

User query: "{user_query}"

Context:
- Location: {context.get('location', 'Boston')}
- Venue preference: {context.get('venue_preference', 'any')}

Extract parameters. Return ONLY JSON:
{{
  "location": "city name",
  "venue_type": "meeting_room",
  "indoor_outdoor": "indoor/outdoor/any"
}}

CRITICAL: venue_type should be "meeting_room" for conference/meeting venues.

Response:"""

    response = call_llm(prompt)
    
    # Parse JSON
    try:
        if "```" in response:
            response = response.replace("```json", "").replace("```", "").strip()
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            params = json.loads(json_match.group())
        else:
            params = json.loads(response)
        
        # FORCE venue_type to be meeting_room
        params["venue_type"] = "meeting_room"
        
        return params
    except:
        return {
            "location": context.get('location', 'Boston, MA'),
            "venue_type": "meeting_room",
            "indoor_outdoor": context.get('venue_preference', 'any')
        }


# STAGE 2: Google Maps API Call
def call_places_api(params):
    """
    Call Google Maps Places API for MEETING VENUES.
    Searches for: conference rooms, meeting spaces, event venues.
    """
    
    if not GOOGLE_MAPS_API_KEY:
        return {'error': 'Google Maps API key not configured in .env'}
    
    location = params.get('location', 'Boston, MA')
    indoor_outdoor = params.get('indoor_outdoor', 'any')
    
    try:
        # Step 1: Geocode location
        geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geocode_params = {
            'address': location,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        print(f"[DEBUG] Geocoding: {location}")
        geocode_response = requests.get(geocode_url, params=geocode_params)
        geocode_data = geocode_response.json()
        
        if geocode_data['status'] != 'OK':
            return {'error': f'Location not found: {location}. Status: {geocode_data["status"]}'}
        
        lat = geocode_data['results'][0]['geometry']['location']['lat']
        lng = geocode_data['results'][0]['geometry']['location']['lng']
        
        print(f"[DEBUG] Coordinates: {lat}, {lng}")
        
        # Step 2: Search for meeting venues
        # Google Places doesn't have a specific "meeting_room" type
        # We'll search for relevant keywords
        places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        # Determine search query based on preference
        if indoor_outdoor == 'outdoor':
            search_query = f"outdoor event venue near {location}"
        else:
            search_query = f"conference room meeting space event venue near {location}"
        
        places_params = {
            'query': search_query,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        print(f"[DEBUG] Calling Google Maps Places API with query: {search_query}")
        
        places_response = requests.get(places_url, params=places_params)
        places_data = places_response.json()
        
        print(f"[DEBUG] Places API status: {places_data.get('status')}")
        print(f"[DEBUG] Found {len(places_data.get('results', []))} results")
        
        if places_data['status'] == 'ZERO_RESULTS':
            # Fallback: try hotels with meeting facilities
            print("[DEBUG] No meeting venues found, trying hotels with meeting facilities...")
            places_params['query'] = f"hotel with conference room near {location}"
            places_response = requests.get(places_url, params=places_params)
            places_data = places_response.json()
        
        if places_data['status'] != 'OK':
            return {'error': f"Google Maps API error: {places_data.get('status')}"}
        
        # Step 3: Format results - Meeting venues
        venues = []
        for place in places_data.get('results', [])[:5]:
            venue_info = {
                'name': place.get('name', 'Unknown'),
                'address': place.get('formatted_address', 'Address not available'),
                'rating': place.get('rating', 'No rating'),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'types': place.get('types', []),
                'place_id': place.get('place_id', '')
            }
            venues.append(venue_info)
            print(f"[DEBUG] Venue: {venue_info['name']} - {venue_info['rating']} stars")
        
        return {
            'venues': venues,
            'count': len(venues),
            'location': f"{lat},{lng}",
            'search_query': search_query
        }
    
    except Exception as e:
        print(f"[DEBUG] Google Maps API exception: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


# STAGE 3: Format Result
def format_places_result(api_response, user_query):
    """
    LLM formats ACTUAL venue data to natural language.
    """
    
    if 'error' in api_response:
        return f"Could not find meeting venues: {api_response['error']}"
    
    venues = api_response.get('venues', [])
    
    if not venues:
        return "I couldn't find any meeting venues in the specified area. Please try a different location."
    
    # Create detailed venue list for LLM
    venues_text = ""
    for i, venue in enumerate(venues[:5], 1):
        venues_text += f"{i}. {venue['name']}\n"
        venues_text += f"   Address: {venue['address']}\n"
        venues_text += f"   Rating: {venue['rating']}"
        if venue.get('user_ratings_total', 0) > 0:
            venues_text += f" ({venue['user_ratings_total']} reviews)"
        venues_text += "\n"
        if venue.get('types'):
            venues_text += f"   Type: {', '.join(venue['types'][:3])}\n"
        venues_text += "\n"
    
    prompt = f"""Format these ACTUAL meeting venues naturally for the user.

ACTUAL VENUES from Google Maps:
{venues_text}

User asked: "{user_query}"

Present these meeting venues conversationally. Include names, addresses, and ratings.
DO NOT make up any venue names - use ONLY the ones listed above.

Response:"""

    formatted = call_llm(prompt)
    return formatted


# MAIN FUNCTION: Executes all 3 stages
def search_venues(user_query, context):
    """
    Complete 3-stage venue search for MEETING SPACES using Google Maps API.
    
    Stage 1: Extract params (LLM)
    Stage 2: Call Google Maps Places Text Search API
    Stage 3: Format actual results (LLM)
    """
    
    print(f"\n[DEBUG] ===== PLACES TOOL START =====")
    print(f"[DEBUG] Query: {user_query}")
    
    # Stage 1
    params = extract_places_parameters(user_query, context)
    print(f"[DEBUG] Extracted params: {params}")
    
    # Stage 2
    api_result = call_places_api(params)
    print(f"[DEBUG] API result keys: {api_result.keys()}")
    
    # Stage 3
    formatted_result = format_places_result(api_result, user_query)
    print(f"[DEBUG] Formatted result length: {len(formatted_result)}")
    print(f"[DEBUG] ===== PLACES TOOL END =====\n")
    
    return {
        'raw': api_result,
        'formatted': formatted_result,
        'params_used': params
    }