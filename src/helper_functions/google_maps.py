"""Google Maps helper functions for SafeTravels API.

Provides route data extraction for crime analysis with:
- Multiple route alternatives
- Adaptive waypoint sampling (denser in urban areas, sparser on highways)
- Real-time traffic data
- Place types along route (gas stations, police stations)

Usage:
    from src.helper_functions.google_maps import use_google_maps

    routes = use_google_maps(
        start="Willis Tower, Chicago, IL",
        destination="Navy Pier, Chicago, IL"
    )
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import googlemaps
import polyline as polyline_lib
from math import radians, sin, cos, sqrt, atan2

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Google Maps API key
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RoutePoint:
    """A point along a route for crime analysis."""
    latitude: float
    longitude: float
    description: Optional[str] = None  # City/area name (if enriched)
    area_type: Optional[str] = None    # "urban", "suburban", "rural"


@dataclass
class PlaceInfo:
    """A place of interest along the route."""
    name: str
    place_type: str  # "gas_station", "police", etc.
    latitude: float
    longitude: float
    vicinity: Optional[str] = None


@dataclass
class TrafficInfo:
    """Traffic information for a route."""
    duration_in_traffic_minutes: int
    traffic_delay_minutes: int  # Additional time due to traffic
    traffic_condition: str      # "light", "moderate", "heavy"


@dataclass
class RouteData:
    """Complete route data for crime analysis."""
    route_id: int
    summary: str                           # e.g., "I-90 W via Downtown"
    distance_miles: float
    duration_minutes: int
    start_address: str
    end_address: str
    waypoints: List[RoutePoint]            # Points for crime analysis
    polyline: str                          # Encoded polyline for visualization
    traffic: Optional[TrafficInfo] = None
    places_along_route: List[PlaceInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "route_id": self.route_id,
            "summary": self.summary,
            "distance_miles": self.distance_miles,
            "duration_minutes": self.duration_minutes,
            "start_address": self.start_address,
            "end_address": self.end_address,
            "waypoints": [
                {
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "description": wp.description,
                    "area_type": wp.area_type
                }
                for wp in self.waypoints
            ],
            "polyline": self.polyline,
            "traffic": asdict(self.traffic) if self.traffic else None,
            "places_along_route": [asdict(p) for p in self.places_along_route]
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates in miles using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def get_adaptive_interval(total_distance_miles: float) -> float:
    """
    Determine waypoint sampling interval based on route distance.

    Adaptive strategy:
    - Urban routes (< 5 mi): 0.5 mile intervals (very dense)
    - Short urban (5-10 mi): 0.75 mile intervals (dense)
    - Suburban (10-20 mi): 1.5 mile intervals (moderate)
    - Mixed (20-40 mi): 2.5 mile intervals
    - Highway (> 40 mi): 4 mile intervals (sparse)

    Args:
        total_distance_miles: Total route distance

    Returns:
        Sampling interval in miles
    """
    if total_distance_miles < 5:
        return 0.5   # Very dense for short urban routes
    elif total_distance_miles < 10:
        return 0.75  # Dense for urban routes
    elif total_distance_miles < 20:
        return 1.5   # Moderate for suburban
    elif total_distance_miles < 40:
        return 2.5   # Mixed urban/highway
    else:
        return 4.0   # Sparse for long highway routes


def sample_points_from_polyline(
    encoded_polyline: str,
    interval_miles: float
) -> List[RoutePoint]:
    """
    Extract waypoints from a polyline at adaptive intervals.

    Ensures even distribution of waypoints along the route for
    comprehensive crime data coverage.

    Args:
        encoded_polyline: Google's encoded polyline string
        interval_miles: Distance between sample points

    Returns:
        List of RoutePoint objects evenly distributed along the route
    """
    # Decode the polyline to get all coordinate points
    coords = polyline_lib.decode(encoded_polyline)

    if not coords:
        return []

    # Always include start point
    waypoints = [RoutePoint(latitude=coords[0][0], longitude=coords[0][1])]
    accumulated_distance = 0.0

    for i in range(1, len(coords)):
        prev_lat, prev_lon = coords[i-1]
        curr_lat, curr_lon = coords[i]

        segment_distance = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
        accumulated_distance += segment_distance

        # Add point if we've traveled far enough
        if accumulated_distance >= interval_miles:
            waypoints.append(RoutePoint(latitude=curr_lat, longitude=curr_lon))
            accumulated_distance = 0.0

    # Always include end point (if not already added)
    if len(coords) > 1:
        final_lat, final_lon = coords[-1]
        last_wp = waypoints[-1]

        # Check if end point is different from last waypoint
        distance_to_end = haversine_distance(
            last_wp.latitude, last_wp.longitude,
            final_lat, final_lon
        )

        # Add end point if it's more than 0.1 miles from last waypoint
        if distance_to_end > 0.1:
            waypoints.append(RoutePoint(latitude=final_lat, longitude=final_lon))

    return waypoints


def classify_traffic(duration_normal: int, duration_traffic: int) -> TrafficInfo:
    """
    Classify traffic condition based on delay.

    Args:
        duration_normal: Normal duration in minutes (without traffic)
        duration_traffic: Duration with current traffic in minutes

    Returns:
        TrafficInfo with condition classification
    """
    delay = max(0, duration_traffic - duration_normal)

    # Calculate delay percentage
    if duration_normal > 0:
        delay_percent = (delay / duration_normal) * 100
    else:
        delay_percent = 0

    # Classify based on both absolute delay and percentage
    if delay < 5 and delay_percent < 10:
        condition = "light"
    elif delay < 15 and delay_percent < 30:
        condition = "moderate"
    else:
        condition = "heavy"

    return TrafficInfo(
        duration_in_traffic_minutes=duration_traffic,
        traffic_delay_minutes=delay,
        traffic_condition=condition
    )


# =============================================================================
# PLACES HELPER
# =============================================================================

def _get_places_along_route(
    gmaps: googlemaps.Client,
    waypoints: List[RoutePoint],
    place_types: List[str],
    search_radius_meters: int = 1609,  # 1 mile
    max_places_per_type: int = 3
) -> List[PlaceInfo]:
    """
    Find places of interest along the route.

    Samples strategic waypoints (start, middle, end) and searches for
    nearby places to avoid excessive API calls.

    Args:
        gmaps: Google Maps client
        waypoints: List of route waypoints
        place_types: Types to search for (e.g., ["gas_station", "police"])
        search_radius_meters: Search radius around each point
        max_places_per_type: Max places to return per type per location

    Returns:
        List of PlaceInfo objects
    """
    places = []

    if not waypoints:
        return places

    # Sample strategic points: start, 25%, 50%, 75%, end
    num_waypoints = len(waypoints)
    if num_waypoints <= 3:
        sample_indices = list(range(num_waypoints))
    else:
        sample_indices = [
            0,                          # Start
            num_waypoints // 4,         # 25%
            num_waypoints // 2,         # 50% (middle)
            3 * num_waypoints // 4,     # 75%
            num_waypoints - 1           # End
        ]
        # Remove duplicates while preserving order
        sample_indices = list(dict.fromkeys(sample_indices))

    sample_points = [waypoints[i] for i in sample_indices]

    for point in sample_points:
        for place_type in place_types:
            try:
                results = gmaps.places_nearby(
                    location=(point.latitude, point.longitude),
                    radius=search_radius_meters,
                    type=place_type
                )

                for result in results.get("results", [])[:max_places_per_type]:
                    loc = result["geometry"]["location"]
                    places.append(PlaceInfo(
                        name=result.get("name", "Unknown"),
                        place_type=place_type,
                        latitude=loc["lat"],
                        longitude=loc["lng"],
                        vicinity=result.get("vicinity")
                    ))
            except Exception as e:
                # Log but don't fail - places are optional
                print(f"Warning: Places search failed for {place_type}: {e}")
                continue

    return places


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def use_google_maps(
    start: str,
    destination: str,
    include_traffic: bool = True,
    include_places: bool = True,
    place_types: Optional[List[str]] = None
) -> List[RouteData]:
    """
    Get route alternatives between two addresses with adaptive waypoints.

    This is the main function for Phase 2. It:
    1. Calls Google Directions API with alternatives=True
    2. Extracts route geometry from polylines
    3. Samples waypoints at adaptive intervals (denser in urban areas)
    4. Optionally fetches real-time traffic data
    5. Optionally finds places of interest along the route

    Args:
        start: Starting address (e.g., "Willis Tower, Chicago, IL")
        destination: Destination address (e.g., "Navy Pier, Chicago, IL")
        include_traffic: Whether to fetch real-time traffic data
        include_places: Whether to fetch places along route
        place_types: Place types to search for (default: gas_station, police)

    Returns:
        List of RouteData objects, one per route alternative

    Raises:
        ValueError: If API key not set or invalid addresses

    Example:
        >>> routes = use_google_maps(
        ...     start="Willis Tower, Chicago, IL",
        ...     destination="Navy Pier, Chicago, IL"
        ... )
        >>> for route in routes:
        ...     print(f"Route {route.route_id}: {route.summary}")
        ...     print(f"  Distance: {route.distance_miles} miles")
        ...     print(f"  Waypoints: {len(route.waypoints)}")
    """
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY environment variable not set. "
            "Please add it to your .env file."
        )

    if place_types is None:
        place_types = ["gas_station", "police"]

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    # Build directions request parameters
    directions_params = {
        "origin": start,
        "destination": destination,
        "mode": "driving",
        "alternatives": True,  # Request multiple routes
    }

    # Add traffic data request (requires departure_time)
    if include_traffic:
        directions_params["departure_time"] = "now"
        directions_params["traffic_model"] = "best_guess"

    # Call Google Directions API
    try:
        directions_result = gmaps.directions(**directions_params)
    except googlemaps.exceptions.ApiError as e:
        raise ValueError(f"Google Maps API error: {e}")
    except Exception as e:
        raise ValueError(f"Failed to get directions: {e}")

    if not directions_result:
        raise ValueError(
            f"No routes found between '{start}' and '{destination}'. "
            "Please check the addresses are valid."
        )

    routes = []

    for idx, route in enumerate(directions_result):
        # Extract the first leg (for direct A to B routes)
        leg = route["legs"][0]

        # Extract distance and duration
        distance_meters = leg["distance"]["value"]
        distance_miles = distance_meters / 1609.34

        duration_seconds = leg["duration"]["value"]
        duration_minutes = duration_seconds // 60

        # Get traffic info if available
        traffic_info = None
        if include_traffic and "duration_in_traffic" in leg:
            traffic_seconds = leg["duration_in_traffic"]["value"]
            traffic_minutes = traffic_seconds // 60
            traffic_info = classify_traffic(duration_minutes, traffic_minutes)

        # Get overview polyline (encoded path)
        overview_polyline = route["overview_polyline"]["points"]

        # Calculate adaptive sampling interval
        interval = get_adaptive_interval(distance_miles)

        # Sample waypoints from polyline
        waypoints = sample_points_from_polyline(
            encoded_polyline=overview_polyline,
            interval_miles=interval
        )

        # Get places along route (optional)
        places = []
        if include_places and waypoints:
            places = _get_places_along_route(
                gmaps=gmaps,
                waypoints=waypoints,
                place_types=place_types
            )

        # Create RouteData object
        route_data = RouteData(
            route_id=idx + 1,
            summary=route.get("summary", f"Route {idx + 1}"),
            distance_miles=round(distance_miles, 2),
            duration_minutes=int(duration_minutes),
            start_address=leg["start_address"],
            end_address=leg["end_address"],
            waypoints=waypoints,
            polyline=overview_polyline,
            traffic=traffic_info,
            places_along_route=places
        )

        routes.append(route_data)

    return routes


# =============================================================================
# OPTIONAL: Enrich waypoints with city names
# =============================================================================

def enrich_waypoints_with_locations(
    routes: List[RouteData],
    gmaps_client: Optional[googlemaps.Client] = None
) -> List[RouteData]:
    """
    Add city/area descriptions to waypoints via reverse geocoding.

    WARNING: This makes additional API calls (one per waypoint).
    Use sparingly to avoid rate limits and costs.

    Args:
        routes: List of RouteData to enrich
        gmaps_client: Optional Google Maps client (creates new if not provided)

    Returns:
        Same routes with waypoint descriptions populated
    """
    if gmaps_client is None:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY not set")
        gmaps_client = googlemaps.Client(key=GOOGLE_API_KEY)

    for route in routes:
        for waypoint in route.waypoints:
            try:
                result = gmaps_client.reverse_geocode(
                    (waypoint.latitude, waypoint.longitude),
                    result_type=["locality", "neighborhood", "sublocality"]
                )
                if result:
                    # Extract the most specific location name
                    for component in result[0].get("address_components", []):
                        types = component.get("types", [])
                        if "neighborhood" in types:
                            waypoint.description = component["long_name"]
                            waypoint.area_type = "urban"
                            break
                        elif "sublocality" in types:
                            waypoint.description = component["long_name"]
                            waypoint.area_type = "urban"
                            break
                        elif "locality" in types:
                            waypoint.description = component["long_name"]
                            # Could determine area_type based on population data
                            break
            except Exception:
                # Continue without description on error
                pass

    return routes


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    """Quick test of the Google Maps helper."""
    print("=" * 60)
    print("Google Maps Helper - Test")
    print("=" * 60)

    try:
        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",
            include_traffic=True,
            include_places=True
        )

        print(f"\nFound {len(routes)} route(s)\n")

        for route in routes:
            print(f"Route {route.route_id}: {route.summary}")
            print(f"  Distance: {route.distance_miles} miles")
            print(f"  Duration: {route.duration_minutes} minutes")
            print(f"  Waypoints: {len(route.waypoints)}")

            if route.traffic:
                print(f"  Traffic: {route.traffic.traffic_condition} "
                      f"(+{route.traffic.traffic_delay_minutes} min delay)")

            if route.places_along_route:
                print(f"  Places found: {len(route.places_along_route)}")
                for place in route.places_along_route[:3]:
                    print(f"    - {place.name} ({place.place_type})")

            print(f"\n  Waypoint coordinates:")
            for i, wp in enumerate(route.waypoints):
                print(f"    {i+1}. ({wp.latitude:.6f}, {wp.longitude:.6f})")

            print()

    except Exception as e:
        print(f"Error: {e}")
