import streamlit as st
import requests
import os
from snowflake_connection import call_cortex_complete

class MapsAgent:
    def __init__(self):
        self.name = "Transit Navigation Specialist"
        self.model = "llama4-maverick"
        self.icon = "🗺️"
        self.maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
    def execute(self, user_query: str, show_backend: bool = False) -> str:
        """Find Apple Store locations and transit directions using Google Maps API"""
        
        # Step 1: Extract location from user query
        location_extraction_prompt = f"""You are a Location Extraction Specialist. Extract location information from this query.

User query: {user_query}

Extract the origin location. If no specific location mentioned, assume "Northeastern University, Boston, MA".
Return ONLY the origin location, no additional text."""

        origin_location = call_cortex_complete(location_extraction_prompt, self.model)
        
        if show_backend:
            st.write(f"{self.icon} **{self.name}** (Google Maps API)")
            with st.expander("🔧 Maps Agent - Step 1: Location Extraction", expanded=False):
                st.code(location_extraction_prompt, language="text")
                st.write(f"**Extracted Origin:** {origin_location}")
        else:
            st.write(f"{self.icon} **{self.name}** (Google Maps API)")
        
        # Step 2: Find Apple Stores using Google Places API
        store_data = self._find_apple_stores(origin_location)
        
        if show_backend:
            with st.expander("🔧 Maps Agent - Step 2: Google Places API", expanded=False):
                st.write("**Google Places API Call:**")
                st.code(f"Query: Apple Store near {origin_location}", language="text")
                st.write("**Store Results:**")
                st.text_area("Places API Results:", str(store_data)[:500] + "..." if len(str(store_data)) > 500 else str(store_data), height=150)
        
        # Step 3: Get transit directions to nearest store
        if isinstance(store_data, list) and len(store_data) > 0 and isinstance(store_data[0], dict):
            directions_data = self._get_transit_directions(origin_location, store_data[0])
        else:
            directions_data = "No stores found for directions"
        
        if show_backend:
            with st.expander("🔧 Maps Agent - Step 3: Google Directions API", expanded=False):
                st.write("**Google Directions API Call:**")
                st.code(f"Mode: transit, From: {origin_location}, To: {store_data[0] if store_data else 'N/A'}", language="text")
                st.write("**Transit Directions:**")
                st.text_area("Directions API Results:", str(directions_data)[:500] + "..." if len(str(directions_data)) > 500 else str(directions_data), height=150)
        
        # Step 4: Format the results using Cortex
        formatting_prompt = f"""You are a Transit Navigation Specialist. Format this location and transit information for the customer.

User query: {user_query}
Store information: {store_data}
Transit directions: {directions_data}

Provide structured location information:
- Store Location: [Store name, address, and contact details]
- Transit Directions: [Step-by-step public transit route]
- Travel Time: [Estimated time by public transit]
- Additional Info: [Store hours or helpful tips]

Return ONLY the structured location information, no additional text."""

        with st.spinner(f"{self.icon} Maps Agent formatting directions..."):
            maps_result = call_cortex_complete(formatting_prompt, self.model)
        
        if show_backend:
            with st.expander("🔧 Maps Agent - Step 4: Response Formatting", expanded=False):
                st.write("**Formatting Prompt:**")
                st.code(formatting_prompt, language="text")
                st.write("**Formatted Result:**")
                st.text_area("Location Analysis Output:", maps_result, height=200)
        
        st.success(f"✅ {self.name} completed location analysis")
        return maps_result
    
    def _find_apple_stores(self, location: str) -> list:
        """Find Apple Stores using Google Places API"""
        if not self.maps_api_key:
            return ["Google Maps API key not configured"]
        
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": f"Apple Store near {location}",
                "key": self.maps_api_key,
                "type": "store"
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return [f"Places API Error: HTTP {response.status_code}"]
            
            data = response.json()
            stores = []
            
            if "results" in data:
                for store in data["results"][:2]:  # Get top 2 stores
                    store_info = {
                        "name": store.get("name", "Apple Store"),
                        "address": store.get("formatted_address", "Address not available"),
                        "place_id": store.get("place_id", ""),
                        "rating": store.get("rating", "No rating")
                    }
                    stores.append(store_info)
            
            return stores if stores else ["No Apple Stores found"]
            
        except Exception as e:
            return [f"Error finding stores: {str(e)}"]
    
    def _get_transit_directions(self, origin: str, destination_store: dict) -> str:
        """Get transit directions using Google Directions API"""
        if not self.maps_api_key:
            return "Google Maps API key not configured"
        
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            
            destination = destination_store.get("address", destination_store.get("name", "Apple Store"))
            
            params = {
                "origin": origin,
                "destination": destination,
                "mode": "transit",
                "key": self.maps_api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return f"Directions API Error: HTTP {response.status_code}"
            
            data = response.json()
            
            if data["status"] != "OK":
                return f"Directions not found: {data.get('status', 'Unknown error')}"
            
            # Extract transit information
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                leg = route["legs"][0]
                
                transit_info = {
                    "duration": leg["duration"]["text"],
                    "distance": leg["distance"]["text"],
                    "start_address": leg["start_address"],
                    "end_address": leg["end_address"],
                    "steps_count": len(leg["steps"])
                }
                
                return str(transit_info)
            else:
                return "No transit routes found"
                
        except Exception as e:
            return f"Error getting directions: {str(e)}"