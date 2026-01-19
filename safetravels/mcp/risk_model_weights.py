"""
SafeTravels MCP - Configuration
===============================

Central configuration for cargo theft risk scoring.
Contains all weight multipliers and constants used in risk calculations.

This file is the SINGLE SOURCE OF TRUTH for all risk factors.
Adjust values here based on real-world data analysis.

FACTOR CATEGORIES:
    1. Temporal:     time_of_day, day_of_week, month, season
    2. Cargo:        commodity_type, cargo_value
    3. Location:     location_type, hotspot_state, risky_corridor
    4. Environmental: weather, event, traffic
    5. Historical:   accident_history, crime_rate

Design Principles:
    - All weights are documented with reasoning
    - Default multiplier is 1.0 (no effect)
    - Values > 1.0 increase risk
    - Values < 1.0 decrease risk (safer)

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, List, Tuple

# =============================================================================
# RISK SCORE BOUNDS
# =============================================================================

# Maximum possible risk score (cap)
MAX_RISK_SCORE: float = 10.0

# Minimum possible risk score (floor)
MIN_RISK_SCORE: float = 1.0

# Risk level thresholds
RISK_THRESHOLDS = {
    "LOW": 3.0,       # 1.0 - 3.0: Low risk
    "MODERATE": 5.0,  # 3.1 - 5.0: Moderate risk
    "HIGH": 7.0,      # 5.1 - 7.0: High risk
    "CRITICAL": 10.0, # 7.1 - 10.0: Critical risk
}


# =============================================================================
# TEMPORAL FACTORS
# =============================================================================

# -----------------------------------------------------------------------------
# Time of Day Weights
# -----------------------------------------------------------------------------
# Night hours (10 PM - 5 AM) have 50% higher theft rates.
# Criminals prefer darkness for concealment and reduced witness presence.
# Source: CargoNet Annual Report, FBI UCR data

TIME_WEIGHTS: Dict[str, float] = {
    "night": 1.5,       # 10 PM - 5 AM: Peak theft hours, reduced visibility
    "evening": 1.25,    # 5 PM - 10 PM: Transition period, fewer witnesses
    "day": 1.0,         # 5 AM - 5 PM: Baseline, most activity
}

# -----------------------------------------------------------------------------
# Day of Week Weights
# -----------------------------------------------------------------------------
# Weekend nights show higher theft rates due to:
#   - Reduced security staffing
#   - Longer parking durations
#   - Fewer witnesses
# Friday/Saturday nights are peak times for organized theft.

DAY_WEIGHTS: Dict[str, float] = {
    "monday": 1.0,      # Baseline
    "tuesday": 1.0,     # Baseline
    "wednesday": 1.0,   # Baseline
    "thursday": 1.05,   # Slight increase as weekend approaches
    "friday": 1.15,     # Weekend begins, more overnight parking
    "saturday": 1.2,    # Peak weekend, extended stops
    "sunday": 1.1,      # Weekend end, still elevated
}

# -----------------------------------------------------------------------------
# Month Weights
# -----------------------------------------------------------------------------
# Seasonal patterns based on CargoNet data:
#   - November/December: Holiday shipping surge = more targets
#   - August/September: Back-to-school electronics
#   - January: Post-holiday returns in transit

MONTH_WEIGHTS: Dict[str, float] = {
    "january": 1.1,     # Post-holiday returns, electronics still moving
    "february": 1.0,    # Baseline
    "march": 1.0,       # Baseline
    "april": 1.0,       # Baseline
    "may": 1.0,         # Baseline
    "june": 1.1,        # Summer shipping increase
    "july": 1.1,        # Summer peak
    "august": 1.2,      # Back-to-school electronics surge
    "september": 1.15,  # Back-to-school continues
    "october": 1.1,     # Pre-holiday inventory buildup
    "november": 1.3,    # Holiday season begins, Black Friday
    "december": 1.4,    # Peak holiday shipping, highest theft rates
}

# -----------------------------------------------------------------------------
# Season / Special Period Weights
# -----------------------------------------------------------------------------
# Special periods with significantly elevated risk.
# These override the base month weight when active.

SEASON_WEIGHTS: Dict[str, float] = {
    "black_friday_week": 1.5,   # Thanksgiving week: highest value shipments
    "holiday_peak": 1.4,        # Dec 15 - Dec 31: Gift electronics + chaos
    "christmas_week": 1.45,     # Dec 20 - Dec 26: Peak vulnerability
    "new_years_week": 1.3,      # Dec 27 - Jan 3: Reduced staffing
    "back_to_school": 1.2,      # Aug 1 - Sep 15: Electronics spike
    "summer": 1.1,              # Jun - Aug: More trucks, longer days
    "normal": 1.0,              # Rest of year
}


# =============================================================================
# CARGO FACTORS
# =============================================================================

# -----------------------------------------------------------------------------
# Commodity Type Weights
# -----------------------------------------------------------------------------
# Based on CargoNet theft data rankings:
#   1. Electronics (TVs, computers, phones) - highest resale value
#   2. Pharmaceuticals - organized crime networks
#   3. Alcohol/Tobacco - easy black market sale
#   4. Clothing/Footwear - brand name items
# Less targeted: Food (perishable), raw materials (hard to resell)

COMMODITY_WEIGHTS: Dict[str, float] = {
    # High Target (organized theft rings)
    "electronics": 1.5,         # #1 most stolen: TVs, laptops, phones
    "pharmaceuticals": 1.45,    # #2 most stolen: high street value
    "consumer_electronics": 1.5,# Same as electronics
    "computers": 1.45,          # Laptops, servers, components
    "phones": 1.4,              # Mobile devices
    
    # Moderate-High Target
    "alcohol": 1.3,             # Easy to resell, hard to trace
    "tobacco": 1.3,             # High street value
    "automotive_parts": 1.25,   # Specific demand, organized buyers
    "appliances": 1.2,          # Large electronics
    "clothing": 1.2,            # Brand name apparel
    "footwear": 1.2,            # Designer shoes
    
    # Moderate Target
    "household_goods": 1.1,     # General consumer products
    "cosmetics": 1.15,          # Beauty products, brand value
    "tools": 1.1,               # Power tools, equipment
    
    # Low Target (perishable or hard to resell)
    "food_beverage": 1.0,       # Perishable, time-sensitive
    "produce": 0.95,            # Very perishable
    "raw_materials": 0.9,       # Hard to resell, traceable
    "lumber": 0.85,             # Heavy, low value density
    "general": 1.0,             # Baseline for unspecified
}

# -----------------------------------------------------------------------------
# Cargo Value Tiers
# -----------------------------------------------------------------------------
# Higher value loads attract more sophisticated, organized theft.
# Million-dollar loads may trigger targeted surveillance by crime rings.

CARGO_VALUE_TIERS: Dict[str, Tuple[float, float, float]] = {
    # (min_value, max_value, multiplier)
    "ultra_high": (1_000_000, float('inf'), 1.6),   # $1M+: Crime ring target
    "very_high": (500_000, 999_999, 1.4),           # $500K-$1M: High value
    "high": (250_000, 499_999, 1.25),               # $250K-$500K: Elevated
    "moderate": (100_000, 249_999, 1.1),            # $100K-$250K: Moderate
    "standard": (0, 99_999, 1.0),                   # Under $100K: Baseline
}


# =============================================================================
# LOCATION FACTORS
# =============================================================================

# -----------------------------------------------------------------------------
# Location Type Weights
# -----------------------------------------------------------------------------
# Security features dramatically affect theft risk.
# Secured facilities with guards, fencing, and CCTV reduce risk.
# Unsecured random stops are prime targets.

LOCATION_WEIGHTS: Dict[str, float] = {
    # High Risk (avoid if possible)
    "random_roadside": 1.6,     # Unpredictable, no security, isolated
    "unsecured_lot": 1.5,       # No security, often dark
    "abandoned_area": 1.7,      # Extremely isolated, no witnesses
    
    # Moderate Risk
    "rest_area": 1.3,           # Public but minimal security
    "truck_stop_basic": 1.1,    # Some lighting, minimal cameras
    "industrial_area": 1.2,     # Often empty at night
    
    # Lower Risk (preferred stops)
    "truck_stop_secured": 0.8,  # Fenced, guards, 24/7 CCTV
    "truck_stop_premium": 0.7,  # Full security, well-lit, patrols
    "distribution_center": 0.6, # High security, controlled access
    "shipper_facility": 0.5,    # Origin/destination, best security
}

# -----------------------------------------------------------------------------
# State Hotspot Weights
# -----------------------------------------------------------------------------
# Certain states are documented cargo theft hotspots.
# Based on CargoNet, NICB, and FBI data.
# California alone accounts for ~20% of all US cargo theft.

HOTSPOT_STATES: Dict[str, float] = {
    "CA": 1.35,     # #1 - California: Ports, highways, population
    "TX": 1.3,      # #2 - Texas: I-10 corridor, border proximity
    "FL": 1.25,     # #3 - Florida: Ports, I-95 corridor
    "IL": 1.2,      # #4 - Illinois: Chicago hub, I-90/I-94
    "GA": 1.2,      # #5 - Georgia: Atlanta distribution hub
    "NJ": 1.15,     # #6 - New Jersey: Port Newark, dense traffic
    "PA": 1.1,      # #7 - Pennsylvania: I-76, I-80 corridors
    "TN": 1.1,      # #8 - Tennessee: Memphis hub
    "AZ": 1.1,      # Border state, I-10 corridor
    "NM": 1.05,     # Border state, I-10 corridor
}

# Default weight for states not in hotspot list
DEFAULT_STATE_WEIGHT: float = 1.0

# -----------------------------------------------------------------------------
# Risky Corridor Definitions
# -----------------------------------------------------------------------------
# Known theft corridors based on historical data.
# These highways/routes have documented patterns of organized theft.

RISKY_CORRIDORS: List[Dict] = [
    {
        "name": "I-10 LA to Houston",
        "description": "Trans-continental corridor, highest theft concentration",
        "states": ["CA", "AZ", "NM", "TX"],
        "multiplier": 1.4,
    },
    {
        "name": "I-95 East Coast",
        "description": "Major port access, dense population",
        "states": ["FL", "GA", "SC", "NC", "VA", "MD", "NJ", "NY"],
        "multiplier": 1.3,
    },
    {
        "name": "I-35 Texas Corridor",
        "description": "NAFTA highway, border proximity",
        "states": ["TX"],
        "multiplier": 1.25,
    },
    {
        "name": "I-5 West Coast",
        "description": "California ports to Pacific Northwest",
        "states": ["CA", "OR", "WA"],
        "multiplier": 1.2,
    },
    {
        "name": "I-80 Northern Route",
        "description": "Cross-country, Chicago access",
        "states": ["CA", "NV", "UT", "WY", "NE", "IA", "IL", "IN", "OH", "PA", "NJ"],
        "multiplier": 1.15,
    },
]


# =============================================================================
# ENVIRONMENTAL FACTORS
# =============================================================================

# -----------------------------------------------------------------------------
# Weather Condition Weights
# -----------------------------------------------------------------------------
# Severe weather impacts theft risk:
#   - Reduced visibility = easier approach
#   - Slower emergency response times
#   - Drivers forced to stop unexpectedly

WEATHER_WEIGHTS: Dict[str, float] = {
    "severe_storm": 1.35,   # Dangerous: low visibility, slow response
    "storm": 1.25,          # Heavy rain/wind: reduced visibility
    "heavy_rain": 1.15,     # Moderate visibility issues
    "fog": 1.2,             # Significantly reduced visibility
    "snow": 1.15,           # Slower response, drivers may stop
    "ice": 1.2,             # Drivers forced to stop, accidents
    "extreme_heat": 1.05,   # Minor: driver fatigue
    "clear": 1.0,           # Baseline
    "cloudy": 1.0,          # No significant impact
    "light_rain": 1.0,      # Minimal impact
}

# -----------------------------------------------------------------------------
# Event / Disturbance Weights
# -----------------------------------------------------------------------------
# Major events divert attention and resources away from cargo security.
# Civil unrest creates chaos that enables opportunistic theft.

EVENT_WEIGHTS: Dict[str, float] = {
    # Highest Risk (avoid area entirely if possible)
    "civil_unrest": 2.0,        # Riots, looting: opportunistic theft
    "riot": 2.0,                # Same as civil unrest
    
    # High Risk (significant distraction)
    "major_protest": 1.6,       # Large gatherings, diverted police
    "emergency_evacuation": 1.5,# Chaos, reduced oversight
    
    # Moderate Risk (some resource diversion)
    "large_event": 1.3,         # Concerts, sports: traffic + distraction
    "festival": 1.25,           # Multi-day events, tourism surge
    "convention": 1.2,          # Business events, hotel area crime
    
    # Slight Risk
    "holiday": 1.15,            # Reduced staffing, more travelers
    "construction": 1.1,        # Blocked exits, reduced visibility
    
    # Baseline
    "none": 1.0,                # Normal conditions
}

# -----------------------------------------------------------------------------
# Traffic Condition Weights
# -----------------------------------------------------------------------------
# Real-time traffic affects vulnerability.
# Stopped/slow traffic = sitting target for theft.
# Thieves monitor traffic apps to find stuck trucks.

TRAFFIC_WEIGHTS: Dict[str, float] = {
    "standstill": 1.5,      # Major incident: truck is immobile target
    "severe": 1.4,          # Nearly stopped, extended exposure
    "heavy": 1.25,          # Slow-moving, frequent stops
    "moderate": 1.1,        # Some delays
    "light": 1.0,           # Normal flow
    "free_flow": 0.95,      # Optimal: moving quickly, harder target
}

# -----------------------------------------------------------------------------
# Accident History Weights
# -----------------------------------------------------------------------------
# Historical accident data for a road segment.
# Accident-prone areas mean trucks frequently get stuck there.
# Thieves learn these patterns and stake out these locations.

ACCIDENT_HISTORY_WEIGHTS: Dict[str, float] = {
    "very_high": 1.4,       # Frequent accidents: known trouble spot
    "high": 1.25,           # Regular accidents
    "moderate": 1.1,        # Occasional issues
    "low": 1.0,             # Baseline
    "very_low": 0.95,       # Rarely any incidents
}


# =============================================================================
# ROUTE-LEVEL FACTORS
# =============================================================================

# -----------------------------------------------------------------------------
# Route Length (Exposure) Weights
# -----------------------------------------------------------------------------
# Longer routes = more stops = more exposure time.
# Cross-country routes have significantly higher cumulative risk.

ROUTE_LENGTH_TIERS: Dict[str, Tuple[float, float, float]] = {
    # (min_miles, max_miles, multiplier)
    "cross_country": (1500, float('inf'), 1.4),  # 1500+ miles
    "long_haul": (1000, 1499, 1.25),             # 1000-1500 miles
    "regional": (500, 999, 1.1),                 # 500-1000 miles
    "short_haul": (0, 499, 1.0),                 # Under 500 miles
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_risk_level(score: float) -> str:
    """
    Convert numeric risk score to human-readable level.
    
    Args:
        score: Risk score from 1-10
        
    Returns:
        Risk level: 'low', 'moderate', 'high', or 'critical'
    """
    if score <= RISK_THRESHOLDS["LOW"]:
        return "low"
    elif score <= RISK_THRESHOLDS["MODERATE"]:
        return "moderate"
    elif score <= RISK_THRESHOLDS["HIGH"]:
        return "high"
    else:
        return "critical"


def clamp_score(score: float) -> float:
    """
    Ensure score stays within valid bounds [MIN, MAX].
    
    Args:
        score: Raw calculated score
        
    Returns:
        Score clamped between MIN_RISK_SCORE and MAX_RISK_SCORE
    """
    return max(MIN_RISK_SCORE, min(score, MAX_RISK_SCORE))


def get_value_multiplier(cargo_value: float) -> float:
    """
    Get cargo value multiplier based on dollar amount.
    
    Args:
        cargo_value: Total declared cargo value in USD
        
    Returns:
        Multiplier from CARGO_VALUE_TIERS
    """
    for tier_name, (min_val, max_val, multiplier) in CARGO_VALUE_TIERS.items():
        if min_val <= cargo_value <= max_val:
            return multiplier
    return 1.0  # Default


def get_state_multiplier(state_code: str) -> float:
    """
    Get hotspot multiplier for a US state.
    
    Args:
        state_code: Two-letter state abbreviation (e.g., 'CA', 'TX')
        
    Returns:
        Multiplier from HOTSPOT_STATES or DEFAULT_STATE_WEIGHT
    """
    return HOTSPOT_STATES.get(state_code.upper(), DEFAULT_STATE_WEIGHT)


def get_route_length_multiplier(miles: float) -> float:
    """
    Get exposure multiplier based on route length.
    
    Args:
        miles: Total route distance in miles
        
    Returns:
        Multiplier from ROUTE_LENGTH_TIERS
    """
    for tier_name, (min_miles, max_miles, multiplier) in ROUTE_LENGTH_TIERS.items():
        if min_miles <= miles <= max_miles:
            return multiplier
    return 1.0  # Default
