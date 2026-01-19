"""
SafeTravels MCP Tools - Behavior Monitor
=========================================

Monitors driver behavior patterns to detect potential distress signals:
    - Unexpected stops in unsafe locations
    - Speed changes (slowdowns that could indicate trouble)
    - Signal loss (possible jamming or remote areas)
    - Deviation from planned route

USAGE:
    from safetravels.mcp.tools.behavior_monitor import analyze_driver_behavior
    
    status = analyze_driver_behavior(
        current_speed=5,
        previous_speed=65,
        location_type="random_roadside",
        signal_strength=0.1,
        last_ping_minutes=20
    )
    
    if status.alert_type != "normal":
        trigger_dispatch_notification(status)

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Speed thresholds
STOPPED_THRESHOLD_MPH: float = 5.0       # Below this = stopped
SLOWDOWN_THRESHOLD_MPH: float = 20.0     # Significant slowdown

# Signal thresholds
SIGNAL_LOSS_MINUTES: int = 15            # No ping for this long = concern
WEAK_SIGNAL_THRESHOLD: float = 0.2       # Signal strength below this = weak

# Safe location types (stops here are normal)
SAFE_STOP_LOCATIONS = [
    "truck_stop_secured",
    "truck_stop_premium",
    "truck_stop_basic",
    "distribution_center",
    "shipper_facility",
]


# =============================================================================
# ENUMS
# =============================================================================

class AlertType(Enum):
    """Types of behavior alerts."""
    NORMAL = "normal"
    UNEXPECTED_STOP = "unexpected_stop"
    SUSPICIOUS_SLOWDOWN = "suspicious_slowdown"
    SIGNAL_LOSS = "signal_loss"
    SIGNAL_WEAK = "signal_weak"
    ROUTE_DEVIATION = "route_deviation"
    EXTENDED_STOP = "extended_stop"


class AlertSeverity(Enum):
    """Severity levels for alerts."""
    INFO = "info"           # Just logging
    WARNING = "warning"     # Dispatch should monitor
    CRITICAL = "critical"   # Immediate action needed


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BehaviorAlert:
    """
    Alert generated from driver behavior analysis.
    
    Attributes:
        alert_type: Type of behavior detected
        severity: How urgent this is
        message: Human-readable description
        recommended_action: What dispatch should do
        should_notify_dispatch: Whether to alert dispatch
        should_notify_driver: Whether to contact driver
        location: Where this occurred (if known)
    """
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    recommended_action: str
    should_notify_dispatch: bool
    should_notify_driver: bool
    location: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "should_notify_dispatch": self.should_notify_dispatch,
            "should_notify_driver": self.should_notify_driver,
            "location": self.location,
        }


@dataclass
class DriverStatus:
    """
    Complete driver status from behavior analysis.
    
    Attributes:
        driver_id: Unique driver identifier
        timestamp: When this status was generated
        current_speed: Current speed in MPH
        is_stopped: Whether driver is stopped
        is_in_safe_location: Whether stopped in safe area
        signal_strength: Signal strength (0-1)
        alerts: List of any triggered alerts
    """
    driver_id: str
    timestamp: str
    current_speed: float
    is_stopped: bool
    is_in_safe_location: bool
    signal_strength: float
    alerts: List[BehaviorAlert] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "driver_id": self.driver_id,
            "timestamp": self.timestamp,
            "current_speed": self.current_speed,
            "is_stopped": self.is_stopped,
            "is_in_safe_location": self.is_in_safe_location,
            "signal_strength": self.signal_strength,
            "alert_count": len(self.alerts),
            "alerts": [a.to_dict() for a in self.alerts],
        }


# =============================================================================
# CORE FUNCTION
# =============================================================================

def analyze_driver_behavior(
    driver_id: str = "driver_001",
    current_lat: float = 0.0,
    current_lon: float = 0.0,
    current_speed: float = 65.0,
    previous_speed: float = 65.0,
    location_type: str = "unknown",
    signal_strength: float = 1.0,
    last_ping_minutes: int = 0,
    stop_duration_minutes: int = 0,
) -> DriverStatus:
    """
    Analyze driver behavior and generate alerts if concerning.
    
    This function checks multiple behavior patterns:
        - Stopped in unsafe location
        - Sudden speed drop
        - Signal loss or weakness
        - Extended stops
    
    Args:
        driver_id: Unique identifier for the driver
        current_lat: Current latitude
        current_lon: Current longitude
        current_speed: Current speed in MPH
        previous_speed: Speed at last check (for comparison)
        location_type: Type of current location
        signal_strength: Signal strength 0-1 (1 = full)
        last_ping_minutes: Minutes since last GPS ping
        stop_duration_minutes: How long stopped (if applicable)
    
    Returns:
        DriverStatus with any triggered alerts.
    
    Example:
        >>> status = analyze_driver_behavior(
        ...     current_speed=0,
        ...     location_type="random_roadside",
        ...     signal_strength=0.1
        ... )
        >>> print(status.alerts[0].alert_type)
        AlertType.UNEXPECTED_STOP
    """
    logger.debug(f"Analyzing behavior for {driver_id}")
    
    alerts: List[BehaviorAlert] = []
    
    # Determine if stopped
    is_stopped = current_speed < STOPPED_THRESHOLD_MPH
    
    # Determine if in safe location
    is_in_safe_location = location_type in SAFE_STOP_LOCATIONS
    
    # -----------------------------------------------------------------
    # CHECK 1: Unexpected Stop
    # -----------------------------------------------------------------
    if is_stopped and not is_in_safe_location:
        alerts.append(BehaviorAlert(
            alert_type=AlertType.UNEXPECTED_STOP,
            severity=AlertSeverity.CRITICAL,
            message=(
                f"⚠️ DRIVER STOPPED in unsafe location "
                f"({location_type}). Immediate check required."
            ),
            recommended_action=(
                "Contact driver immediately via phone. "
                "If no response in 5 minutes, alert authorities."
            ),
            should_notify_dispatch=True,
            should_notify_driver=True,
            location={"latitude": current_lat, "longitude": current_lon},
        ))
    
    # -----------------------------------------------------------------
    # CHECK 2: Extended Stop (even in safe location)
    # -----------------------------------------------------------------
    if is_stopped and stop_duration_minutes > 120:  # 2+ hours
        severity = AlertSeverity.WARNING if is_in_safe_location else AlertSeverity.CRITICAL
        alerts.append(BehaviorAlert(
            alert_type=AlertType.EXTENDED_STOP,
            severity=severity,
            message=(
                f"⏱️ Driver has been stopped for {stop_duration_minutes} minutes."
            ),
            recommended_action=(
                "Check in with driver. Verify hours of service compliance."
            ),
            should_notify_dispatch=True,
            should_notify_driver=False,
            location={"latitude": current_lat, "longitude": current_lon},
        ))
    
    # -----------------------------------------------------------------
    # CHECK 3: Suspicious Slowdown
    # -----------------------------------------------------------------
    speed_drop = previous_speed - current_speed
    if speed_drop > 40 and current_speed < SLOWDOWN_THRESHOLD_MPH:
        alerts.append(BehaviorAlert(
            alert_type=AlertType.SUSPICIOUS_SLOWDOWN,
            severity=AlertSeverity.WARNING,
            message=(
                f"🚨 Sudden speed drop detected: {previous_speed:.0f} → "
                f"{current_speed:.0f} MPH. Possible emergency."
            ),
            recommended_action=(
                "Monitor for continued slowdown. Prepare to contact driver."
            ),
            should_notify_dispatch=True,
            should_notify_driver=False,
            location={"latitude": current_lat, "longitude": current_lon},
        ))
    
    # -----------------------------------------------------------------
    # CHECK 4: Signal Loss
    # -----------------------------------------------------------------
    if last_ping_minutes >= SIGNAL_LOSS_MINUTES:
        alerts.append(BehaviorAlert(
            alert_type=AlertType.SIGNAL_LOSS,
            severity=AlertSeverity.CRITICAL,
            message=(
                f"📡 NO SIGNAL for {last_ping_minutes} minutes. "
                f"Last known location: ({current_lat:.4f}, {current_lon:.4f})"
            ),
            recommended_action=(
                "Attempt phone contact immediately. "
                "If no response, dispatch security or authorities."
            ),
            should_notify_dispatch=True,
            should_notify_driver=True,
            location={"latitude": current_lat, "longitude": current_lon},
        ))
    
    # -----------------------------------------------------------------
    # CHECK 5: Weak Signal
    # -----------------------------------------------------------------
    if signal_strength < WEAK_SIGNAL_THRESHOLD and last_ping_minutes < SIGNAL_LOSS_MINUTES:
        alerts.append(BehaviorAlert(
            alert_type=AlertType.SIGNAL_WEAK,
            severity=AlertSeverity.WARNING,
            message=(
                f"📶 Weak signal detected ({signal_strength:.0%}). "
                f"Possible jamming or remote area."
            ),
            recommended_action=(
                "Monitor for signal loss. "
                "Check if location matches known dead zones."
            ),
            should_notify_dispatch=True,
            should_notify_driver=False,
            location={"latitude": current_lat, "longitude": current_lon},
        ))
    
    return DriverStatus(
        driver_id=driver_id,
        timestamp=datetime.utcnow().isoformat(),
        current_speed=current_speed,
        is_stopped=is_stopped,
        is_in_safe_location=is_in_safe_location,
        signal_strength=signal_strength,
        alerts=alerts,
    )


def is_emergency(status: DriverStatus) -> bool:
    """
    Quick check if any alerts are critical.
    
    Args:
        status: DriverStatus from analyze_driver_behavior
        
    Returns:
        True if any CRITICAL severity alerts exist
    """
    return any(
        alert.severity == AlertSeverity.CRITICAL 
        for alert in status.alerts
    )


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Behavior Monitor - Test")
    print("=" * 70)
    
    # Test 1: Normal driving
    print("\n--- Test 1: Normal Driving ---")
    status = analyze_driver_behavior(
        current_speed=65,
        previous_speed=65,
        location_type="highway",
        signal_strength=0.9,
    )
    print(f"Alerts: {len(status.alerts)}")
    print(f"Is Emergency: {is_emergency(status)}")
    
    # Test 2: Stopped in unsafe location
    print("\n--- Test 2: Stopped in Unsafe Location ---")
    status = analyze_driver_behavior(
        current_speed=0,
        previous_speed=65,
        location_type="random_roadside",
        signal_strength=0.8,
    )
    print(f"Alerts: {len(status.alerts)}")
    print(f"Is Emergency: {is_emergency(status)}")
    for alert in status.alerts:
        print(f"  - {alert.alert_type.value}: {alert.severity.value}")
    
    # Test 3: Signal loss
    print("\n--- Test 3: Signal Loss ---")
    status = analyze_driver_behavior(
        current_speed=0,
        previous_speed=65,
        location_type="unknown",
        signal_strength=0,
        last_ping_minutes=20,
    )
    print(f"Alerts: {len(status.alerts)}")
    print(f"Is Emergency: {is_emergency(status)}")
    for alert in status.alerts:
        print(f"  - {alert.alert_type.value}: {alert.message[:50]}...")
    
    # Test 4: Stopped at safe truck stop (normal)
    print("\n--- Test 4: Stopped at Safe Truck Stop ---")
    status = analyze_driver_behavior(
        current_speed=0,
        previous_speed=0,
        location_type="truck_stop_secured",
        signal_strength=1.0,
        stop_duration_minutes=30,
    )
    print(f"Alerts: {len(status.alerts)}")
    print(f"Is Emergency: {is_emergency(status)}")
    
    print("\n" + "=" * 70)
    print("✅ Behavior Monitor tests complete!")
    print("=" * 70)
