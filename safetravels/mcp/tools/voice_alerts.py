"""
SafeTravels MCP Tools - Voice Alert System
===========================================

Audio warnings for truck drivers.

ALERT TYPES:
    - Red Zone Entry: "Warning: High-theft zone. Do not stop."
    - Dwell Warning: "Alert: Move immediately. You're in danger."
    - Safe Zone: "You've exited the high-risk zone."
    - GPS Jammer: "Emergency: GPS signal lost. Contact dispatch."

IMPLEMENTATION:
    - Returns audio URLs + text for TTS fallback
    - Pre-recorded MP3s for consistent experience
    - Text available for browser speechSynthesis API

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AlertType(Enum):
    """Types of voice alerts."""
    RED_ZONE_ENTRY = "red_zone_entry"
    RED_ZONE_EXIT = "red_zone_exit"
    DWELL_WARNING = "dwell_warning"
    DWELL_CRITICAL = "dwell_critical"
    SAFE_PARKING_NEARBY = "safe_parking_nearby"
    SAFE_ZONE_REACHED = "safe_zone_reached"
    GPS_JAMMER = "gps_jammer"
    CREEPING_DETECTED = "creeping_detected"
    HOS_WARNING = "hos_warning"
    HOS_CRITICAL = "hos_critical"
    WEATHER_ALERT = "weather_alert"
    EMERGENCY = "emergency"


class AlertPriority(Enum):
    """Priority levels for alert playback."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# =============================================================================
# ALERT MESSAGES
# =============================================================================

# All voice alert messages with text and audio file references
ALERT_MESSAGES: Dict[AlertType, Dict[str, Any]] = {
    AlertType.RED_ZONE_ENTRY: {
        "text": "Warning: You are entering a high-theft area. Do not stop until you reach a safe zone.",
        "short_text": "⚠️ High-theft zone ahead",
        "audio_file": "red_zone_entry.mp3",
        "priority": AlertPriority.HIGH,
        "repeat_interval_seconds": 300,  # Don't repeat for 5 min
    },
    AlertType.RED_ZONE_EXIT: {
        "text": "You have exited the high-risk zone. Safe parking is now available.",
        "short_text": "✅ Exited high-risk zone",
        "audio_file": "red_zone_exit.mp3",
        "priority": AlertPriority.LOW,
        "repeat_interval_seconds": 0,
    },
    AlertType.DWELL_WARNING: {
        "text": "Alert: You have been stopped for 10 minutes in a high-risk area. Consider moving to a safer location.",
        "short_text": "🟡 10 min in risk zone",
        "audio_file": "dwell_warning.mp3",
        "priority": AlertPriority.MEDIUM,
        "repeat_interval_seconds": 300,
    },
    AlertType.DWELL_CRITICAL: {
        "text": "Critical Alert: You have been stopped for over 15 minutes in a dangerous area. Move immediately!",
        "short_text": "🔴 MOVE NOW!",
        "audio_file": "dwell_critical.mp3",
        "priority": AlertPriority.CRITICAL,
        "repeat_interval_seconds": 60,
    },
    AlertType.SAFE_PARKING_NEARBY: {
        "text": "Safe parking available. {stop_name} is {distance} miles ahead with {spaces} spots open.",
        "short_text": "🅿️ Safe parking ahead",
        "audio_file": "safe_parking.mp3",
        "priority": AlertPriority.LOW,
        "repeat_interval_seconds": 600,
    },
    AlertType.SAFE_ZONE_REACHED: {
        "text": "You have completed the 200-mile safety buffer. It is now safe to stop if needed.",
        "short_text": "✅ 200-mile buffer complete",
        "audio_file": "safe_zone.mp3",
        "priority": AlertPriority.LOW,
        "repeat_interval_seconds": 0,
    },
    AlertType.GPS_JAMMER: {
        "text": "Emergency: GPS signal has been lost while ignition is on. This may indicate a GPS jammer. Contact dispatch immediately!",
        "short_text": "🚨 GPS JAMMER DETECTED",
        "audio_file": "gps_jammer.mp3",
        "priority": AlertPriority.CRITICAL,
        "repeat_interval_seconds": 30,
    },
    AlertType.CREEPING_DETECTED: {
        "text": "Caution: Unusual slow speed detected on highway. You may be being followed. Stay alert and consider changing your route.",
        "short_text": "⚠️ Possible tailing",
        "audio_file": "creeping.mp3",
        "priority": AlertPriority.HIGH,
        "repeat_interval_seconds": 180,
    },
    AlertType.HOS_WARNING: {
        "text": "Hours of Service reminder: You have {hours} hours remaining in your shift. Start planning your rest stop.",
        "short_text": "⏰ {hours}h remaining",
        "audio_file": "hos_warning.mp3",
        "priority": AlertPriority.MEDIUM,
        "repeat_interval_seconds": 1800,  # 30 min
    },
    AlertType.HOS_CRITICAL: {
        "text": "Hours of Service alert: You have less than 1 hour remaining. Find a safe rest stop immediately.",
        "short_text": "🔴 <1 hour HOS left!",
        "audio_file": "hos_critical.mp3",
        "priority": AlertPriority.HIGH,
        "repeat_interval_seconds": 600,
    },
    AlertType.WEATHER_ALERT: {
        "text": "Weather alert: {condition} conditions ahead. Proceed with caution and consider delaying your trip.",
        "short_text": "🌧️ Weather alert",
        "audio_file": "weather.mp3",
        "priority": AlertPriority.MEDIUM,
        "repeat_interval_seconds": 1800,
    },
    AlertType.EMERGENCY: {
        "text": "Emergency alert! Contact dispatch immediately at 1-800-SAFE-HAUL or call 911.",
        "short_text": "🆘 EMERGENCY",
        "audio_file": "emergency.mp3",
        "priority": AlertPriority.CRITICAL,
        "repeat_interval_seconds": 30,
    },
}


