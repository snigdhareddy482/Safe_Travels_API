"""
SafeTravels MCP Tools - Route Scanner
======================================

Scans a complete route from origin to destination, identifying
high-risk segments ("Red Zones") and calculating overall route risk.

PROCESS:
    1. Generate sample points along the route (every N miles)
    2. Calculate risk at each point using the 15-factor formula
    3. Aggregate segments into risk zones
    4. Identify Red Zones (score >= RED_ZONE_THRESHOLD)
    5. Find safe stops near Red Zones as alternatives

USAGE:
    from safetravels.mcp.tools.route_scanner import scan_route
    
    result = scan_route(
        origin=(32.7767, -96.7970),      # Dallas
        destination=(41.8781, -87.6298),  # Chicago
        commodity="electronics",
        cargo_value=250000
    )
    
    print(f"Overall Risk: {result.overall_risk}/10")
    print(f"Red Zones: {len(result.red_zones)}")

Design Principles:
    - Uses existing risk_scorer for consistency
    - Mock route interpolation (replace with OSRM later)
    - Efficient: batch processing of segments

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import math
import logging

from safetravels.mcp.tools.risk_scorer import (
    calculate_risk,
    RiskContext,
    RiskAssessment,
    get_time_category,
    get_day_name,
    get_month_name,
    get_season,
)
from safetravels.mcp import risk_model_weights as config
from safetravels.mcp.risk_model_weights import get_route_length_multiplier

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Distance between sample points (in miles)
SAMPLE_INTERVAL_MILES: float = 20.0

# Threshold for Red Zone classification
RED_ZONE_THRESHOLD: float = 7.0

# Threshold for Yellow Zone (caution)
YELLOW_ZONE_THRESHOLD: float = 5.0

# Maximum segments to analyze (performance limit)
MAX_SEGMENTS: int = 100

# Earth's radius in miles (for distance calculations)
EARTH_RADIUS_MILES: float = 3958.8


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RouteSegment:
    """
    A single segment of the route with risk assessment.
    
    Attributes:
        segment_id: Sequential ID (1, 2, 3, ...)
        latitude: Segment center latitude
        longitude: Segment center longitude
        mile_marker: Distance from origin
        risk_score: Calculated risk (1-10)
        risk_level: 'low', 'moderate', 'high', 'critical'
        zone_type: 'green', 'yellow', or 'red'
        warnings: Specific warnings for this segment
    """
    segment_id: int
    latitude: float
    longitude: float
    mile_marker: float
    risk_score: float
    risk_level: str
    zone_type: str
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "segment_id": self.segment_id,
            "latitude": round(self.latitude, 4),
            "longitude": round(self.longitude, 4),
            "mile_marker": round(self.mile_marker, 1),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "zone_type": self.zone_type,
            "warnings": self.warnings,
        }


@dataclass
class RedZone:
    """
    A high-risk zone requiring driver attention.
    
    Attributes:
        start_mile: Mile marker where zone begins
        end_mile: Mile marker where zone ends
        peak_risk: Highest risk score in zone
        center_lat: Center latitude
        center_lon: Center longitude
        description: Human-readable description
        recommended_action: What the driver should do
        nearby_safe_stops: Safe alternatives near this zone
    """
    start_mile: float
    end_mile: float
    peak_risk: float
    center_lat: float
    center_lon: float
    description: str
    recommended_action: str
    nearby_safe_stops: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_mile": round(self.start_mile, 1),
            "end_mile": round(self.end_mile, 1),
            "length_miles": round(self.end_mile - self.start_mile, 1),
            "peak_risk": self.peak_risk,
            "center": {
                "latitude": round(self.center_lat, 4),
                "longitude": round(self.center_lon, 4),
            },
            "description": self.description,
            "recommended_action": self.recommended_action,
            "nearby_safe_stops": self.nearby_safe_stops,
        }


@dataclass
class RouteAnalysis:
    """
    Complete analysis of a route.
    
    Attributes:
        origin: Origin coordinates
        destination: Destination coordinates
        total_miles: Total route distance
        overall_risk: Weighted average risk score
        overall_level: 'low', 'moderate', 'high', 'critical'
        segments: All analyzed segments
        red_zones: High-risk zones requiring attention
        yellow_zones: Moderate-risk zones (caution)
        recommendations: Overall route recommendations
    """
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    total_miles: float
    overall_risk: float
    overall_level: str
    segments: List[RouteSegment]
    red_zones: List[RedZone]
    yellow_zones: List[RedZone]
    recommendations: List[str]
    analyzed_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "origin": {
                "latitude": self.origin[0],
                "longitude": self.origin[1],
            },
            "destination": {
                "latitude": self.destination[0],
                "longitude": self.destination[1],
            },
            "total_miles": round(self.total_miles, 1),
            "overall_risk": self.overall_risk,
            "overall_level": self.overall_level,
            "segment_count": len(self.segments),
            "red_zone_count": len(self.red_zones),
            "yellow_zone_count": len(self.yellow_zones),
            "red_zones": [z.to_dict() for z in self.red_zones],
            "yellow_zones": [z.to_dict() for z in self.yellow_zones],
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at,
        }


# =============================================================================
# CORE FUNCTION
# =============================================================================

def scan_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    context: Optional[RiskContext] = None,
    sample_interval: float = SAMPLE_INTERVAL_MILES,
) -> RouteAnalysis:
    """
    Scan a complete route and identify risk zones.
    
    This function:
        1. Calculates route distance
        2. Generates sample points along the route
        3. Assesses risk at each point
        4. Groups high-risk segments into Red Zones
        5. Provides recommendations
    
    Args:
        origin: Tuple of (latitude, longitude) for start
        destination: Tuple of (latitude, longitude) for end
        context: Optional RiskContext with cargo/time info.
                 If not provided, uses current time and defaults.
        sample_interval: Distance between samples in miles (default: 20)
    
    Returns:
        RouteAnalysis with segments, red zones, and recommendations.
    
    Example:
        >>> result = scan_route(
        ...     origin=(32.7767, -96.7970),      # Dallas
        ...     destination=(41.8781, -87.6298),  # Chicago
        ...     context=RiskContext(commodity="electronics", cargo_value=250000)
        ... )
        >>> print(f"Red Zones: {len(result.red_zones)}")
    """
    logger.info(
        f"Scanning route: {origin} → {destination}"
    )
    
    # ---------------------------------------------------------------------
    # STEP 1: Calculate total distance
    # ---------------------------------------------------------------------
    total_miles = _calculate_distance(origin, destination)
    logger.debug(f"Total distance: {total_miles:.1f} miles")
    
    # ---------------------------------------------------------------------
    # STEP 2: Generate sample points along route
    # ---------------------------------------------------------------------
    sample_points = _interpolate_route(origin, destination, sample_interval)
    logger.debug(f"Generated {len(sample_points)} sample points")
    
    # Limit segments for performance
    if len(sample_points) > MAX_SEGMENTS:
        sample_points = sample_points[:MAX_SEGMENTS]
        logger.warning(f"Truncated to {MAX_SEGMENTS} segments")
    
    # ---------------------------------------------------------------------
    # STEP 3: Build context (use provided or create from current time)
    # ---------------------------------------------------------------------
    if context is None:
        now = datetime.now()
        context = RiskContext(
            time_of_day=get_time_category(now.hour),
            day_of_week=get_day_name(now),
            month=get_month_name(now),
            season=get_season(now),
        )
    
    # ---------------------------------------------------------------------
    # STEP 4: Assess risk at each sample point
    # ---------------------------------------------------------------------
    segments: List[RouteSegment] = []
    
    for idx, (lat, lon, mile_marker) in enumerate(sample_points, start=1):
        # Determine state from coordinates (mock)
        state = _get_state_from_coords(lat, lon)
        context.state = state
        
        # Calculate risk
        assessment = calculate_risk(lat, lon, context)
        
        # Determine zone type
        if assessment.risk_score >= RED_ZONE_THRESHOLD:
            zone_type = "red"
        elif assessment.risk_score >= YELLOW_ZONE_THRESHOLD:
            zone_type = "yellow"
        else:
            zone_type = "green"
        
        segment = RouteSegment(
            segment_id=idx,
            latitude=lat,
            longitude=lon,
            mile_marker=mile_marker,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level,
            zone_type=zone_type,
            warnings=assessment.warnings[:2],  # Top 2 warnings per segment
        )
        segments.append(segment)
    
    # ---------------------------------------------------------------------
    # STEP 5: Group segments into Red and Yellow Zones
    # ---------------------------------------------------------------------
    red_zones = _identify_zones(segments, "red")
    yellow_zones = _identify_zones(segments, "yellow")
    
    # ---------------------------------------------------------------------
    # STEP 6: Calculate overall route risk
    # ---------------------------------------------------------------------
    if segments:
        # Weighted average (red zones count more)
        total_weight = 0
        weighted_sum = 0
        for seg in segments:
            weight = 2.0 if seg.zone_type == "red" else 1.0
            weighted_sum += seg.risk_score * weight
            total_weight += weight
        overall_risk = round(weighted_sum / total_weight, 1)
    else:
        overall_risk = 5.0  # Default if no segments
    
    # Apply route length multiplier
    length_multiplier = get_route_length_multiplier(total_miles)
    overall_risk = min(overall_risk * length_multiplier, 10.0)
    overall_risk = round(overall_risk, 1)
    
    # Determine overall level
    if overall_risk <= 3.0:
        overall_level = "low"
    elif overall_risk <= 5.0:
        overall_level = "moderate"
    elif overall_risk <= 7.0:
        overall_level = "high"
    else:
        overall_level = "critical"
    
    # ---------------------------------------------------------------------
    # STEP 7: Generate recommendations
    # ---------------------------------------------------------------------
    recommendations = _generate_route_recommendations(
        overall_risk, red_zones, yellow_zones, total_miles
    )
    
    return RouteAnalysis(
        origin=origin,
        destination=destination,
        total_miles=round(total_miles, 1),
        overall_risk=overall_risk,
        overall_level=overall_level,
        segments=segments,
        red_zones=red_zones,
        yellow_zones=yellow_zones,
        recommendations=recommendations,
        analyzed_at=datetime.utcnow().isoformat(),
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _calculate_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> float:
    """
    Calculate distance between two GPS coordinates (Haversine formula).
    
    Args:
        point1: (latitude, longitude) of first point
        point2: (latitude, longitude) of second point
        
    Returns:
        Distance in miles
    """
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_MILES * c


def _interpolate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    interval_miles: float
) -> List[Tuple[float, float, float]]:
    """
    Generate sample points along a route.
    
    TODO: Replace with OSRM API for actual road routing.
    Current implementation uses straight-line interpolation.
    
    Args:
        origin: (lat, lon) of start
        destination: (lat, lon) of end
        interval_miles: Distance between samples
        
    Returns:
        List of (lat, lon, mile_marker) tuples
    """
    total_distance = _calculate_distance(origin, destination)
    num_points = max(2, int(total_distance / interval_miles) + 1)
    
    points = []
    for i in range(num_points):
        fraction = i / (num_points - 1) if num_points > 1 else 0
        
        lat = origin[0] + fraction * (destination[0] - origin[0])
        lon = origin[1] + fraction * (destination[1] - origin[1])
        mile_marker = fraction * total_distance
        
        points.append((lat, lon, mile_marker))
    
    return points


def _get_state_from_coords(lat: float, lon: float) -> str:
    """
    Get US state code from coordinates.
    
    TODO: Replace with reverse geocoding API.
    Current implementation uses rough bounding boxes.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Two-letter state code
    """
    # Rough state boundaries (very simplified)
    STATE_BOUNDS = [
        ("CA", 32.5, 42.0, -124.5, -114.0),
        ("TX", 25.8, 36.5, -106.6, -93.5),
        ("FL", 24.5, 31.0, -87.6, -80.0),
        ("IL", 36.9, 42.5, -91.5, -87.0),
        ("GA", 30.3, 35.0, -85.6, -80.8),
        ("AZ", 31.3, 37.0, -114.8, -109.0),
        ("NM", 31.3, 37.0, -109.0, -103.0),
        ("OK", 33.6, 37.0, -103.0, -94.4),
    ]
    
    for state, lat_min, lat_max, lon_min, lon_max in STATE_BOUNDS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return state
    
    return ""  # Unknown state


def _identify_zones(
    segments: List[RouteSegment],
    zone_type: str
) -> List[RedZone]:
    """
    Group consecutive segments of the same zone type.
    
    Args:
        segments: List of all route segments
        zone_type: 'red' or 'yellow'
        
    Returns:
        List of grouped zones
    """
    zones = []
    current_zone_segments = []
    
    for segment in segments:
        if segment.zone_type == zone_type:
            current_zone_segments.append(segment)
        else:
            if current_zone_segments:
                zones.append(_create_zone(current_zone_segments, zone_type))
                current_zone_segments = []
    
    # Don't forget the last zone
    if current_zone_segments:
        zones.append(_create_zone(current_zone_segments, zone_type))
    
    return zones


def _create_zone(
    segments: List[RouteSegment],
    zone_type: str
) -> RedZone:
    """
    Create a zone from a group of consecutive segments.
    
    Args:
        segments: Consecutive segments in this zone
        zone_type: 'red' or 'yellow'
        
    Returns:
        RedZone object
    """
    start_mile = segments[0].mile_marker
    end_mile = segments[-1].mile_marker
    peak_risk = max(s.risk_score for s in segments)
    
    # Center of zone
    center_idx = len(segments) // 2
    center_lat = segments[center_idx].latitude
    center_lon = segments[center_idx].longitude
    
    # Description based on zone type
    if zone_type == "red":
        description = f"High-risk zone from mile {start_mile:.0f} to {end_mile:.0f}"
        action = "Avoid stopping in this area. Proceed through quickly if possible."
    else:
        description = f"Caution zone from mile {start_mile:.0f} to {end_mile:.0f}"
        action = "Maintain awareness. Stop only at secured locations."
    
    return RedZone(
        start_mile=start_mile,
        end_mile=end_mile,
        peak_risk=peak_risk,
        center_lat=center_lat,
        center_lon=center_lon,
        description=description,
        recommended_action=action,
        nearby_safe_stops=[],  # TODO: Query safe stops near this zone
    )


def _generate_route_recommendations(
    overall_risk: float,
    red_zones: List[RedZone],
    yellow_zones: List[RedZone],
    total_miles: float
) -> List[str]:
    """
    Generate actionable recommendations for the route.
    
    Args:
        overall_risk: Overall route risk score
        red_zones: List of red zones
        yellow_zones: List of yellow zones
        total_miles: Total route distance
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Based on overall risk
    if overall_risk >= 8.0:
        recommendations.append(
            "⚠️ CRITICAL ROUTE: Consider alternative routing or additional security."
        )
    elif overall_risk >= 6.0:
        recommendations.append(
            "⚠️ HIGH RISK ROUTE: Plan stops carefully and maintain communication."
        )
    
    # Based on red zones
    if len(red_zones) > 0:
        recommendations.append(
            f"🔴 {len(red_zones)} RED ZONE(S) detected. "
            f"Avoid stopping in these areas."
        )
    
    # Based on yellow zones
    if len(yellow_zones) > 3:
        recommendations.append(
            "🟡 Multiple caution zones. Stay alert throughout the route."
        )
    
    # Based on route length
    if total_miles > 1000:
        recommendations.append(
            "📏 Long haul (1000+ miles). Plan multiple secured rest stops."
        )
    elif total_miles > 500:
        recommendations.append(
            "📏 Regional haul. Plan at least one secured rest stop."
        )
    
    # General safety
    recommendations.append(
        "✅ Keep dispatch informed of your location and any unusual activity."
    )
    
    return recommendations


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Route Scanner - Test")
    print("=" * 70)
    
    # Test route: Dallas to Chicago
    origin = (32.7767, -96.7970)      # Dallas, TX
    destination = (41.8781, -87.6298)  # Chicago, IL
    
    print(f"\nRoute: Dallas, TX → Chicago, IL")
    
    # Create context with high-value electronics
    context = RiskContext(
        time_of_day="night",
        month="december",
        commodity="electronics",
        cargo_value=250000,
    )
    
    result = scan_route(origin, destination, context)
    
    print(f"\n--- Results ---")
    print(f"Total Distance: {result.total_miles} miles")
    print(f"Segments Analyzed: {len(result.segments)}")
    print(f"Overall Risk: {result.overall_risk}/10 ({result.overall_level})")
    print(f"Red Zones: {len(result.red_zones)}")
    print(f"Yellow Zones: {len(result.yellow_zones)}")
    
    if result.red_zones:
        print("\n--- Red Zones ---")
        for zone in result.red_zones:
            print(f"  Mile {zone.start_mile:.0f}-{zone.end_mile:.0f}: "
                  f"Peak Risk {zone.peak_risk}/10")
    
    print("\n--- Recommendations ---")
    for rec in result.recommendations:
        print(f"  {rec}")
    
    print("\n" + "=" * 70)
    print("✅ Route Scanner test complete!")
    print("=" * 70)
