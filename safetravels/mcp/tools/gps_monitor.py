"""
SafeTravels MCP Tools - GPS Ping Gap Detection
===============================================

Detects GPS signal anomalies that may indicate:
- GPS jammer nearby (common theft tactic)
- Signal interference
- Possible hijacking in progress

GPS JAMMER DETECTION:
    If ignition is ON but GPS signal disappears for > 30 seconds,
    this is suspicious. Thieves use jammers to prevent tracking.

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class GPSAlertType(Enum):
    """Types of GPS-related alerts."""
    SIGNAL_LOSS = "signal_loss"          # Temporary loss (30-60s)
    GPS_JAMMER = "gps_jammer"            # Sustained loss (> 60s)
    LOCATION_JUMP = "location_jump"       # Sudden impossible movement
    STALE_DATA = "stale_data"            # Data not updating


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# CONFIGURATION
# =============================================================================

# GPS ping gap thresholds (seconds)
NORMAL_PING_INTERVAL = 10       # Expected ping every 10 seconds
WARNING_GAP_THRESHOLD = 30      # 30 seconds = warning
CRITICAL_GAP_THRESHOLD = 60     # 60 seconds = jammer suspected
EMERGENCY_GAP_THRESHOLD = 120   # 2 minutes = emergency

# Location jump thresholds
MAX_PLAUSIBLE_SPEED_MPH = 100   # Max 100 mph = ~147 fps
MAX_JUMP_DISTANCE_MILES = 0.5   # 0.5 mile jump in one ping = suspicious


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class GPSPing:
    """Single GPS ping data point."""
    latitude: float
    longitude: float
    timestamp: datetime
    speed_mph: float = 0
    heading: float = 0          # Degrees (0-360)
    accuracy_meters: float = 10


@dataclass
class GPSAlert:
    """Detected GPS anomaly alert."""
    alert_type: GPSAlertType
    severity: AlertSeverity
    message: str
    gap_seconds: Optional[int] = None
    last_known_location: Optional[Dict] = None
    timestamp: datetime = None
    recommended_action: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "gap_seconds": self.gap_seconds,
            "last_known_location": self.last_known_location,
            "timestamp": self.timestamp.isoformat(),
            "recommended_action": self.recommended_action,
        }


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def detect_gps_gap(
    last_ping_time: datetime,
    current_time: datetime = None,
    ignition_on: bool = True,
    last_known_lat: float = None,
    last_known_lon: float = None,
) -> Optional[GPSAlert]:
    """
    Detect GPS signal gaps that may indicate jammer.
    
    GPS JAMMER BEHAVIOR:
        - Ignition is ON (truck running)
        - GPS signal disappears
        - Common in "strategic theft" operations
    
    Args:
        last_ping_time: Timestamp of last GPS ping received
        current_time: Current time (defaults to now)
        ignition_on: Whether the vehicle ignition is on
        last_known_lat: Last known latitude
        last_known_lon: Last known longitude
        
    Returns:
        GPSAlert if anomaly detected, None otherwise
    """
    if current_time is None:
        current_time = datetime.now()
    
    gap_seconds = int((current_time - last_ping_time).total_seconds())
    
    # If ignition is OFF, gaps are expected (parked)
    if not ignition_on:
        return None
    
    # Build last known location dict
    last_location = None
    if last_known_lat and last_known_lon:
        last_location = {
            "latitude": last_known_lat,
            "longitude": last_known_lon,
            "timestamp": last_ping_time.isoformat(),
        }
    
    # Check gap thresholds
    if gap_seconds >= EMERGENCY_GAP_THRESHOLD:
        # 2+ minutes = EMERGENCY
        logger.critical(f"GPS EMERGENCY: No signal for {gap_seconds}s")
        return GPSAlert(
            alert_type=GPSAlertType.GPS_JAMMER,
            severity=AlertSeverity.CRITICAL,
            message=(
                f"🚨 GPS EMERGENCY: No signal for {gap_seconds // 60} min "
                f"{gap_seconds % 60}s. GPS JAMMER SUSPECTED. "
                "Contact driver immediately!"
            ),
            gap_seconds=gap_seconds,
            last_known_location=last_location,
            recommended_action="Call driver immediately. Alert law enforcement if no response.",
        )
    
    elif gap_seconds >= CRITICAL_GAP_THRESHOLD:
        # 60+ seconds = Jammer suspected
        logger.warning(f"GPS jammer suspected: {gap_seconds}s gap")
        return GPSAlert(
            alert_type=GPSAlertType.GPS_JAMMER,
            severity=AlertSeverity.HIGH,
            message=(
                f"⚠️ GPS JAMMER SUSPECTED: No signal for {gap_seconds}s "
                "while ignition is ON. Possible theft in progress."
            ),
            gap_seconds=gap_seconds,
            last_known_location=last_location,
            recommended_action="Attempt to contact driver. Prepare to alert authorities.",
        )
    
    elif gap_seconds >= WARNING_GAP_THRESHOLD:
        # 30+ seconds = Warning
        logger.info(f"GPS signal loss warning: {gap_seconds}s gap")
        return GPSAlert(
            alert_type=GPSAlertType.SIGNAL_LOSS,
            severity=AlertSeverity.WARNING,
            message=(
                f"🟡 GPS signal lost for {gap_seconds}s. "
                "May be tunnel, urban canyon, or interference."
            ),
            gap_seconds=gap_seconds,
            last_known_location=last_location,
            recommended_action="Monitor for reconnection. Escalate if gap continues.",
        )
    
    return None


def detect_location_jump(
    previous_ping: GPSPing,
    current_ping: GPSPing,
) -> Optional[GPSAlert]:
    """
    Detect impossible location jumps (spoofing indicator).
    
    LOCATION SPOOFING:
        If GPS shows truck "jumped" 50 miles in 1 second,
        the signal may be spoofed by thieves.
    
    Args:
        previous_ping: Previous GPS ping
        current_ping: Current GPS ping
        
    Returns:
        GPSAlert if impossible jump detected, None otherwise
    """
    from math import radians, sin, cos, sqrt, atan2
    
    # Calculate distance using Haversine formula
    R = 3959  # Earth radius in miles
    
    lat1 = radians(previous_ping.latitude)
    lon1 = radians(previous_ping.longitude)
    lat2 = radians(current_ping.latitude)
    lon2 = radians(current_ping.longitude)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance_miles = R * c
    
    # Calculate time difference
    time_diff = (current_ping.timestamp - previous_ping.timestamp).total_seconds()
    
    if time_diff <= 0:
        return None
    
    # Calculate implied speed
    implied_speed_mph = (distance_miles / time_diff) * 3600
    
    # Check if jump is impossible
    if implied_speed_mph > MAX_PLAUSIBLE_SPEED_MPH * 2:  # 200+ mph = impossible
        logger.warning(f"Impossible jump detected: {distance_miles:.2f} mi in {time_diff}s")
        return GPSAlert(
            alert_type=GPSAlertType.LOCATION_JUMP,
            severity=AlertSeverity.HIGH,
            message=(
                f"⚠️ IMPOSSIBLE GPS JUMP: {distance_miles:.1f} miles in "
                f"{time_diff:.0f}s (= {implied_speed_mph:.0f} mph). "
                "Possible GPS spoofing."
            ),
            last_known_location={
                "latitude": previous_ping.latitude,
                "longitude": previous_ping.longitude,
            },
            recommended_action="Verify with driver. This may indicate spoofed GPS.",
        )
    
    return None


def check_gps_status(
    last_ping_time: datetime,
    ignition_on: bool = True,
    last_known_lat: float = None,
    last_known_lon: float = None,
    previous_lat: float = None,
    previous_lon: float = None,
    previous_time: datetime = None,
) -> Dict[str, Any]:
    """
    Comprehensive GPS health check.
    
    Runs all GPS detection algorithms and returns status.
    
    Args:
        last_ping_time: Timestamp of last GPS ping
        ignition_on: Whether ignition is on
        last_known_lat/lon: Last known coordinates
        previous_lat/lon/time: Previous ping data for jump detection
        
    Returns:
        Dict with status and any alerts
    """
    current_time = datetime.now()
    alerts = []
    
    # Check for GPS gap
    gap_alert = detect_gps_gap(
        last_ping_time=last_ping_time,
        current_time=current_time,
        ignition_on=ignition_on,
        last_known_lat=last_known_lat,
        last_known_lon=last_known_lon,
    )
    if gap_alert:
        alerts.append(gap_alert.to_dict())
    
    # Check for location jump
    if all([previous_lat, previous_lon, previous_time, last_known_lat, last_known_lon]):
        prev_ping = GPSPing(previous_lat, previous_lon, previous_time)
        curr_ping = GPSPing(last_known_lat, last_known_lon, last_ping_time)
        jump_alert = detect_location_jump(prev_ping, curr_ping)
        if jump_alert:
            alerts.append(jump_alert.to_dict())
    
    # Calculate gap for info
    gap_seconds = int((current_time - last_ping_time).total_seconds())
    
    if alerts:
        return {
            "status": "alert",
            "alerts": alerts,
            "highest_severity": max(a["severity"] for a in alerts),
            "gap_seconds": gap_seconds,
        }
    
    return {
        "status": "normal",
        "message": "GPS signal healthy",
        "gap_seconds": gap_seconds,
        "ignition_on": ignition_on,
    }


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GPS Ping Gap Detection - Test")
    print("=" * 60)
    
    # Test 1: Normal ping (10 seconds ago)
    print("\n--- Test 1: Recent ping (10s ago) ---")
    result = check_gps_status(
        last_ping_time=datetime.now() - timedelta(seconds=10),
        ignition_on=True,
    )
    print(f"Status: {result['status']}, Gap: {result['gap_seconds']}s")
    
    # Test 2: Warning gap (45 seconds)
    print("\n--- Test 2: Warning gap (45s) ---")
    result = check_gps_status(
        last_ping_time=datetime.now() - timedelta(seconds=45),
        ignition_on=True,
        last_known_lat=32.7767,
        last_known_lon=-96.7970,
    )
    print(f"Status: {result['status']}")
    if result.get("alerts"):
        print(f"Alert: {result['alerts'][0]['message']}")
    
    # Test 3: Critical gap (90 seconds)
    print("\n--- Test 3: Critical gap - Jammer suspected (90s) ---")
    result = check_gps_status(
        last_ping_time=datetime.now() - timedelta(seconds=90),
        ignition_on=True,
        last_known_lat=32.7767,
        last_known_lon=-96.7970,
    )
    print(f"Status: {result['status']}")
    if result.get("alerts"):
        print(f"Alert: {result['alerts'][0]['message']}")
        print(f"Action: {result['alerts'][0]['recommended_action']}")
    
    # Test 4: Emergency gap (3 minutes)
    print("\n--- Test 4: Emergency gap (180s) ---")
    result = check_gps_status(
        last_ping_time=datetime.now() - timedelta(seconds=180),
        ignition_on=True,
    )
    print(f"Status: {result['status']}")
    if result.get("alerts"):
        print(f"Alert: {result['alerts'][0]['message']}")
    
    # Test 5: Ignition OFF (expected gap)
    print("\n--- Test 5: Ignition OFF (no alert) ---")
    result = check_gps_status(
        last_ping_time=datetime.now() - timedelta(seconds=300),
        ignition_on=False,
    )
    print(f"Status: {result['status']}")
    
    print("\n" + "=" * 60)
    print("✅ GPS Monitor test complete!")
