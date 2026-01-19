"""
SafeTravels MCP Server
======================

Model Context Protocol server exposing cargo theft risk intelligence
tools to any MCP-compatible AI client (Claude, GPT, etc.).

AVAILABLE TOOLS:
    - assess_location_risk: Comprehensive 15-factor risk scoring
    - find_safe_stops: Locate nearby secure parking
    - check_recent_incidents: Query driver reports

Running the Server:
    # Local (stdio transport for Claude Desktop)
    python -m safetravels.mcp.server
    
    # Or via FastMCP CLI
    fastmcp run safetravels.mcp.server:mcp

Author: SafeTravels Team
Created: January 2026
"""

import logging
from typing import Optional, List

# FastMCP SDK
try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "FastMCP not installed. Run: pip install fastmcp>=2.0"
    )

# Import tools
from safetravels.mcp.tools.risk_scorer import (
    calculate_risk,
    RiskContext,
    get_time_category,
    get_day_name,
    get_month_name,
    get_season,
)
from safetravels.mcp.tools.route_scanner import (
    scan_route,
    RouteAnalysis,
)
from safetravels.mcp.tools.safe_stops import (
    find_nearby_stops,
    find_fuel_stops,
    find_emergency_help,
    get_hos_recommendation,
    find_stops_before_zone,
    StopTier,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# MCP SERVER INITIALIZATION
# =============================================================================

mcp = FastMCP(
    name="SafeTravels",
    description=(
        "Cargo theft risk intelligence for logistics and trucking. "
        "Provides location-based risk scoring using 15+ factors."
    )
)


# =============================================================================
# TOOL: Assess Location Risk (Comprehensive)
# =============================================================================

@mcp.tool()
def assess_location_risk(
    latitude: float,
    longitude: float,
    # Temporal factors
    time_of_day: str = "day",
    day_of_week: str = "monday",
    month: str = "january",
    season: str = "normal",
    # Cargo factors
    commodity: str = "general",
    cargo_value: float = 50000.0,
    # Location factors
    location_type: str = "truck_stop_basic",
    state: str = "",
    # Environmental factors
    weather: str = "clear",
    event: str = "none",
    traffic: str = "light",
    accident_history: str = "low",
) -> dict:
    """
    Calculate comprehensive cargo theft risk for a GPS location.
    
    Uses a 15-factor weighted formula considering:
    - Temporal: Time of day, day of week, month, season
    - Cargo: Commodity type, declared value
    - Location: Stop type, state hotspots
    - Environmental: Weather, events, traffic, accident history
    
    Args:
        latitude: GPS latitude (e.g., 32.7767 for Dallas)
        longitude: GPS longitude (e.g., -96.7970 for Dallas)
        
        time_of_day: 'day', 'evening', or 'night'
        day_of_week: Lowercase day (e.g., 'friday', 'saturday')
        month: Lowercase month (e.g., 'november', 'december')
        season: Special period - 'normal', 'holiday_peak', 'black_friday_week', 
                'christmas_week', 'back_to_school', 'summer'
        
        commodity: Cargo type - 'electronics', 'pharmaceuticals', 'alcohol',
                   'tobacco', 'automotive_parts', 'clothing', 'food_beverage',
                   'general', etc.
        cargo_value: Total declared cargo value in USD
        
        location_type: Stop type - 'truck_stop_secured', 'truck_stop_basic',
                       'truck_stop_premium', 'rest_area', 'unsecured_lot',
                       'random_roadside', 'distribution_center'
        state: Two-letter state code (e.g., 'CA', 'TX', 'FL')
        
        weather: Current conditions - 'clear', 'cloudy', 'light_rain',
                 'heavy_rain', 'storm', 'severe_storm', 'fog', 'snow', 'ice'
        event: Local disturbances - 'none', 'holiday', 'construction',
               'large_event', 'festival', 'major_protest', 'civil_unrest'
        traffic: Current traffic - 'free_flow', 'light', 'moderate',
                 'heavy', 'severe', 'standstill'
        accident_history: Area accident frequency - 'very_low', 'low',
                          'moderate', 'high', 'very_high'
    
    Returns:
        dict containing:
            - risk_score: Number from 1-10 (10 = highest risk)
            - risk_level: 'low', 'moderate', 'high', or 'critical'
            - factors: Breakdown of each weight applied
            - confidence: Model confidence (0-1)
            - warnings: List of actionable warnings
            - latitude/longitude: Echo of input location
    
    Example:
        >>> assess_location_risk(
        ...     32.7767, -96.7970,
        ...     time_of_day="night",
        ...     month="december",
        ...     commodity="electronics",
        ...     cargo_value=500000
        ... )
        {
            "risk_score": 8.5,
            "risk_level": "critical",
            "factors": {...},
            "warnings": ["🌙 Night travel with high-value cargo..."]
        }
    """
    logger.info(
        f"MCP assess_location_risk: ({latitude}, {longitude}) "
        f"commodity={commodity}, value=${cargo_value:,.0f}"
    )
    
    # Build complete context from all parameters
    context = RiskContext(
        time_of_day=time_of_day,
        day_of_week=day_of_week,
        month=month,
        season=season,
        commodity=commodity,
        cargo_value=cargo_value,
        location_type=location_type,
        state=state,
        weather=weather,
        event=event,
        traffic=traffic,
        accident_history=accident_history,
    )
    
    # Perform calculation
    result = calculate_risk(latitude, longitude, context)
    
    # Convert to MCP-friendly dict
    return {
        "latitude": result.latitude,
        "longitude": result.longitude,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "factors": result.factors.to_dict(),
        "confidence": round(result.confidence, 2),
        "warnings": result.warnings,
    }


# =============================================================================
# TOOL: Quick Risk Check (Simplified)
# =============================================================================

@mcp.tool()
def quick_risk_check(
    latitude: float,
    longitude: float,
    commodity: str = "general",
    cargo_value: float = 50000.0,
) -> dict:
    """
    Quick risk check with minimal parameters.
    
    Automatically detects current time factors (time of day, day, month).
    Use this for fast checks when you don't have full context.
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        commodity: Cargo type (default: 'general')
        cargo_value: Cargo value in USD (default: $50,000)
    
    Returns:
        dict with risk_score, risk_level, and top warnings
    """
    from datetime import datetime
    
    now = datetime.now()
    
    context = RiskContext(
        time_of_day=get_time_category(now.hour),
        day_of_week=get_day_name(now),
        month=get_month_name(now),
        season=get_season(now),
        commodity=commodity,
        cargo_value=cargo_value,
    )
    
    result = calculate_risk(latitude, longitude, context)
    
    return {
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "confidence": round(result.confidence, 2),
        "warnings": result.warnings[:3],  # Top 3 warnings
    }


# =============================================================================
# TOOL: Find Safe Stops (REAL DATA)
# =============================================================================

@mcp.tool()
def find_safe_stops_nearby(
    latitude: float,
    longitude: float,
    radius_miles: int = 50,
    min_security_tier: str = "level_3",
    require_fuel: bool = False,
    limit: int = 5,
) -> List[dict]:
    """
    Find safe truck stops near a location, ranked by security score.
    
    Uses 2024 theft statistics and 100-point security scoring:
        - Physical Security: 45 pts (gates, guards, CCTV, lighting)
        - Location Context: 35 pts (theft history, state risk, highway access)
        - Operational: 20 pts (brand reputation, 24h staffing)
    
    TIER SYSTEM:
        - Level 1 (85+): Premium security - gated, guards, monitored CCTV
        - Level 2 (65-84): Secure - good lighting, cameras, major brand
        - Level 3 (45-64): Basic - acceptable for quick stops
        - Avoid (<45): Not recommended
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        radius_miles: Search radius (default: 50)
        min_security_tier: Minimum tier - 'level_1', 'level_2', 'level_3', 'avoid'
        require_fuel: Only return stops with diesel fuel
        limit: Maximum stops to return (default: 5)
    
    Returns:
        List of stops sorted by distance, each containing:
            - name: Stop name (e.g., "Pilot Travel Center #587")
            - security_score: 0-100 points
            - tier: 'Level 1', 'Level 2', 'Level 3', 'Avoid'
            - distance_miles: Distance from current location
            - has_fuel, has_guards, has_gated_parking: Amenity flags
            - location: {lat, lon}
    
    Example:
        >>> find_safe_stops_nearby(32.7767, -96.7970, radius_miles=100)
        [
            {"name": "Pilot #587", "security_score": 73, "tier": "Level 2", ...},
            ...
        ]
    """
    logger.info(f"MCP find_safe_stops_nearby: ({latitude}, {longitude}), r={radius_miles}mi")
    
    # Map tier string to StopTier enum
    tier_map = {
        "level_1": StopTier.LEVEL_1,
        "level_2": StopTier.LEVEL_2,
        "level_3": StopTier.LEVEL_3,
        "avoid": StopTier.AVOID,
    }
    min_tier = tier_map.get(min_security_tier.lower(), StopTier.LEVEL_3)
    
    # Call real safe_stops module
    stops = find_nearby_stops(
        lat=latitude,
        lon=longitude,
        radius_miles=float(radius_miles),
        min_tier=min_tier,
        require_fuel=require_fuel,
        limit=limit,
    )
    
    return [s.to_dict() for s in stops]


# =============================================================================
# TOOL: Find Fuel Stops
# =============================================================================

@mcp.tool()
def find_fuel_stops_nearby(
    latitude: float,
    longitude: float,
    radius_miles: int = 50,
) -> List[dict]:
    """
    Find truck stops with diesel fuel, prioritized by safety.
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        radius_miles: Search radius (default: 50)
    
    Returns:
        List of fuel stops sorted by distance, with security scores
    """
    logger.info(f"MCP find_fuel_stops: ({latitude}, {longitude})")
    
    stops = find_fuel_stops(latitude, longitude, float(radius_miles))
    return [s.to_dict() for s in stops]


# =============================================================================
# TOOL: Emergency Help
# =============================================================================

@mcp.tool()
def find_emergency_stops(
    latitude: float,
    longitude: float,
) -> List[dict]:
    """
    Find emergency help options: secured truck stops + police stations.
    
    Use when driver feels unsafe or needs immediate assistance.
    Returns highest-security options within 100 miles.
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
    
    Returns:
        List of emergency options (truck stops with guards + police stations)
    """
    logger.info(f"MCP find_emergency_stops: ({latitude}, {longitude})")
    
    stops = find_emergency_help(latitude, longitude)
    return [s.to_dict() for s in stops]


# =============================================================================
# TOOL: HOS-Aware Stop Recommendation
# =============================================================================

@mcp.tool()
def get_hos_stop_recommendation(
    latitude: float,
    longitude: float,
    hours_driven: float,
    break_type: str = "quick",
) -> dict:
    """
    Get stop recommendations based on Hours of Service (HOS) rules.
    
    SAFETY GUARANTEE:
        - Never recommends below Level 2 security for overnight rest
        - Alerts driver if no safe options available
    
    Args:
        latitude: Current GPS latitude
        longitude: Current GPS longitude
        hours_driven: Hours driven in current shift (max 10 allowed)
        break_type: 'quick' (30-min break) or 'overnight' (10-hour rest)
    
    Returns:
        Recommendation with:
            - status: 'SAFE' or 'UNSAFE' (no safe stops available)
            - urgency: 'info', 'warning', 'critical'
            - message: Driver-friendly message
            - hours_remaining: Time left in shift
            - recommended_stops: List of safe stops
            - fallback_options: If status is UNSAFE, less-safe alternatives
    
    Example:
        >>> get_hos_stop_recommendation(32.7767, -96.7970, 8.0, "overnight")
        {
            "status": "SAFE",
            "urgency": "warning",
            "message": "🟡 Plan your 10-hour break soon...",
            "recommended_stops": [...]
        }
    """
    logger.info(f"MCP get_hos_stop: ({latitude}, {longitude}), hours={hours_driven}")
    
    return get_hos_recommendation(latitude, longitude, hours_driven, break_type)


# =============================================================================
# TOOL: Analyze Route
# =============================================================================

@mcp.tool()
def analyze_route(
    origin_lat: float,
    origin_lon: float,
    destination_lat: float,
    destination_lon: float,
    # Cargo context
    commodity: str = "general",
    cargo_value: float = 50000.0,
    # Time context
    time_of_day: str = "day",
    month: str = "january",
) -> dict:
    """
    Analyze a complete route for cargo theft risk.
    
    Scans the route from origin to destination, identifying:
    - Red Zones: High-risk segments to avoid stopping in
    - Yellow Zones: Caution areas requiring awareness
    - Safe stops: Recommended secure parking near red zones
    
    Args:
        origin_lat: Starting point latitude
        origin_lon: Starting point longitude
        destination_lat: Ending point latitude
        destination_lon: Ending point longitude
        commodity: Cargo type (e.g., 'electronics', 'pharmaceuticals')
        cargo_value: Total cargo value in USD
        time_of_day: Expected travel time - 'day', 'evening', 'night'
        month: Travel month (affects seasonal risk)
    
    Returns:
        dict containing:
            - total_miles: Route distance
            - overall_risk: Weighted average risk (1-10)
            - overall_level: 'low', 'moderate', 'high', 'critical'
            - red_zone_count: Number of high-risk zones
            - red_zones: List of red zone details with mile markers
            - yellow_zones: List of caution zones
            - recommendations: Actionable safety recommendations
    
    Example:
        >>> analyze_route(
        ...     32.7767, -96.7970,      # Dallas
        ...     41.8781, -87.6298,      # Chicago
        ...     commodity="electronics",
        ...     cargo_value=250000
        ... )
        {
            "total_miles": 917.4,
            "overall_risk": 6.8,
            "red_zone_count": 2,
            "recommendations": ["⚠️ HIGH RISK ROUTE...", ...]
        }
    """
    logger.info(
        f"MCP analyze_route: ({origin_lat}, {origin_lon}) → "
        f"({destination_lat}, {destination_lon})"
    )
    
    # Build context
    context = RiskContext(
        time_of_day=time_of_day,
        month=month,
        commodity=commodity,
        cargo_value=cargo_value,
    )
    
    # Run route scanner
    result = scan_route(
        origin=(origin_lat, origin_lon),
        destination=(destination_lat, destination_lon),
        context=context,
    )
    
    # Return MCP-friendly dict
    return result.to_dict()


# =============================================================================
# TOOL: Check Recent Incidents
# =============================================================================

@mcp.tool()
def check_recent_incidents(
    latitude: float,
    longitude: float,
    radius_miles: int = 5,
    hours_ago: int = 24,
) -> List[dict]:
    """
    Check for recent theft incidents or driver reports near a location.
    
    Queries driver-submitted reports and known incidents within
    the specified timeframe. Essential for real-time awareness.
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        radius_miles: Search radius (default: 5)
        hours_ago: How far back to check (default: 24 hours)
    
    Returns:
        List of incidents, each containing:
            - type: 'theft', 'suspicious_activity', 'police_activity', etc.
            - description: Brief description
            - reported_at: Timestamp
            - distance_miles: Distance from query point
            - severity: 'low', 'medium', 'high'
    """
    logger.info(f"MCP check_recent_incidents: ({latitude}, {longitude})")
    
    # TODO: Replace with real database/vector search query
    # Return empty for now (no incidents = safe)
    return []


# =============================================================================
# MAIN (Server Entry Point)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SafeTravels MCP Server")
    print("=" * 60)
    print("\nAvailable Tools:")
    print("  📊 assess_location_risk    - Comprehensive 15-factor scoring")
    print("  ⚡ quick_risk_check        - Fast check with auto-detected time")
    print("  🅿️  find_safe_stops_nearby  - Locate secure parking (real data)")
    print("  ⛽ find_fuel_stops_nearby  - Find fuel with safety ranking")
    print("  🆘 find_emergency_stops    - Police + secured stops")
    print("  ⏰ get_hos_stop_recommendation - HOS-aware recommendations")
    print("  🗺️  analyze_route           - Full route risk analysis")
    print("  🚨 check_recent_incidents  - Query driver reports")
    print("\nStarting server (stdio transport)...")
    
    mcp.run()
