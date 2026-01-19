"""
SafeTravels MCP Tools - Red Zone Checker
=========================================

Monitors driver position relative to upcoming Red Zones and triggers
alerts when approaching (200-mile countdown) or entering danger areas.

FEATURES:
    - Distance to next Red Zone calculation
    - 200-mile warning threshold
    - Estimated time to Red Zone
    - Real-time alert generation

USAGE:
    from safetravels.mcp.tools.red_zone_checker import check_red_zone_proximity
    
    alert = check_red_zone_proximity(
        current_lat=35.5,
        current_lon=-95.0,
        red_zones=[...],  # From route_scanner
        speed_mph=65
    )
    
    if alert.should_alert:
        send_notification(alert.message)

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Distance thresholds for alerts (in miles)
ALERT_THRESHOLD_CRITICAL: float = 50.0    # Imminent danger
ALERT_THRESHOLD_WARNING: float = 100.0    # Warning level
ALERT_THRESHOLD_CAUTION: float = 200.0    # Initial heads-up

# Default speed assumption if not provided
DEFAULT_SPEED_MPH: float = 55.0

# Earth's radius in miles
EARTH_RADIUS_MILES: float = 3958.8


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RedZoneAlert:
    """
    Alert generated when approaching a Red Zone.
    
    Attributes:
        should_alert: Whether to trigger notification
        alert_level: 'critical', 'warning', 'caution', or 'safe'
        distance_miles: Distance to nearest Red Zone
        estimated_minutes: ETA to Red Zone at current speed
        zone_name: Description of the Red Zone
        message: Human-readable alert message
        recommended_action: What the driver should do
    """
    should_alert: bool
    alert_level: str
    distance_miles: float
    estimated_minutes: float
    zone_name: str
    message: str
    recommended_action: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "should_alert": self.should_alert,
            "alert_level": self.alert_level,
            "distance_miles": round(self.distance_miles, 1),
            "estimated_minutes": round(self.estimated_minutes, 0),
            "zone_name": self.zone_name,
            "message": self.message,
            "recommended_action": self.recommended_action,
        }


@dataclass
class RedZoneInfo:
    """
    Simplified Red Zone info for proximity checking.
    
    Attributes:
        start_mile: Mile marker where zone begins
        center_lat: Center latitude
        center_lon: Center longitude
        peak_risk: Highest risk score in zone
        description: Zone description
    """
    start_mile: float
    center_lat: float
    center_lon: float
    peak_risk: float
    description: str


# =============================================================================
# CORE FUNCTION
# =============================================================================

def check_red_zone_proximity(
    current_lat: float,
    current_lon: float,
    red_zones: List[Dict[str, Any]],
    speed_mph: float = DEFAULT_SPEED_MPH,
    heading_towards_destination: bool = True,
) -> RedZoneAlert:
    """
    Check if driver is approaching a Red Zone.
    
    Calculates distance to each Red Zone and returns alert
    if within threshold distance.
    
    Args:
        current_lat: Driver's current latitude
        current_lon: Driver's current longitude
        red_zones: List of Red Zone dicts from route_scanner
        speed_mph: Current driving speed (for ETA calculation)
        heading_towards_destination: Direction of travel
    
    Returns:
        RedZoneAlert with proximity info and recommendations.
    
    Example:
        >>> zones = [{"center": {"latitude": 36.0, "longitude": -95.0}, ...}]
        >>> alert = check_red_zone_proximity(35.5, -95.0, zones)
        >>> if alert.should_alert:
        ...     print(alert.message)
    """
    logger.debug(f"Checking red zone proximity: ({current_lat}, {current_lon})")
    
    if not red_zones:
        return _create_safe_alert()
    
    # Find nearest Red Zone
    nearest_distance = float('inf')
    nearest_zone = None
    
    for zone in red_zones:
        # Extract center coordinates
        center = zone.get("center", {})
        zone_lat = center.get("latitude", 0)
        zone_lon = center.get("longitude", 0)
        
        # Calculate distance
        distance = _haversine_distance(
            (current_lat, current_lon),
            (zone_lat, zone_lon)
        )
        
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_zone = zone
    
    if nearest_zone is None:
        return _create_safe_alert()
    
    # Determine alert level based on distance
    if nearest_distance <= ALERT_THRESHOLD_CRITICAL:
        alert_level = "critical"
        should_alert = True
    elif nearest_distance <= ALERT_THRESHOLD_WARNING:
        alert_level = "warning"
        should_alert = True
    elif nearest_distance <= ALERT_THRESHOLD_CAUTION:
        alert_level = "caution"
        should_alert = True
    else:
        alert_level = "safe"
        should_alert = False
    
    # Calculate ETA
    if speed_mph > 0:
        eta_minutes = (nearest_distance / speed_mph) * 60
    else:
        eta_minutes = float('inf')
    
    # Generate message
    zone_desc = nearest_zone.get("description", "High-risk zone ahead")
    message = _generate_alert_message(alert_level, nearest_distance, eta_minutes, zone_desc)
    action = _generate_recommended_action(alert_level, nearest_distance)
    
    return RedZoneAlert(
        should_alert=should_alert,
        alert_level=alert_level,
        distance_miles=nearest_distance,
        estimated_minutes=eta_minutes,
        zone_name=zone_desc,
        message=message,
        recommended_action=action,
    )


# =============================================================================
# CONTINUOUS MONITORING
# =============================================================================

def create_200_mile_countdown(
    current_lat: float,
    current_lon: float,
    red_zones: List[Dict[str, Any]],
    speed_mph: float = DEFAULT_SPEED_MPH,
) -> Dict[str, Any]:
    """
    Create a countdown status for the 200-mile Red Zone warning.
    
    Returns countdown info suitable for dashboard display.
    
    Args:
        current_lat: Driver's current latitude
        current_lon: Driver's current longitude
        red_zones: List of Red Zone dicts
        speed_mph: Current speed
    
    Returns:
        dict with countdown info for UI display
    """
    alert = check_red_zone_proximity(
        current_lat, current_lon, red_zones, speed_mph
    )
    
    # Create countdown display
    if not alert.should_alert:
        countdown_status = "CLEAR"
        countdown_color = "green"
        countdown_miles = None
    elif alert.alert_level == "caution":
        countdown_status = "APPROACHING"
        countdown_color = "yellow"
        countdown_miles = alert.distance_miles
    elif alert.alert_level == "warning":
        countdown_status = "WARNING"
        countdown_color = "orange"
        countdown_miles = alert.distance_miles
    else:  # critical
        countdown_status = "DANGER"
        countdown_color = "red"
        countdown_miles = alert.distance_miles
    
    return {
        "status": countdown_status,
        "color": countdown_color,
        "miles_to_zone": countdown_miles,
        "eta_minutes": alert.estimated_minutes if alert.should_alert else None,
        "zone_description": alert.zone_name if alert.should_alert else None,
        "alert": alert.to_dict() if alert.should_alert else None,
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _haversine_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float]
) -> float:
    """
    Calculate distance between two GPS coordinates.
    
    Args:
        point1: (latitude, longitude)
        point2: (latitude, longitude)
        
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


