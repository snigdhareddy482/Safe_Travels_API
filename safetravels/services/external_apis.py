"""
External API Services
=====================

Unified interface for all external APIs:
- Google Maps (Routes, Places, Geocoding, Distance Matrix, Time Zone)
- Open-Meteo (Weather)
- FBI UCR (Crime data)
- OpenStreetMap/Overpass (Truck stops)
"""

import requests
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import time

# Load API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Location:
    latitude: float
    longitude: float
    address: Optional[str] = None


@dataclass
class WeatherData:
    temperature: float
    windspeed: float
    is_day: bool
    weather_code: int
    description: str


@dataclass
class RouteInfo:
    distance_miles: float
    duration_minutes: int
    duration_in_traffic: Optional[int] = None


@dataclass
class PlaceResult:
    name: str
    address: str
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    rating: Optional[float] = None


# =============================================================================
# GOOGLE MAPS SERVICES
# =============================================================================

class GoogleMapsService:
    """Google Maps API integration"""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    @staticmethod
    def geocode(address: str) -> Optional[Location]:
        """Convert address to coordinates"""
        try:
            r = requests.get(
                f"{GoogleMapsService.BASE_URL}/geocode/json",
                params={"address": address, "key": GOOGLE_API_KEY},
                timeout=10
            )
            if r.status_code == 200 and r.json().get("status") == "OK":
                result = r.json()["results"][0]
                loc = result["geometry"]["location"]
                return Location(
                    latitude=loc["lat"],
                    longitude=loc["lng"],
                    address=result.get("formatted_address")
                )
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None
    
    @staticmethod
    def get_distance_matrix(origin: str, destination: str) -> Optional[RouteInfo]:
        """Get distance and duration between two points"""
        try:
            r = requests.get(
                f"{GoogleMapsService.BASE_URL}/distancematrix/json",
                params={
                    "origins": origin,
                    "destinations": destination,
                    "departure_time": "now",
                    "key": GOOGLE_API_KEY
                },
                timeout=10
            )
            if r.status_code == 200 and r.json().get("status") == "OK":
                element = r.json()["rows"][0]["elements"][0]
                if element.get("status") == "OK":
                    return RouteInfo(
                        distance_miles=element["distance"]["value"] / 1609.34,
                        duration_minutes=element["duration"]["value"] // 60,
                        duration_in_traffic=element.get("duration_in_traffic", {}).get("value", 0) // 60
                    )
        except Exception as e:
            print(f"Distance matrix error: {e}")
        return None
    
    @staticmethod
    def get_timezone(latitude: float, longitude: float) -> Optional[Dict]:
        """Get timezone for a location"""
        try:
            timestamp = int(time.time())
            r = requests.get(
                f"{GoogleMapsService.BASE_URL}/timezone/json",
                params={
                    "location": f"{latitude},{longitude}",
                    "timestamp": timestamp,
                    "key": GOOGLE_API_KEY
                },
                timeout=10
            )
            if r.status_code == 200 and r.json().get("status") == "OK":
                data = r.json()
                return {
                    "timezone_id": data["timeZoneId"],
                    "timezone_name": data["timeZoneName"],
                    "raw_offset_hours": data["rawOffset"] / 3600,
                    "dst_offset_hours": data["dstOffset"] / 3600
                }
        except Exception as e:
            print(f"Timezone error: {e}")
        return None
    
    @staticmethod
    def compute_route(origin: str, destination: str) -> Optional[Dict]:
        """Compute route using Routes API"""
        try:
            url = "https://routes.googleapis.com/directions/v2:computeRoutes"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_API_KEY,
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline,routes.legs"
            }
            data = {
                "origin": {"address": origin},
                "destination": {"address": destination},
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE"
            }
            r = requests.post(url, headers=headers, json=data, timeout=15)
            if r.status_code == 200:
                routes = r.json().get("routes", [])
                if routes:
                    route = routes[0]
                    return {
                        "distance_miles": route.get("distanceMeters", 0) / 1609.34,
                        "duration_minutes": int(route.get("duration", "0s").replace("s", "")) // 60,
                        "legs": route.get("legs", [])
                    }
        except Exception as e:
            print(f"Route computation error: {e}")
        return None
    
    @staticmethod
    def search_nearby_places(latitude: float, longitude: float, 
                             place_type: str = "gas_station", 
                             radius_meters: int = 50000) -> List[PlaceResult]:
        """Search for places nearby using Places API (New)"""
        try:
            url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GOOGLE_API_KEY,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating"
            }
            data = {
                "includedTypes": [place_type],
                "maxResultCount": 20,
                "locationRestriction": {
                    "circle": {
                        "center": {"latitude": latitude, "longitude": longitude},
                        "radius": float(radius_meters)
                    }
                }
            }
            r = requests.post(url, headers=headers, json=data, timeout=15)
            if r.status_code == 200:
                places = r.json().get("places", [])
                results = []
                for p in places:
                    loc = p.get("location", {})
                    results.append(PlaceResult(
                        name=p.get("displayName", {}).get("text", "Unknown"),
                        address=p.get("formattedAddress", ""),
                        latitude=loc.get("latitude", 0),
                        longitude=loc.get("longitude", 0),
                        rating=p.get("rating")
                    ))
                return results
        except Exception as e:
            print(f"Places search error: {e}")
        return []