# =============================================================================
# VOICE ALERT DATA CLASS
# =============================================================================

@dataclass
class VoiceAlert:
    """Voice alert ready for playback."""
    alert_type: AlertType
    text: str
    short_text: str
    audio_url: Optional[str]
    priority: AlertPriority
    should_interrupt: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "text": self.text,
            "short_text": self.short_text,
            "audio_url": self.audio_url,
            "priority": self.priority.value,
            "priority_name": self.priority.name,
            "should_interrupt": self.should_interrupt,
        }


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def get_voice_alert(
    alert_type: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Get voice alert data for playback.
    
    Args:
        alert_type: Type of alert (e.g., "red_zone_entry")
        **kwargs: Variables for message formatting (e.g., stop_name, distance)
        
    Returns:
        Dict with alert text, audio URL, and playback settings
    """
    # Parse alert type
    try:
        alert_enum = AlertType(alert_type.lower())
    except ValueError:
        logger.error(f"Unknown alert type: {alert_type}")
        return {
            "error": f"Unknown alert type: {alert_type}",
            "valid_types": [a.value for a in AlertType],
        }
    
    # Get alert template
    template = ALERT_MESSAGES.get(alert_enum)
    if not template:
        return {"error": f"No template for alert type: {alert_type}"}
    
    # Format text with any provided variables
    text = template["text"]
    short_text = template["short_text"]
    try:
        text = text.format(**kwargs)
        short_text = short_text.format(**kwargs)
    except KeyError:
        pass  # Use template as-is if variables not provided
    
    # Build audio URL (static files path)
    audio_file = template.get("audio_file")
    audio_url = f"/static/alerts/{audio_file}" if audio_file else None
    
    # Determine if this should interrupt other audio
    priority = template["priority"]
    should_interrupt = priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]
    
    alert = VoiceAlert(
        alert_type=alert_enum,
        text=text,
        short_text=short_text,
        audio_url=audio_url,
        priority=priority,
        should_interrupt=should_interrupt,
    )
    
    return alert.to_dict()


def get_all_alert_types() -> List[Dict[str, str]]:
    """
    Get list of all available alert types.
    
    Returns:
        List of alert types with descriptions
    """
    return [
        {"type": a.value, "short_text": ALERT_MESSAGES[a]["short_text"]}
        for a in AlertType
    ]


def trigger_voice_alert(
    alert_type: str,
    latitude: float = None,
    longitude: float = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Trigger a voice alert and return playback data.
    
    This is the main API function for triggering alerts.
    
    Args:
        alert_type: Type of alert to trigger
        latitude: Current location (for logging)
        longitude: Current location (for logging)
        **kwargs: Variables for message formatting
        
    Returns:
        Dict with alert data ready for UI playback
    """
    logger.info(f"Voice alert triggered: {alert_type} at ({latitude}, {longitude})")
    
    alert_data = get_voice_alert(alert_type, **kwargs)
    
    # Add location context
    if latitude and longitude:
        alert_data["location"] = {
            "latitude": latitude,
            "longitude": longitude,
        }
    
    # Add TTS fallback instruction
    alert_data["tts_fallback"] = {
        "enabled": True,
        "voice": "en-US-Neural2-D",  # Google TTS voice
        "rate": 1.0,
        "pitch": 1.0,
    }
    
    return alert_data


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Voice Alert System - Test")
    print("=" * 60)
    
    # Test 1: Red Zone Entry
    print("\n--- Test 1: Red Zone Entry ---")
    alert = get_voice_alert("red_zone_entry")
    print(f"Short: {alert['short_text']}")
    print(f"Full: {alert['text']}")
    print(f"Priority: {alert['priority_name']}")
    
    # Test 2: Safe Parking (with variables)
    print("\n--- Test 2: Safe Parking Nearby ---")
    alert = get_voice_alert(
        "safe_parking_nearby",
        stop_name="Pilot #587",
        distance="3.2",
        spaces="45",
    )
    print(f"Message: {alert['text']}")
    
    # Test 3: HOS Warning
    print("\n--- Test 3: HOS Warning ---")
    alert = get_voice_alert("hos_warning", hours="2")
    print(f"Message: {alert['text']}")
    
    # Test 4: GPS Jammer (Critical)
    print("\n--- Test 4: GPS Jammer ---")
    alert = trigger_voice_alert("gps_jammer", latitude=32.7767, longitude=-96.7970)
    print(f"Priority: {alert['priority_name']}")
    print(f"Interrupt: {alert['should_interrupt']}")
    print(f"Message: {alert['text']}")
    
    # Test 5: List all types
    print("\n--- Test 5: All Alert Types ---")
    types = get_all_alert_types()
    for t in types[:5]:
        print(f"  {t['type']}: {t['short_text']}")
    print(f"  ... and {len(types) - 5} more")
    
    print("\n" + "=" * 60)
    print("✅ Voice Alert System test complete!")