def _create_safe_alert() -> RedZoneAlert:
    """Create a 'safe' alert when no Red Zones are nearby."""
    return RedZoneAlert(
        should_alert=False,
        alert_level="safe",
        distance_miles=float('inf'),
        estimated_minutes=float('inf'),
        zone_name="",
        message="No Red Zones detected on your route.",
        recommended_action="Continue on planned route.",
    )


def _generate_alert_message(
    level: str,
    distance: float,
    eta_minutes: float,
    zone_desc: str
) -> str:
    """Generate human-readable alert message."""
    if level == "critical":
        return (
            f"🔴 CRITICAL: Entering {zone_desc} in {distance:.0f} miles "
            f"(~{eta_minutes:.0f} min). Find secure parking NOW."
        )
    elif level == "warning":
        return (
            f"🟠 WARNING: {zone_desc} in {distance:.0f} miles "
            f"(~{eta_minutes:.0f} min). Plan your stop soon."
        )
    elif level == "caution":
        return (
            f"🟡 HEADS UP: {zone_desc} in {distance:.0f} miles "
            f"(~{eta_minutes:.0f} min). Monitor for safe stops."
        )
    else:
        return "✅ Route is clear of Red Zones."


def _generate_recommended_action(level: str, distance: float) -> str:
    """Generate recommended action based on alert level."""
    if level == "critical":
        return (
            "IMMEDIATE ACTION: Find secured truck stop or distribution center. "
            "Do NOT stop in unsecured areas."
        )
    elif level == "warning":
        return (
            "Plan your next stop at a secured location before entering the zone. "
            "Check find_safe_stops for options."
        )
    elif level == "caution":
        return (
            "Begin monitoring for safe stopping options. Review zone details "
            "and consider timing your drive to pass through during daylight."
        )
    else:
        return "Continue on planned route."


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Red Zone Checker - Test")
    print("=" * 70)
    
    # Mock Red Zones from route scanner
    mock_red_zones = [
        {
            "center": {"latitude": 36.0, "longitude": -95.0},
            "start_mile": 200,
            "end_mile": 250,
            "peak_risk": 8.5,
            "description": "High-risk zone from mile 200 to 250",
        }
    ]
    
    # Test 1: Far from zone (300 miles away)
    print("\n--- Test 1: 300 miles from Red Zone ---")
    alert = check_red_zone_proximity(32.0, -96.0, mock_red_zones, speed_mph=65)
    print(f"Alert Level: {alert.alert_level}")
    print(f"Should Alert: {alert.should_alert}")
    print(f"Distance: {alert.distance_miles:.0f} miles")
    
    # Test 2: Within 200-mile threshold
    print("\n--- Test 2: 150 miles from Red Zone ---")
    alert = check_red_zone_proximity(34.5, -95.5, mock_red_zones, speed_mph=65)
    print(f"Alert Level: {alert.alert_level}")
    print(f"Should Alert: {alert.should_alert}")
    print(f"Message: {alert.message}")
    
    # Test 3: Critical distance
    print("\n--- Test 3: 30 miles from Red Zone ---")
    alert = check_red_zone_proximity(35.7, -95.2, mock_red_zones, speed_mph=65)
    print(f"Alert Level: {alert.alert_level}")
    print(f"Should Alert: {alert.should_alert}")
    print(f"Message: {alert.message}")
    
    # Test 4: Countdown display
    print("\n--- Test 4: 200-Mile Countdown ---")
    countdown = create_200_mile_countdown(34.5, -95.5, mock_red_zones)
    print(f"Status: {countdown['status']}")
    print(f"Color: {countdown['color']}")
    print(f"Miles: {countdown['miles_to_zone']}")
    
    print("\n" + "=" * 70)
    print("✅ Red Zone Checker tests complete!")
    print("=" * 70)