# =============================================================================
# WEATHER SERVICE (Open-Meteo - FREE)
# =============================================================================

class WeatherService:
    """Open-Meteo weather API - 100% free, no API key needed"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    
    @staticmethod
    def get_current_weather(latitude: float, longitude: float) -> Optional[WeatherData]:
        """Get current weather for a location"""
        try:
            r = requests.get(
                WeatherService.BASE_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_weather": "true"
                },
                timeout=10
            )
            if r.status_code == 200:
                data = r.json().get("current_weather", {})
                weather_code = data.get("weathercode", 0)
                return WeatherData(
                    temperature=data.get("temperature", 0),
                    windspeed=data.get("windspeed", 0),
                    is_day=data.get("is_day", 1) == 1,
                    weather_code=weather_code,
                    description=WeatherService.WEATHER_CODES.get(weather_code, "Unknown")
                )
        except Exception as e:
            print(f"Weather error: {e}")
        return None
    
    @staticmethod
    def get_weather_alerts(latitude: float, longitude: float) -> List[str]:
        """Check for weather-related safety alerts"""
        weather = WeatherService.get_current_weather(latitude, longitude)
        alerts = []
        
        if weather:
            # High wind alert
            if weather.windspeed > 40:
                alerts.append("⚠️ HIGH WIND WARNING: Wind speeds over 40 mph")
            elif weather.windspeed > 25:
                alerts.append("🌬️ Wind advisory: Gusty conditions")
            
            # Temperature alerts
            if weather.temperature < 0:
                alerts.append("🥶 FREEZE WARNING: Roads may be icy")
            elif weather.temperature > 38:  # 100°F
                alerts.append("🔥 EXTREME HEAT: Stay hydrated")
            
            # Rain/Snow alerts
            if weather.weather_code in [65, 67, 82]:
                alerts.append("🌧️ HEAVY RAIN: Reduced visibility")
            if weather.weather_code in [75, 86]:
                alerts.append("❄️ HEAVY SNOW: Hazardous driving")
            if weather.weather_code in [95, 96, 99]:
                alerts.append("⛈️ THUNDERSTORM: Seek shelter")
            if weather.weather_code in [45, 48]:
                alerts.append("🌫️ FOG WARNING: Low visibility")
        
        return alerts


# =============================================================================
# TRUCK STOP SERVICE (OpenStreetMap - FREE)
# =============================================================================

class TruckStopService:
    """Query truck stops from OpenStreetMap via Overpass API"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    @staticmethod
    def find_truck_stops(latitude: float, longitude: float, 
                         radius_km: int = 50) -> List[Dict]:
        """Find truck stops using OpenStreetMap Overpass API"""
        try:
            # Overpass QL query for truck stops
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="fuel"]["hgv"="yes"](around:{radius_km * 1000},{latitude},{longitude});
              node["amenity"="truck_stop"](around:{radius_km * 1000},{latitude},{longitude});
              way["amenity"="fuel"]["hgv"="yes"](around:{radius_km * 1000},{latitude},{longitude});
            );
            out center 20;
            """
            
            r = requests.post(
                TruckStopService.OVERPASS_URL,
                data={"data": query},
                timeout=30
            )
            
            if r.status_code == 200:
                elements = r.json().get("elements", [])
                stops = []
                for elem in elements:
                    tags = elem.get("tags", {})
                    stops.append({
                        "name": tags.get("name", "Truck Stop"),
                        "brand": tags.get("brand", "Unknown"),
                        "latitude": elem.get("lat", elem.get("center", {}).get("lat")),
                        "longitude": elem.get("lon", elem.get("center", {}).get("lon")),
                        "fuel": tags.get("fuel", "diesel"),
                        "hgv": tags.get("hgv", "yes")
                    })
                return stops
        except Exception as e:
            print(f"Truck stop search error: {e}")
        return []


# =============================================================================
# UNIFIED API CLIENT
# =============================================================================

class SafeTravelsAPIClient:
    """Unified client combining all external APIs"""
    
    google = GoogleMapsService
    weather = WeatherService
    truck_stops = TruckStopService
    
    @classmethod
    def get_location_info(cls, latitude: float, longitude: float) -> Dict:
        """Get comprehensive info for a location"""
        weather = cls.weather.get_current_weather(latitude, longitude)
        timezone = cls.google.get_timezone(latitude, longitude)
        weather_alerts = cls.weather.get_weather_alerts(latitude, longitude)
        
        return {
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "weather": {
                "temperature_c": weather.temperature if weather else None,
                "temperature_f": (weather.temperature * 9/5 + 32) if weather else None,
                "conditions": weather.description if weather else None,
                "windspeed_mph": weather.windspeed if weather else None,
                "is_day": weather.is_day if weather else None
            } if weather else None,
            "timezone": timezone,
            "alerts": weather_alerts
        }
    
    @classmethod
    def plan_safe_route(cls, origin: str, destination: str) -> Dict:
        """Plan a route with safety information"""
        route = cls.google.compute_route(origin, destination)
        
        if route:
            # Get weather at destination
            dest_loc = cls.google.geocode(destination)
            dest_weather = None
            if dest_loc:
                dest_weather = cls.weather.get_current_weather(
                    dest_loc.latitude, dest_loc.longitude
                )
            
            return {
                "route": {
                    "distance_miles": round(route["distance_miles"], 1),
                    "duration_minutes": route["duration_minutes"],
                    "duration_hours": round(route["duration_minutes"] / 60, 1)
                },
                "destination_weather": {
                    "temperature_c": dest_weather.temperature if dest_weather else None,
                    "conditions": dest_weather.description if dest_weather else None
                } if dest_weather else None
            }
        return {"error": "Could not compute route"}


# Export main client
api_client = SafeTravelsAPIClient()


# =============================================================================
# TEST FUNCTION
# =============================================================================

if __name__ == "__main__":
    print("Testing SafeTravels API Services...")
    print("=" * 50)
    
    # Test Geocoding
    print("\n1. Geocoding Dallas, TX:")
    loc = GoogleMapsService.geocode("Dallas, TX")
    print(f"   {loc}")
    
    # Test Weather
    print("\n2. Weather in Dallas:")
    weather = WeatherService.get_current_weather(32.7767, -96.7970)
    print(f"   {weather}")
    
    # Test Timezone
    print("\n3. Timezone:")
    tz = GoogleMapsService.get_timezone(32.7767, -96.7970)
    print(f"   {tz}")
    
    # Test Distance
    print("\n4. Distance Dallas to Memphis:")
    dist = GoogleMapsService.get_distance_matrix("Dallas, TX", "Memphis, TN")
    print(f"   {dist}")
    
    # Test Places
    print("\n5. Nearby gas stations:")
    places = GoogleMapsService.search_nearby_places(32.7767, -96.7970)
    for p in places[:3]:
        print(f"   - {p.name}")
    
    # Test Weather Alerts
    print("\n6. Weather Alerts:")
    alerts = WeatherService.get_weather_alerts(32.7767, -96.7970)
    print(f"   {alerts if alerts else 'No alerts'}")
    
    print("\n" + "=" * 50)
    print("All tests complete!")
