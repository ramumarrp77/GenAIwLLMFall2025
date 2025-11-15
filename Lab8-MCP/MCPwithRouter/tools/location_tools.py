"""
Location Tools - Google Maps Operations
"""

import requests

class LocationTools:
    """
    Location operations tools
    Uses same pattern as your MapsAgent
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("[LOCATION TOOLS] Initialized with Google Maps API")
    
    def find_nearest_store(self, location: str) -> dict:
        """Find nearest Apple Store"""
        print(f"\n[LOCATION TOOL] find_nearest_store")
        print(f"[LOCATION TOOL] Location: {location}")
        
        stores = self._find_apple_stores(location)
        
        # Check if error (string) or success (dict)
        if isinstance(stores, list) and len(stores) > 0:
            if isinstance(stores[0], str):
                # It's an error message
                print(f"[LOCATION TOOL] ❌ {stores[0]}")
                return {"success": False, "error": stores[0]}
            elif isinstance(stores[0], dict):
                # Actual stores
                print(f"[LOCATION TOOL] ✅ Found {len(stores)} stores")
                return {"success": True, "stores": stores, "count": len(stores)}
        
        return {"success": False, "error": "No stores found"}
    
    def get_directions(self, origin: str, destination: str) -> dict:
        """Get directions between two locations"""
        print(f"\n[LOCATION TOOL] get_directions")
        print(f"[LOCATION TOOL] From: {origin}")
        print(f"[LOCATION TOOL] To: {destination}")
        
        stores = self._find_apple_stores(destination)
        
        # Check for errors
        if not isinstance(stores, list) or not stores:
            return {"success": False, "error": "No stores found"}
        
        if isinstance(stores[0], str):
            print(f"[LOCATION TOOL] ❌ {stores[0]}")
            return {"success": False, "error": stores[0]}
        
        directions_data = self._get_transit_directions(origin, stores[0])
        
        # Check if directions returned error
        if "Error" in str(directions_data) or "not found" in str(directions_data):
            print(f"[LOCATION TOOL] ❌ {directions_data}")
            return {"success": False, "error": str(directions_data)}
        
        print(f"[LOCATION TOOL] ✅ Got directions")
        return {"success": True, "directions": directions_data}
    
    def get_store_details(self, store_name: str) -> dict:
        """Get details about a specific store"""
        print(f"\n[LOCATION TOOL] get_store_details")
        print(f"[LOCATION TOOL] Store: {store_name}")
        
        stores = self._find_apple_stores(store_name)
        
        # Check for errors
        if not isinstance(stores, list) or not stores:
            return {"success": False, "error": "No stores found"}
        
        if isinstance(stores[0], str):
            print(f"[LOCATION TOOL] ❌ {stores[0]}")
            return {"success": False, "error": stores[0]}
        
        store_info = stores[0]
        
        print(f"[LOCATION TOOL] ✅ Retrieved store details")
        print(f"[LOCATION TOOL]    Name: {store_info.get('name')}")
        
        return {"success": True, "store": store_info}
    
    def _find_apple_stores(self, location: str) -> list:
        """Find Apple Stores - EXACT from your MapsAgent"""
        if not self.api_key:
            return ["Google Maps API key not configured"]
        
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": f"Apple Store near {location}",
                "key": self.api_key,
                "type": "store"
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return [f"Places API Error: HTTP {response.status_code}"]
            
            data = response.json()
            stores = []
            
            if "results" in data:
                for store in data["results"][:2]:
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
        """Get transit directions - EXACT from your MapsAgent"""
        if not self.api_key:
            return "Google Maps API key not configured"
        
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            
            destination = destination_store.get("address", destination_store.get("name", "Apple Store"))
            
            params = {
                "origin": origin,
                "destination": destination,
                "mode": "transit",
                "key": self.api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                return f"Directions API Error: HTTP {response.status_code}"
            
            data = response.json()
            
            if data["status"] != "OK":
                return f"Directions not found: {data.get('status', 'Unknown error')}"
            
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