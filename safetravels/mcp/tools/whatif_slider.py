"""
SafeTravels MCP Tools - What-If Time Slider
============================================

Interactive risk calculation that allows users to see how
risk changes based on departure time.

WHAT-IF ANALYSIS:
    "What if I leave at 2 AM instead of 2 PM?"
    → Shows risk expanding/contracting based on time

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, Any, List
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# TIME-BASED RISK MULTIPLIERS
# =============================================================================

# Risk multiplier by hour (0-23)
# Based on 2024 cargo theft statistics
HOURLY_RISK_MULTIPLIERS = {
    # Midnight - 6 AM: Highest risk (drivers sleeping, low visibility)
    0: 1.4,
    1: 1.5,
    2: 1.6,   # Peak risk
    3: 1.6,   # Peak risk
    4: 1.5,
    5: 1.4,
    # 6 AM - 12 PM: Lower risk (daylight, traffic)
    6: 1.1,
    7: 1.0,   # Morning rush - lowest
    8: 0.9,   # Lowest risk
    9: 0.9,
    10: 0.9,
    11: 1.0,
    # 12 PM - 6 PM: Low-moderate risk
    12: 1.0,
    13: 1.0,
    14: 1.0,
    15: 1.1,
    16: 1.1,
    17: 1.2,
    # 6 PM - Midnight: Rising risk
    18: 1.2,
    19: 1.3,
    20: 1.3,
    21: 1.4,
    22: 1.4,
    23: 1.4,
}

# Day of week multipliers (0 = Monday)
DAY_RISK_MULTIPLIERS = {
    0: 0.95,  # Monday
    1: 0.95,  # Tuesday
    2: 1.0,   # Wednesday
    3: 1.0,   # Thursday
    4: 1.15,  # Friday - higher
    5: 1.20,  # Saturday - highest
    6: 1.05,  # Sunday
}

# Month multipliers (holiday theft surge)
MONTH_RISK_MULTIPLIERS = {
    1: 1.0,   # January
    2: 0.95,
    3: 0.95,
    4: 1.0,
    5: 1.0,
    6: 1.05,
    7: 1.05,
    8: 1.0,
    9: 1.05,  # Back to school
    10: 1.10, # Pre-holiday
    11: 1.20, # Holiday surge starts
    12: 1.25, # Peak holiday theft
}


# =============================================================================
# RISK LEVEL THRESHOLDS
# =============================================================================

def get_risk_level(risk_score: float) -> str:
    """Convert risk score to level."""
    if risk_score <= 3.0:
        return "LOW"
    elif risk_score <= 5.0:
        return "MODERATE"
    elif risk_score <= 7.0:
        return "HIGH"
    else:
        return "CRITICAL"


def get_risk_color(risk_score: float) -> str:
    """Get color code for UI visualization."""
    if risk_score <= 3.0:
        return "#22c55e"  # Green
    elif risk_score <= 5.0:
        return "#f59e0b"  # Yellow
    elif risk_score <= 7.0:
        return "#ef4444"  # Red
    else:
        return "#7c2d12"  # Dark red


# =============================================================================
# WHAT-IF CALCULATION
# =============================================================================

def calculate_risk_at_time(
    base_risk: float,
    departure_hour: int,
    departure_day: int = None,
    departure_month: int = None,
) -> Dict[str, Any]:
    """
    Calculate adjusted risk for a specific departure time.
    
    Args:
        base_risk: Base risk score (1-10) for the location
        departure_hour: Hour of departure (0-23)
        departure_day: Day of week (0=Monday, 6=Sunday)
        departure_month: Month (1-12)
        
    Returns:
        Dict with adjusted risk and details
    """
    # Get current date defaults
    now = datetime.now()
    if departure_day is None:
        departure_day = now.weekday()
    if departure_month is None:
        departure_month = now.month
    
    # Get multipliers
    hour_mult = HOURLY_RISK_MULTIPLIERS.get(departure_hour, 1.0)
    day_mult = DAY_RISK_MULTIPLIERS.get(departure_day, 1.0)
    month_mult = MONTH_RISK_MULTIPLIERS.get(departure_month, 1.0)
    
    # Calculate combined multiplier
    combined_mult = hour_mult * day_mult * month_mult
    
    # Apply to base risk (cap at 10)
    adjusted_risk = min(10.0, base_risk * combined_mult)
    
    # Get level and color
    level = get_risk_level(adjusted_risk)
    color = get_risk_color(adjusted_risk)
    
    # Format time for display
    hour_12 = departure_hour % 12 or 12
    am_pm = "AM" if departure_hour < 12 else "PM"
    time_str = f"{hour_12}:00 {am_pm}"
    
    return {
        "base_risk": round(base_risk, 1),
        "adjusted_risk": round(adjusted_risk, 1),
        "risk_level": level,
        "risk_color": color,
        "departure_time": time_str,
        "departure_hour": departure_hour,
        "multipliers": {
            "time_of_day": round(hour_mult, 2),
            "day_of_week": round(day_mult, 2),
            "month": round(month_mult, 2),
            "combined": round(combined_mult, 2),
        },
        "recommendation": _get_time_recommendation(level, departure_hour),
    }


def _get_time_recommendation(level: str, hour: int) -> str:
    """Get recommendation based on risk level and time."""
    if level == "CRITICAL":
        if 2 <= hour <= 5:
            return "⛔ Avoid departing at this time. Night hours have highest theft risk."
        return "⚠️ High risk time. Consider alternative departure time."
    elif level == "HIGH":
        return "🟡 Elevated risk. Take extra precautions if departing now."
    elif level == "MODERATE":
        return "✓ Moderate risk. Standard precautions recommended."
    else:
        return "✅ Good time to depart. Lower risk window."


# =============================================================================
# WHAT-IF SLIDER DATA
# =============================================================================

def get_hourly_risk_profile(
    base_risk: float,
    departure_day: int = None,
    departure_month: int = None,
) -> List[Dict[str, Any]]:
    """
    Get risk profile for all 24 hours.
    
    Useful for rendering a slider or chart showing
    how risk changes throughout the day.
    
    Args:
        base_risk: Base location risk (1-10)
        departure_day: Day of week
        departure_month: Month
        
    Returns:
        List of 24 hourly risk calculations
    """
    profile = []
    
    for hour in range(24):
        risk_data = calculate_risk_at_time(
            base_risk=base_risk,
            departure_hour=hour,
            departure_day=departure_day,
            departure_month=departure_month,
        )
        profile.append(risk_data)
    
    # Add statistics
    risks = [p["adjusted_risk"] for p in profile]
    min_risk = min(risks)
    max_risk = max(risks)
    min_hour = risks.index(min_risk)
    max_hour = risks.index(max_risk)
    
    return {
        "hourly_profile": profile,
        "statistics": {
            "min_risk": round(min_risk, 1),
            "min_risk_hour": min_hour,
            "max_risk": round(max_risk, 1),
            "max_risk_hour": max_hour,
            "risk_range": round(max_risk - min_risk, 1),
        },
        "best_departure_time": f"{min_hour % 12 or 12}:00 {'AM' if min_hour < 12 else 'PM'}",
        "worst_departure_time": f"{max_hour % 12 or 12}:00 {'AM' if max_hour < 12 else 'PM'}",
    }


def what_if_departure(
    latitude: float,
    longitude: float,
    base_risk: float,
    hour: int = None,
) -> Dict[str, Any]:
    """
    Main API function for What-If time analysis.
    
    If hour is provided, calculates risk for that hour.
    If hour is None, returns full 24-hour profile.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        base_risk: Base risk score (1-10)
        hour: Optional specific hour (0-23)
        
    Returns:
        What-If analysis results
    """
    logger.info(f"What-If analysis: ({latitude}, {longitude}), base_risk={base_risk}")
    
    if hour is not None:
        # Single hour calculation
        result = calculate_risk_at_time(base_risk, hour)
        result["location"] = {"latitude": latitude, "longitude": longitude}
        return result
    else:
        # Full 24-hour profile
        profile = get_hourly_risk_profile(base_risk)
        profile["location"] = {"latitude": latitude, "longitude": longitude}
        profile["base_risk"] = base_risk
        return profile


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("What-If Time Slider - Test")
    print("=" * 60)
    
    base = 5.0  # Moderate base risk
    
    # Test 1: Compare 2 AM vs 2 PM
    print(f"\n--- Test 1: Compare times (base risk = {base}) ---")
    am = calculate_risk_at_time(base, 2)  # 2 AM
    pm = calculate_risk_at_time(base, 14)  # 2 PM
    print(f"2 AM: {am['adjusted_risk']}/10 ({am['risk_level']})")
    print(f"2 PM: {pm['adjusted_risk']}/10 ({pm['risk_level']})")
    print(f"Difference: {am['adjusted_risk'] - pm['adjusted_risk']:.1f} points")
    
    # Test 2: Friday night vs Sunday morning
    print("\n--- Test 2: Friday night vs Sunday morning ---")
    fri = calculate_risk_at_time(base, 22, departure_day=4)  # Friday 10 PM
    sun = calculate_risk_at_time(base, 9, departure_day=6)   # Sunday 9 AM
    print(f"Friday 10 PM: {fri['adjusted_risk']}/10")
    print(f"Sunday 9 AM: {sun['adjusted_risk']}/10")
    
    # Test 3: Full profile
    print("\n--- Test 3: 24-hour profile ---")
    profile = get_hourly_risk_profile(base)
    print(f"Best time: {profile['best_departure_time']} (risk: {profile['statistics']['min_risk']})")
    print(f"Worst time: {profile['worst_departure_time']} (risk: {profile['statistics']['max_risk']})")
    print(f"Risk range: {profile['statistics']['risk_range']} points")
    
    # Test 4: Holiday surge (December)
    print("\n--- Test 4: Holiday surge (December) ---")
    normal = calculate_risk_at_time(base, 14, departure_month=6)  # June
    holiday = calculate_risk_at_time(base, 14, departure_month=12)  # December
    print(f"June 2 PM: {normal['adjusted_risk']}/10")
    print(f"December 2 PM: {holiday['adjusted_risk']}/10")
    
    print("\n" + "=" * 60)
    print("✅ What-If Time Slider test complete!")
