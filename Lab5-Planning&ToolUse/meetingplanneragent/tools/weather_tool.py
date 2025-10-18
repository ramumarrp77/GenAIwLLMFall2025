# Weather Tool - 3-Stage Pattern (Adapted from EventLens)

from utils.snowflake_connection import call_llm
from config import OPENWEATHER_API_KEY
import requests
import json
import re
from datetime import datetime

# STAGE 1: Parameter Extraction
def extract_weather_parameters(user_query, context):
    """
    LLM extracts location and date from user query
    """
    
    # Get today's date
    today_date_string = datetime.now().strftime("%A, %B %d, %Y")
    
    prompt = f"""Extract weather check parameters from this query.

User query: "{user_query}"

Context:
- Date preference: {context.get('date_preference', 'not set')}
- Location: {context.get('location', 'Boston')}

Today's date is {today_date_string}.

Extract location and date. For relative dates like 'tomorrow', convert to actual date.
If no specific date mentioned, use 'TODAY'.

Return ONLY JSON:
{{
  "location": "city name",
  "date": "YYYY-MM-DD or TODAY"
}}

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
        
        # Handle TODAY
        if params.get('date') == 'TODAY':
            params['date'] = datetime.now().strftime("%Y-%m-%d")
            params['is_today'] = True
        else:
            params['is_today'] = False
        
        return params
    except:
        return {
            "location": context.get('location', 'Boston'),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "is_today": True
        }


# STAGE 2: API Call (Adapted from EventLens)
def call_weather_api(params):
    """
    Call OpenWeatherMap API with multiple geocoding attempts
    """
    
    if not OPENWEATHER_API_KEY:
        return {'error': 'OpenWeatherMap API key not configured. Please add OPENWEATHER_API_KEY to your .env file'}
    
    location = params.get('location', 'Boston')
    is_today = params.get('is_today', True)
    
    try:
        print(f"[DEBUG] Weather: Geocoding '{location}'")
        
        # Try multiple location formats (from EventLens approach)
        location_attempts = [
            location,
            f"{location},US",
            location.split(',')[0].strip() if ',' in location else location,
        ]
        
        # Add special handling for Boston
        if 'Boston' in location or 'boston' in location.lower():
            location_attempts.extend([
                "Boston,MA,US",
                "Boston,Massachusetts,US"
            ])
        
        geo_data = None
        successful_location = None
        
        # Geocoding API
        geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
        
        for attempt in location_attempts:
            params_geo = {
                "q": attempt,
                "limit": 1,
                "appid": OPENWEATHER_API_KEY
            }
            
            print(f"[DEBUG] Weather: Trying '{attempt}'")
            
            response = requests.get(geocoding_url, params=params_geo, timeout=10)
            
            if response.status_code != 200:
                print(f"[DEBUG] Weather: HTTP {response.status_code}")
                continue
            
            try:
                data = response.json()
                if data and len(data) > 0:
                    geo_data = data
                    successful_location = attempt
                    print(f"[DEBUG] Weather: Success with '{attempt}'")
                    break
            except:
                continue
        
        if not geo_data or len(geo_data) == 0:
            return {
                'error': f'Location "{location}" not found. Try: "Boston", "Boston, MA", or zip code',
                'attempted': location_attempts
            }
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        location_name = geo_data[0].get('name', location)
        state = geo_data[0].get('state', '')
        country = geo_data[0].get('country', '')
        
        print(f"[DEBUG] Weather: Coordinates - {lat}, {lon}")
        
        # Use current weather for "today" (simpler and more reliable)
        if is_today:
            weather_url = "http://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                'lat': lat,
                'lon': lon,
                'appid': OPENWEATHER_API_KEY,
                'units': 'imperial'  # Fahrenheit
            }
            
            print(f"[DEBUG] Weather: Fetching current weather...")
            
            weather_response = requests.get(weather_url, params=weather_params, timeout=10)
            
            if weather_response.status_code != 200:
                return {'error': f'Weather API error: HTTP {weather_response.status_code}'}
            
            weather_data = weather_response.json()
            
            result = {
                'location': location_name,
                'state': state,
                'country': country,
                'temperature': round(weather_data['main']['temp']),
                'feels_like': round(weather_data['main']['feels_like']),
                'condition': weather_data['weather'][0]['description'],
                'humidity': weather_data['main']['humidity'],
                'wind_speed': round(weather_data['wind']['speed'], 1),
                'suitable_for_outdoor': weather_data['main']['temp'] > 50 and 'rain' not in weather_data['weather'][0]['description'].lower(),
                'is_today': True
            }
            
        else:
            # Use 5-day forecast for future dates (from EventLens)
            forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                'lat': lat,
                'lon': lon,
                'appid': OPENWEATHER_API_KEY,
                'units': 'imperial',
                'cnt': 40
            }
            
            print(f"[DEBUG] Weather: Fetching forecast...")
            
            forecast_response = requests.get(forecast_url, params=forecast_params, timeout=10)
            
            if forecast_response.status_code != 200:
                return {'error': f'Forecast API error: HTTP {forecast_response.status_code}'}
            
            forecast_data = forecast_response.json()
            
            # Find forecast for specific date
            target_date = datetime.strptime(params['date'], "%Y-%m-%d").date()
            forecasts = forecast_data.get("list", [])
            filtered = [
                f for f in forecasts 
                if datetime.fromtimestamp(f.get("dt")).date() == target_date
            ]
            
            if not filtered:
                return {'error': f'No forecast available for {params["date"]}'}
            
            # Get average for the day
            avg_temp = sum(f['main']['temp'] for f in filtered) / len(filtered)
            avg_feels = sum(f['main']['feels_like'] for f in filtered) / len(filtered)
            
            # Most common condition
            conditions = {}
            for f in filtered:
                cond = f['weather'][0]['description']
                conditions[cond] = conditions.get(cond, 0) + 1
            most_common = max(conditions.items(), key=lambda x: x[1])[0]
            
            result = {
                'location': location_name,
                'state': state,
                'country': country,
                'temperature': round(avg_temp),
                'feels_like': round(avg_feels),
                'condition': most_common,
                'humidity': round(sum(f['main']['humidity'] for f in filtered) / len(filtered)),
                'wind_speed': round(sum(f['wind']['speed'] for f in filtered) / len(filtered), 1),
                'suitable_for_outdoor': avg_temp > 50 and 'rain' not in most_common.lower(),
                'is_today': False,
                'date': params['date']
            }
        
        print(f"[DEBUG] Weather: {result['temperature']}°F, {result['condition']}")
        
        return result
        
    except requests.Timeout:
        return {'error': 'Weather API timeout. Please try again.'}
    except requests.RequestException as e:
        return {'error': f'Network error: {str(e)}'}
    except Exception as e:
        print(f"[DEBUG] Weather: Unexpected error - {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Error: {str(e)}'}


# STAGE 3: Format Result
def format_weather_result(api_response, user_query):
    """
    LLM formats weather data to natural language
    """
    
    if 'error' in api_response:
        error_msg = api_response['error']
        if 'attempted' in api_response:
            error_msg += f"\n\nTried: {', '.join(api_response['attempted'][:3])}"
        return error_msg
    
    # Build location string
    location_str = api_response['location']
    if api_response.get('state'):
        location_str += f", {api_response['state']}"
    
    weather_info = {
        'location': location_str,
        'temperature': f"{api_response['temperature']}°F",
        'feels_like': f"{api_response['feels_like']}°F",
        'condition': api_response['condition'],
        'humidity': f"{api_response['humidity']}%",
        'wind': f"{api_response['wind_speed']} mph",
        'outdoor_suitable': 'Yes' if api_response['suitable_for_outdoor'] else 'No, too cold or rainy'
    }
    
    prompt = f"""Format this weather data naturally for the user.

