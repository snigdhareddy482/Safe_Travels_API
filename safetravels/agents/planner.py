"""
SafeTravels Agents - Planner
=============================

The Planner agent generates multiple route options for a trip,
ranks them by safety, and marks hotspots to avoid.

RESPONSIBILITIES:
    1. Generate 3+ alternative routes (origin → destination)
    2. Score each route using route_scanner
    3. Auto-avoid theft hotspots (penalize or exclude)
    4. Mark recommended route
    5. Let driver choose (no auto-selection)

OUTPUT:
    List of RouteOption objects, sorted by risk (safest first)

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import math

from safetravels.agents.state import (
    AgentState,
    RouteOption,
    TripRequest,
    add_reasoning_step,
)
from safetravels.mcp.tools.route_scanner import scan_route
from safetravels.mcp.tools.risk_scorer import RiskContext

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Penalty multiplier for routes through hotspots
HOTSPOT_PENALTY: float = 1.5

# Maximum routes to generate
MAX_ROUTES: int = 3

# Route scoring weights
WEIGHT_SAFETY: float = 0.6      # Safety is most important
WEIGHT_TIME: float = 0.25       # Time matters
WEIGHT_DISTANCE: float = 0.15   # Distance matters less


# =============================================================================
# KNOWN HOTSPOTS (Mock - replace with real data)
# =============================================================================

# Known theft hotspots to avoid if possible
THEFT_HOTSPOTS = [
    {
        "name": "I-10 Corridor LA-Phoenix",
        "bounds": {"lat_min": 32.0, "lat_max": 34.5, "lon_min": -118.5, "lon_max": -111.0},
        "severity": "high",
    },
    {
        "name": "I-95 Miami Corridor",
        "bounds": {"lat_min": 25.0, "lat_max": 28.0, "lon_min": -81.0, "lon_max": -79.5},
        "severity": "high",
    },
    {
        "name": "Chicago South Side",
        "bounds": {"lat_min": 41.6, "lat_max": 42.0, "lon_min": -87.9, "lon_max": -87.5},
        "severity": "medium",
    },
]


# =============================================================================
# MAIN PLANNER FUNCTION
# =============================================================================

def plan_routes(state: AgentState) -> AgentState:
    """
    Generate multiple route options for the trip request.
    
    This is a LangGraph node that:
        1. Reads trip_request from state
        2. Generates alternative routes
        3. Scores each route
        4. Returns updated state with route_options
    
    Args:
        state: Current agent state with trip_request
        
    Returns:
        Updated state with route_options populated
    """
    logger.info("--- PLANNER: Generating route options ---")
    
    trip = state.get("trip_request")
    if not trip:
        state["route_options"] = []
        state["warnings"].append("No trip request provided")
        return state
    
    # Extract coordinates
    origin = (trip["origin"]["lat"], trip["origin"]["lon"])
    destination = (trip["destination"]["lat"], trip["destination"]["lon"])
    commodity = trip.get("commodity", "general")
    cargo_value = trip.get("cargo_value", 50000)
    
    add_reasoning_step(state, f"Planning routes from {origin} to {destination}")
    
    # Generate alternative routes (mock waypoints)
    alternative_routes = _generate_alternative_routes(origin, destination)
    
    # Score each route
    route_options: List[Dict[str, Any]] = []
    
    for idx, route_data in enumerate(alternative_routes):
        route_id = f"route_{chr(65 + idx)}"  # route_A, route_B, etc.
        
        # Create context for scanning
        context = RiskContext(
            commodity=commodity,
            cargo_value=cargo_value,
        )
        
        # Scan the route
        scan_result = scan_route(
            origin=origin,
            destination=route_data["waypoint"],  # Go via waypoint
            context=context,
        )
        
        # Check if route passes through hotspots
        avoids_hotspots = not _passes_through_hotspot(
            origin, 
            route_data["waypoint"], 
            destination
        )
        
        # Apply penalty if through hotspot
        adjusted_risk = scan_result.overall_risk
        if not avoids_hotspots:
            adjusted_risk = min(adjusted_risk * HOTSPOT_PENALTY, 10.0)
        
        route_option = RouteOption(
            route_id=route_id,
            name=route_data["name"],
            total_miles=route_data["distance"],
            estimated_hours=route_data["hours"],
            risk_score=round(adjusted_risk, 1),
            risk_level=scan_result.overall_level,
            red_zone_count=len(scan_result.red_zones),
            red_zones=[z.to_dict() for z in scan_result.red_zones],
            avoids_hotspots=avoids_hotspots,
            is_recommended=False,  # Set after sorting
            waypoints=[origin, route_data["waypoint"], destination],
        )
        
        route_options.append(route_option.to_dict())
        add_reasoning_step(
            state, 
            f"Scored {route_option.name}: {route_option.risk_score}/10, "
            f"{route_option.red_zone_count} red zones"
        )
    
    # Sort by risk (safest first)
    route_options.sort(key=lambda r: r["risk_score"])
    
    # Mark the safest as recommended
    if route_options:
        route_options[0]["is_recommended"] = True
    
    state["route_options"] = route_options
    add_reasoning_step(state, f"Generated {len(route_options)} route options")
    
    logger.info(f"Planner generated {len(route_options)} routes")
    return state


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _generate_alternative_routes(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
) -> List[Dict[str, Any]]:
    """
    Generate alternative routes via different waypoints.
    
    TODO: Replace with OSRM or Google Directions API for real routing.
    Current implementation creates mock alternatives.
    
    Args:
        origin: (lat, lon) of start
        destination: (lat, lon) of end
        
    Returns:
        List of route data with waypoints and estimated metrics
    """
    # Calculate direct distance
    direct_dist = _haversine_distance(origin, destination)
    
    # Midpoint
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    
    # Generate 3 alternatives with different waypoints
    routes = [
        {
            "name": f"Direct Route (I-35)",
            "waypoint": (mid_lat, mid_lon),  # Straight through
            "distance": direct_dist,
            "hours": direct_dist / 55,  # 55 mph average
        },
        {
            "name": f"Northern Bypass (I-40)",
            "waypoint": (mid_lat + 1.0, mid_lon - 0.5),  # North detour
            "distance": direct_dist * 1.15,  # 15% longer
            "hours": (direct_dist * 1.15) / 55,
        },
        {
            "name": f"Southern Route (I-20)",
            "waypoint": (mid_lat - 1.0, mid_lon + 0.5),  # South detour
            "distance": direct_dist * 1.10,  # 10% longer
            "hours": (direct_dist * 1.10) / 55,
        },
    ]
    
    return routes


def _passes_through_hotspot(
    origin: Tuple[float, float],
    waypoint: Tuple[float, float],
    destination: Tuple[float, float],
) -> bool:
    """
    Check if a route passes through any known theft hotspots.
    
    Args:
        origin: Start coordinates
        waypoint: Via coordinates
        destination: End coordinates
        
    Returns:
        True if route intersects any hotspot
    """
    # Check all points against hotspots
    points = [origin, waypoint, destination]
    
    for point in points:
        lat, lon = point
        for hotspot in THEFT_HOTSPOTS:
            bounds = hotspot["bounds"]
            if (bounds["lat_min"] <= lat <= bounds["lat_max"] and
                bounds["lon_min"] <= lon <= bounds["lon_max"]):
                logger.debug(f"Route passes through hotspot: {hotspot['name']}")
                return True
    
    return False


def _haversine_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> float:
    """Calculate distance between two GPS points in miles."""
    EARTH_RADIUS = 3958.8
    
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS * c


# =============================================================================
# FORMAT OUTPUT FOR DRIVER
# =============================================================================

def format_routes_for_driver(route_options: List[Dict[str, Any]]) -> str:
    """
    Format route options as a readable message for the driver.
    
    Args:
        route_options: List of route option dicts
        
    Returns:
        Formatted string for display
    """
    if not route_options:
        return "No routes available."
    
    lines = ["📍 **ROUTE OPTIONS** (ranked by safety)\n"]
    
    for i, route in enumerate(route_options):
        # Status indicator
        if route.get("is_recommended"):
            status = "✅ RECOMMENDED"
        elif route["risk_score"] >= 7:
            status = "🔴 HIGH RISK"
        elif route["risk_score"] >= 5:
            status = "🟡 CAUTION"
        else:
            status = "🟢 SAFE"
        
        lines.append(f"**[{route['route_id'].upper()}] {route['name']}** - {status}")
        lines.append(f"   Risk: {route['risk_score']}/10 | "
                    f"Distance: {route['total_miles']:.0f}mi | "
                    f"Time: {route['estimated_hours']:.1f}h")
        
        if route.get("red_zone_count", 0) > 0:
            lines.append(f"   ⚠️ {route['red_zone_count']} Red Zone(s)")
        
        if route.get("avoids_hotspots"):
            lines.append(f"   ✅ Avoids known theft hotspots")
        
        lines.append("")
    
    lines.append("**Select a route to continue.**")
    
    return "\n".join(lines)


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    from safetravels.agents.state import create_initial_state, TripRequest
    
    print("=" * 70)
    print("SafeTravels Planner - Test")
    print("=" * 70)
    
    # Create test trip
    trip = TripRequest(
        origin_lat=32.7767,
        origin_lon=-96.7970,      # Dallas
        destination_lat=41.8781,
        destination_lon=-87.6298,  # Chicago
        commodity="electronics",
        cargo_value=250000,
    )
    
    state = create_initial_state(
        query="Plan safest route from Dallas to Chicago",
        trip_request=trip,
    )
    
    # Run planner
    state = plan_routes(state)
    
    # Display results
    print("\n" + format_routes_for_driver(state["route_options"]))
    
    print("\n--- Reasoning Chain ---")
    for step in state["reasoning_chain"]:
        print(f"  {step}")
    
    print("\n" + "=" * 70)
    print("✅ Planner test complete!")
    print("=" * 70)
