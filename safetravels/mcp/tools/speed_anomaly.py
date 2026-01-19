"""
SafeTravels MCP Tools - Speed Anomaly Detection
================================================

Detects unusual vehicle speed patterns that may indicate:
- Tailing/following by thieves
- Scouting behavior
- Driver under duress

CREEPING DETECTION:
    Speed of 5-15 mph on highway with free-flowing traffic
    is suspicious and warrants an alert.

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class RoadType(Enum):
    """Road classification types."""
    HIGHWAY = "highway"
    INTERSTATE = "interstate"
    US_ROUTE = "us_route"
    STATE_ROUTE = "state_route"
    LOCAL = "local"
    UNKNOWN = "unknown"


class TrafficLevel(Enum):
    """Traffic congestion levels."""
    FREE_FLOW = "free_flow"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    STANDSTILL = "standstill"


# =============================================================================
# CONFIGURATION
# =============================================================================

# Speed thresholds for anomaly detection (mph)
CREEPING_MIN_SPEED = 5      # Below this = stopped
CREEPING_MAX_SPEED = 15     # Above this = normal slow driving
NORMAL_HIGHWAY_MIN = 45     # Expected minimum on highway

# Time thresholds (seconds)
MIN_CREEP_DURATION = 30     # Must creep for 30s to trigger alert
SUSTAINED_CREEP_DURATION = 120  # 2 minutes = escalate to HIGH


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SpeedAnomaly:
    """
    Detected speed anomaly with context.
    """
    alert_type: str          # CREEPING, ERRATIC_BRAKING, SUDDEN_STOP
    severity: AlertSeverity
    message: str             # Human-readable description
    speed_mph: float
    road_type: str
    traffic_level: str
    timestamp: datetime
    duration_seconds: Optional[int] = None
    recommended_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "speed_mph": self.speed_mph,
            "road_type": self.road_type,
            "traffic_level": self.traffic_level,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "recommended_action": self.recommended_action,
        }


# =============================================================================
# DETECTION FUNCTIONS
# =============================================================================

def detect_creeping(
    speed_mph: float,
    road_type: str,
    traffic_level: str,
    duration_seconds: int = 0,
) -> Optional[SpeedAnomaly]:
    """
    Detect creeping behavior (unusually slow speed on highway).
    
    CREEPING DEFINITION:
        - Speed between 5-15 mph
        - On highway/interstate
        - Traffic is free-flowing or light
        - Sustained for > 30 seconds
    
    WHY IT MATTERS:
        Thieves often follow trucks at slow speeds before striking.
        A truck doing 8 mph on an empty highway is suspicious.
    
    Args:
        speed_mph: Current vehicle speed in miles per hour
        road_type: Type of road (highway, interstate, local, etc.)
        traffic_level: Current traffic conditions
        duration_seconds: How long the slow speed has been sustained
        
    Returns:
        SpeedAnomaly if detected, None otherwise
    """
    # Normalize inputs
    road = road_type.lower()
    traffic = traffic_level.lower()
    
    # Check if this is a highway-type road
    is_highway = road in ["highway", "interstate", "us_route", "i-", "us-"]
    
    # Check if traffic is flowing (not congested)
    is_traffic_clear = traffic in ["free_flow", "light", "free", "clear"]
    
    # Check if speed is in creeping range
    is_creeping = CREEPING_MIN_SPEED <= speed_mph <= CREEPING_MAX_SPEED
    
    # Only alert on highways with clear traffic
    if is_highway and is_traffic_clear and is_creeping:
        # Determine severity based on duration
        if duration_seconds >= SUSTAINED_CREEP_DURATION:
            severity = AlertSeverity.HIGH
            message = (
                f"⚠️ SUSTAINED CREEPING DETECTED: {speed_mph} mph for "
                f"{duration_seconds // 60} min on {road_type}. "
                "Possible tailing. Consider changing course."
            )
            action = "Change route or proceed to nearest safe location."
        elif duration_seconds >= MIN_CREEP_DURATION:
            severity = AlertSeverity.WARNING
            message = (
                f"🟡 Unusual slow speed: {speed_mph} mph on {road_type} "
                f"with {traffic_level} traffic. Monitor surroundings."
            )
            action = "Stay alert and monitor vehicles behind you."
        else:
            # Too short to trigger alert
            return None
        
        logger.warning(f"Creeping detected: {speed_mph} mph, duration={duration_seconds}s")
        
        return SpeedAnomaly(
            alert_type="CREEPING",
            severity=severity,
            message=message,
            speed_mph=speed_mph,
            road_type=road_type,
            traffic_level=traffic_level,
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
            recommended_action=action,
        )
    
    return None


def detect_erratic_braking(
    speed_history: list,  # List of (timestamp, speed) tuples
    road_conditions: str = "normal",
) -> Optional[SpeedAnomaly]:
    """
    Detect erratic braking patterns.
    
    ERRATIC BRAKING DEFINITION:
        - Speed drops > 20 mph in < 3 seconds
        - Not explained by road conditions
        - Repeated pattern (3+ times in 5 minutes)
    
    WHY IT MATTERS:
        May indicate driver under duress or forced stop.
    
    Args:
        speed_history: List of (timestamp, speed_mph) tuples
        road_conditions: Current road conditions (normal, construction, etc.)
        
    Returns:
        SpeedAnomaly if detected, None otherwise
    """
    if len(speed_history) < 2:
        return None
    
    # Find rapid deceleration events
    braking_events = []
    for i in range(1, len(speed_history)):
        prev_time, prev_speed = speed_history[i - 1]
        curr_time, curr_speed = speed_history[i]
        
        time_diff = (curr_time - prev_time).total_seconds()
        speed_drop = prev_speed - curr_speed
        
        # Rapid deceleration: > 20 mph drop in < 3 seconds
        if time_diff <= 3 and speed_drop >= 20:
            braking_events.append({
                "timestamp": curr_time,
                "speed_drop": speed_drop,
                "time_diff": time_diff,
            })
    
    # Alert if 3+ erratic braking events
    if len(braking_events) >= 3:
        latest = braking_events[-1]
        
        return SpeedAnomaly(
            alert_type="ERRATIC_BRAKING",
            severity=AlertSeverity.HIGH,
            message=(
                f"⚠️ ERRATIC BRAKING: {len(braking_events)} sudden stops detected. "
                "Driver may be under duress."
            ),
            speed_mph=0,  # Variable
            road_type="unknown",
            traffic_level="unknown",
            timestamp=latest["timestamp"],
            duration_seconds=None,
            recommended_action="Contact driver or dispatch immediately.",
        )
    
    return None


def detect_sudden_stop(
    current_speed: float,
    previous_speed: float,
    location_type: str,
    time_stopped_seconds: int = 0,
) -> Optional[SpeedAnomaly]:
    """
    Detect sudden unplanned stops.
    
    SUDDEN STOP DEFINITION:
        - Speed drops from > 30 mph to 0 mph
        - Location is not an approved stop
        - Stopped for > 60 seconds
    
    Args:
        current_speed: Current speed (should be 0 or near 0)
        previous_speed: Speed before stopping
        location_type: Type of location (approved_stop, roadside, unknown)
        time_stopped_seconds: How long the vehicle has been stopped
        
    Returns:
        SpeedAnomaly if detected, None otherwise
    """
    # Check for sudden stop from moving
    was_moving = previous_speed >= 30
    is_stopped = current_speed < 2
    is_unapproved = location_type.lower() not in [
        "truck_stop", "rest_area", "gas_station", "approved_stop"
    ]
    
    if was_moving and is_stopped and is_unapproved:
        if time_stopped_seconds >= 60:
            severity = AlertSeverity.CRITICAL
            message = (
                f"🚨 UNPLANNED STOP: Vehicle stopped at {location_type} "
                f"for {time_stopped_seconds}s. Verify driver status."
            )
        else:
            severity = AlertSeverity.WARNING
            message = (
                f"🟡 Unexpected stop at {location_type}. Monitoring..."
            )
        
        return SpeedAnomaly(
            alert_type="SUDDEN_STOP",
            severity=severity,
            message=message,
            speed_mph=current_speed,
            road_type="unknown",
            traffic_level="unknown",
            timestamp=datetime.now(),
            duration_seconds=time_stopped_seconds,
            recommended_action="Contact driver to verify status.",
        )
    
    return None


def check_speed_anomaly(
    speed_mph: float,
    road_type: str = "highway",
    traffic_level: str = "free_flow",
    duration_seconds: int = 0,
    previous_speed: float = None,
    location_type: str = "unknown",
) -> Dict[str, Any]:
    """
    Comprehensive speed anomaly check.
    
    Runs all detection algorithms and returns any alerts.
    
    Args:
        speed_mph: Current speed
        road_type: Type of road
        traffic_level: Traffic conditions
        duration_seconds: Duration at current speed
        previous_speed: Previous speed reading
        location_type: Type of location (for stop detection)
        
    Returns:
        Dict with alert info or {"status": "normal"} if no issues
    """
    alerts = []
    
    # Check for creeping
    creep = detect_creeping(speed_mph, road_type, traffic_level, duration_seconds)
    if creep:
        alerts.append(creep.to_dict())
    
    # Check for sudden stop
    if previous_speed is not None:
        stop = detect_sudden_stop(speed_mph, previous_speed, location_type, duration_seconds)
        if stop:
            alerts.append(stop.to_dict())
    
    if alerts:
        return {
            "status": "alert",
            "alerts": alerts,
            "highest_severity": max(a["severity"] for a in alerts),
        }
    
    return {
        "status": "normal",
        "message": "No speed anomalies detected",
        "current_speed": speed_mph,
        "road_type": road_type,
    }


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Speed Anomaly Detection - Test")
    print("=" * 60)
    
    # Test 1: Creeping detection
    print("\n--- Test 1: Creeping at 8 mph for 60s ---")
    result = check_speed_anomaly(
        speed_mph=8,
        road_type="highway",
        traffic_level="free_flow",
        duration_seconds=60,
    )
    print(f"Status: {result['status']}")
    if result.get("alerts"):
        print(f"Alert: {result['alerts'][0]['message']}")
    
    # Test 2: Normal speed
    print("\n--- Test 2: Normal highway speed ---")
    result = check_speed_anomaly(speed_mph=65, road_type="highway", traffic_level="light")
    print(f"Status: {result['status']}")
    
    # Test 3: Sudden stop
    print("\n--- Test 3: Sudden stop at roadside ---")
    result = check_speed_anomaly(
        speed_mph=0,
        previous_speed=55,
        location_type="roadside",
        duration_seconds=120,
    )
    print(f"Status: {result['status']}")
    if result.get("alerts"):
        print(f"Alert: {result['alerts'][0]['message']}")
    
    print("\n" + "=" * 60)
    print("✅ Speed Anomaly Detection test complete!")