Weather in {location_str}:
- Temperature: {weather_info['temperature']} (feels like {weather_info['feels_like']})
- Conditions: {weather_info['condition']}
- Humidity: {weather_info['humidity']}
- Wind: {weather_info['wind']}
- Good for outdoor meeting: {weather_info['outdoor_suitable']}

User asked: "{user_query}"

Write a brief, conversational weather summary. Mention if it's suitable for outdoor meetings.

Response:"""

    formatted = call_llm(prompt)
    return formatted


# MAIN FUNCTION: Executes all 3 stages
def get_weather_forecast(user_query, context):
    """
    Complete 3-stage weather check
    
    Stage 1: Extract params (Snowflake Cortex)
    Stage 2: Call OpenWeather API
    Stage 3: Format result (Snowflake Cortex)
    """
    
    print(f"\n[DEBUG] ===== WEATHER TOOL START =====")
    print(f"[DEBUG] Weather query: {user_query}")
    print(f"[DEBUG] Weather API key: {'CONFIGURED' if OPENWEATHER_API_KEY else 'MISSING'}")
    
    # Stage 1
    params = extract_weather_parameters(user_query, context)
    print(f"[DEBUG] Weather params: {params}")
    
    # Stage 2
    api_result = call_weather_api(params)
    print(f"[DEBUG] Weather API result keys: {api_result.keys()}")
    
    # Stage 3
    formatted_result = format_weather_result(api_result, user_query)
    print(f"[DEBUG] Weather formatted length: {len(formatted_result)}")
    print(f"[DEBUG] ===== WEATHER TOOL END =====\n")
    
    return {
        'raw': api_result,
        'formatted': formatted_result,
        'params_used': params
    }