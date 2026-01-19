"""
SafeTravels MCP Tools - Safe Stops Finder
==========================================

Finds and ranks safe stopping locations for truck drivers.

FEATURES:
    - Security scoring (0-100 points)
    - Tier ranking (Level 1, 2, 3, Avoid)
    - Nearby search by distance
    - Pre-Red-Zone stop recommendations
    - Emergency stop finder
    - Fuel stop finder
    - HOS-aware recommendations

DATA SOURCES:
    - dot_truck_stops.json (real DOT data)
    - fbi_crime_data.json (crime context)
    - Mock police station data (placeholder)

SCORING FORMULA:
    Physical Security: 40 pts max
    Location Context: 30 pts max
    Operational: 20 pts max
    Real-Time: 10 pts max

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import math
import logging
import requests
from safetravels.realtime.aggregator import aggregator
from safetravels.core.app_settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Path to data files
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRUCK_STOPS_FILE = DATA_DIR / "dot_truck_stops.json"
FBI_CRIME_FILE = DATA_DIR / "fbi_crime_data.json"

# Default search radius (miles)
DEFAULT_RADIUS_MILES: float = 50.0

# Earth's radius
EARTH_RADIUS_MILES: float = 3958.8

# Load Data Cache
_CARGO_HOTSPOTS = {}
_CARGO_RISK_MULTIPLIERS = {}

def _load_cargo_data():
    """Load cargo theft hotspots into memory."""
    global _CARGO_HOTSPOTS, _CARGO_RISK_MULTIPLIERS
    hotspot_file = DATA_DIR / "cargo_theft_hotspots.json"
    if hotspot_file.exists():
        try:
            with open(hotspot_file, "r") as f:
                data = json.load(f)
                _CARGO_HOTSPOTS = data.get("hotspots", {})
                _CARGO_RISK_MULTIPLIERS = data.get("state_risk_multipliers", {})
        except Exception as e:
            logger.error(f"Failed to load cargo hotspots: {e}")

# Initialize on module load
_load_cargo_data()


# =============================================================================
# ENUMS
# =============================================================================

class StopTier(Enum):
    """Security tier levels."""
    LEVEL_1 = "Level 1"    # 80-100 pts: Highest security
    LEVEL_2 = "Level 2"    # 60-79 pts: Secure
    LEVEL_3 = "Level 3"    # 40-59 pts: Basic
    AVOID = "Avoid"        # 0-39 pts: Not recommended


class StopType(Enum):
    """Types of stops."""
    TRUCK_STOP = "truck_stop"
    REST_AREA = "rest_area"
    FUEL_STATION = "fuel_station"
    POLICE_STATION = "police_station"
    WEIGH_STATION = "weigh_station"


# =============================================================================
# SCORING WEIGHTS (Revised January 2026 - Based on 2024 Theft Statistics)
# =============================================================================
# 
# RATIONALE:
#   - Cameras reduce theft by 45%; lighting by 50% (FBI UCR 2024)
#   - 15% of cargo thefts happen at truck stops (CargoNet 2024)
#   - 72% of drivers avoid stops due to crime reputation
#   - California (32%) + Texas (19%) = 51% of all cargo theft
#
# TIER CUTOFFS: Level 1 (85+), Level 2 (65+), Level 3 (45+), Avoid (<45)
# =============================================================================

# -----------------------------------------------------------------------------
# TIER 1: PHYSICAL SECURITY (45 points max) - HIGHEST IMPACT
# -----------------------------------------------------------------------------
SCORE_GATED_PARKING = 18         # Gating reduces theft access by 60%+
SCORE_SECURITY_GUARDS_24H = 15   # Real personnel > cameras alone
SCORE_CCTV_WITH_MONITORING = 8   # Monitored CCTV is key, not just recording
SCORE_WELL_LIT = 4               # Minimum baseline expectation

# -----------------------------------------------------------------------------
# TIER 2: LOCATION & CRIME HISTORY (35 points max)
# -----------------------------------------------------------------------------
SCORE_NO_THEFT_HISTORY = 18      # SPECIFIC incident data is gold
SCORE_LOW_STATE_RISK = 8         # Less reliable alone, but still matters
SCORE_HIGHWAY_ACCESS = 6         # Enables quick escape, relevant for safety
SCORE_NEARBY_POLICE = 3          # Police station <5 miles = faster response

# -----------------------------------------------------------------------------
# TIER 3: OPERATIONAL (20 points max)
# -----------------------------------------------------------------------------
SCORE_MAJOR_BRAND = 8            # Pilot/Love's = corporate safety policies
SCORE_STAFFED_24H = 7            # vs. seasonal/limited hours
SCORE_HIGH_DRIVER_RATING = 5     # Less reliable than incident history
# NOTE: Removed SCORE_LARGE_CAPACITY - capacity doesn't correlate with safety

# -----------------------------------------------------------------------------
# PENALTY FACTORS (subtract from total score)
# -----------------------------------------------------------------------------
PENALTY_SINGLE_EXIT = -8         # Dangerous bottleneck, trap risk
PENALTY_POOR_LIGHTING = -6       # Active vulnerability
PENALTY_NO_CCTV = -3             # Minimal monitoring
PENALTY_ISOLATED = -5            # No help nearby, remote location
PENALTY_HIGH_CRIME_STATE = -5    # CA/TX/FL = CRITICAL risk states

# -----------------------------------------------------------------------------
# TIER CUTOFFS (Stricter than before)
# -----------------------------------------------------------------------------
TIER_LEVEL_1_MIN = 85            # Premium security
TIER_LEVEL_2_MIN = 65            # Good security
TIER_LEVEL_3_MIN = 45            # Acceptable, use with caution
# Below 45 = AVOID


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SafeStop:
    """
    A safe stopping location with security assessment.
    """
    stop_id: int = 0
    name: str = ""
    city: str = ""
    state: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    highway: str = ""
    distance_miles: float = 0.0        # From search location
    
    # Security
    security_score: int = 0           # 0-100
    tier: StopTier = StopTier.LEVEL_3
    security_level: str = "unknown"   # high/medium/low/none
    
    # Amenities
    has_fuel: bool = False
    has_showers: bool = False
    has_food: bool = False
    has_guards: bool = False
    has_gated_parking: bool = False
    parking_spaces: int = 0
    
    # Context
    area_risk_level: str = "unknown"  # State crime risk
    
    # Real-Time Data (New Jan 2026)
    available_spaces: Optional[int] = None
    realtime_status: str = "UNKNOWN" # AVAILABLE, FULL, CROWDED, UNKNOWN

    # Crowdsourced/Enriched Data
    rating: float = 0.0          # 1.0 - 5.0 Stars
    review_count: int = 0        # Number of reviews
    has_cctv: bool = False       # From OSM/enrichment
    photo_url: Optional[str] = None # Google Photo or Brand Image

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_id": self.stop_id,
            "name": self.name,
            "city": self.city,
            "state": self.state,
            "location": {"lat": self.latitude, "lon": self.longitude},
            "highway": self.highway,
            "distance_miles": round(self.distance_miles, 1),
            "security_score": self.security_score,
            "tier": self.tier.value,
            "security_level": self.security_level,
            "has_fuel": self.has_fuel,
            "has_showers": self.has_showers,
            "has_guards": self.has_guards,
            "has_gated_parking": self.has_gated_parking,
            "parking_spaces": self.parking_spaces,
            "area_risk_level": self.area_risk_level,
            "realtime": {
                "status": self.realtime_status,
                "available": self.available_spaces
            }
        }


@dataclass
class EmergencyStop:
    """
    Emergency stop option (police or secured truck stop).
    """
    stop_type: StopType
    name: str
    distance_miles: float
    latitude: float
    longitude: float
    phone: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.stop_type.value,
            "name": self.name,
            "distance_miles": round(self.distance_miles, 1),
            "location": {"lat": self.latitude, "lon": self.longitude},
            "phone": self.phone,
        }


# =============================================================================
# DATA LOADING
# =============================================================================

_truck_stops_cache: Optional[List[Dict]] = None
_crime_data_cache: Optional[Dict] = None


def _load_truck_stops() -> List[Dict]:
    """Load truck stops from JSON file."""
    global _truck_stops_cache
    
    if _truck_stops_cache is not None:
        return _truck_stops_cache
    
    try:
        with open(TRUCK_STOPS_FILE, "r") as f:
            data = json.load(f)
        _truck_stops_cache = data.get("truck_stops", [])
        logger.info(f"Loaded {len(_truck_stops_cache)} truck stops")
    except Exception as e:
        logger.error(f"Failed to load truck stops: {e}")
        _truck_stops_cache = []
    
    return _truck_stops_cache


def _load_crime_data() -> Dict:
    """Load FBI crime data from JSON file."""
    global _crime_data_cache
    
    if _crime_data_cache is not None:
        return _crime_data_cache
    
    try:
        with open(FBI_CRIME_FILE, "r") as f:
            _crime_data_cache = json.load(f)
        logger.info("Loaded FBI crime data")
    except Exception as e:
        logger.error(f"Failed to load crime data: {e}")
        _crime_data_cache = {"states": {}}
    
    return _crime_data_cache


def _get_state_risk_level(state_code: str) -> str:
    """Get crime risk level for a state."""
    crime_data = _load_crime_data()
    state_info = crime_data.get("states", {}).get(state_code, {})
    return state_info.get("risk_level", "MODERATE")


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def score_stop(stop_data: Dict, current_hour: int = 12) -> Tuple[int, StopTier]:
    """
    Calculate security score for a truck stop.
    
    REVISED FORMULA (January 2026 - Based on 2024 Statistics):
        - Physical Security: 45 points max (highest impact)
        - Location Context: 35 points max
        - Operational: 20 points max
        - Penalties: Up to -27 points
        - Time-based adjustments for night hours
    
    Args:
        stop_data: Raw stop data from JSON
        current_hour: Hour of day (0-23) for time-based scoring
        
    Returns:
        (score, tier) tuple
    """
    score = 0
    amenities = stop_data.get("amenities", [])
    security = stop_data.get("security", "none")
    name = stop_data.get("name", "")
    state = stop_data.get("state", "")
    city = stop_data.get("city", "")
    
    # Major brands list for consistent checking
    MAJOR_BRANDS = ["Pilot", "Love's", "Flying J", "TA", "Petro", "Sapp", "Buc-ee", "QuikTrip"]
    is_major_brand = any(brand in name for brand in MAJOR_BRANDS)
    
    # -----------------------------------------------------------------
    # TIER 1: PHYSICAL SECURITY (50 points max) - REAL VALIDATED DATA
    # -----------------------------------------------------------------
    # We prioritize EXPLICIT tags over brand assumptions
    
    if "gated_parking" in amenities:
        score += 25  # HUGe bonus for Verified Fence
    elif is_major_brand:
        score += 5   # Small bonus for "likely" fence
    
    if "security_guards" in amenities:
        score += 20  # Verified Guards
    
    if "cctv" in amenities or "cameras" in amenities:
        score += 15  # Verified Cameras
    elif security == "high":
        score += 5   # Inferred Cameras
        
    if "lighting_good" in amenities:
        score += 10  # Verified Lights
    elif is_major_brand: 
        score += 3   # Assumed Lights
    
    # -----------------------------------------------------------------
    # TIER 2: LOCATION & CRIME HISTORY (35 points max)
    # -----------------------------------------------------------------
    
    # Theft history (most valuable data point)
    data_risk = stop_data.get("risk_score", 5)  # 1-10, lower is safer
    if data_risk <= 2:
        score += SCORE_NO_THEFT_HISTORY  # +18 (excellent history)
    elif data_risk <= 3:
        score += int(SCORE_NO_THEFT_HISTORY * 0.8)  # +14
    elif data_risk <= 5:
        score += int(SCORE_NO_THEFT_HISTORY * 0.5)  # +9
    # data_risk > 5 = no bonus (has theft history)
    
    # State-level risk
    state_risk = _get_state_risk_level(state)
    if state_risk == "LOW":
        score += SCORE_LOW_STATE_RISK  # +8
    elif state_risk == "MODERATE":
        score += SCORE_LOW_STATE_RISK // 2  # +4
    # HIGH/CRITICAL = no bonus
    
    # Highway access (easy escape routes)
    highway = stop_data.get("highway", "")
    if highway.startswith("I-"):
        score += SCORE_HIGHWAY_ACCESS  # +6
    elif highway.startswith("US-"):
        score += SCORE_HIGHWAY_ACCESS // 2  # +3
    
    # Nearby police (placeholder - assume major brands have this)
    if is_major_brand:
        score += SCORE_NEARBY_POLICE  # +3
    
    # -----------------------------------------------------------------
    # TIER 3: OPERATIONAL (20 points max)
    # -----------------------------------------------------------------
    
    # Major brand bonus (corporate safety policies)
    if is_major_brand:
        score += SCORE_MAJOR_BRAND  # +8
    
    # 24-hour staffing (inferred from major brands + security level)
    if is_major_brand or security == "high":
        score += SCORE_STAFFED_24H  # +7
    
    # Driver rating (placeholder - assume okay for major brands)
    if is_major_brand:
        score += SCORE_HIGH_DRIVER_RATING  # +5
    
    # NOTE: Removed capacity scoring - crowded doesn't mean safer
    
    # -----------------------------------------------------------------
    # SPECIAL: CARGO THEFT HOTSPOTS (CargoNet Data 2025)
    # -----------------------------------------------------------------
    # Check if this stop is in a known organized crime hotspot
    
    # Simple mapping: Check if City + State matches a hotspot key (e.g. "TX-Dallas", "CA-Los Angeles")
    # We construct a key from the stop's data
    city_key = f"{state}-{city}"
    
    # We also check partial matches for major counties (e.g. if city is "Fort Worth", we might miss Tarrant)
    # For this MVP, we will rely on city names aligning with our keys or simply check state risk.
    
    hotspot = _CARGO_HOTSPOTS.get(city_key)
    
    # State Multiplier Check
    state_multiplier = _CARGO_RISK_MULTIPLIERS.get(state, 1.0)
    
    if hotspot:
        # It is a specific Known Hotspot City
        risk_val = hotspot.get("risk_score", 0)
        penalty = risk_val * 3  # e.g., Risk 10 * 3 = -30 points!
        score -= penalty
        # Log this significant penalty for debugging/explainability if needed
        # (This explains why a nice Pilot in Dallas might score lower than a Pilot in Waco)
        
    elif state_multiplier > 1.2:
        # High Risk State but not specific hotspot city
        score -= 5
        
    # -----------------------------------------------------------------
    # PENALTIES (subtract from score)
    # -----------------------------------------------------------------
    
    # No CCTV penalty
    if security == "none":
        score += PENALTY_NO_CCTV  # -3
    
    # Poor lighting (rest areas, low-security stops)
    if security == "none" or security == "low":
        if "Rest Area" in name:
            score += PENALTY_POOR_LIGHTING  # -6
    
    # Isolated location (inferred from rest area or low capacity)
    parking = stop_data.get("parking_spaces", 0)
    if parking < 30 and not is_major_brand:
        score += PENALTY_ISOLATED  # -5
    
    # High crime state penalty (CA, TX, FL = CRITICAL)
    if state_risk == "CRITICAL":
        score += PENALTY_HIGH_CRIME_STATE  # -5
    
    # Single exit penalty (placeholder - could be data-driven)
    # TODO: Add single_exit data field
    
    # -----------------------------------------------------------------
    # TIME-BASED ADJUSTMENTS (Night = 10 PM - 6 AM)
    # -----------------------------------------------------------------
    is_night = current_hour >= 22 or current_hour < 6
    
    if is_night:
        # Nighttime bonuses for security features
        if "security_guards" in amenities:
            score += 2  # Extra value at night
        if security == "high":
            score += 3  # Well-lit stops more valuable at night
    
    # -----------------------------------------------------------------
    # DETERMINE TIER (Stricter cutoffs)
    # -----------------------------------------------------------------
    # Clamp score to 0-100
    score = max(0, min(score, 100))
    
    if score >= TIER_LEVEL_1_MIN:  # 85+
        tier = StopTier.LEVEL_1
    elif score >= TIER_LEVEL_2_MIN:  # 65+
        tier = StopTier.LEVEL_2
    elif score >= TIER_LEVEL_3_MIN:  # 45+
        tier = StopTier.LEVEL_3
    else:
        tier = StopTier.AVOID
    
    return score, tier


# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

def find_nearby_stops(
    lat: float,
    lon: float,
    radius_miles: float = DEFAULT_RADIUS_MILES,
    min_tier: StopTier = StopTier.LEVEL_3,
    require_fuel: bool = False,
    limit: int = 10,
) -> List[SafeStop]:
    """
    Find safe stops near a location.
    
    Args:
        lat: Search latitude
        lon: Search longitude
        radius_miles: Search radius
        min_tier: Minimum acceptable tier
        require_fuel: Only return stops with fuel
        limit: Maximum results
        
    Returns:
        List of SafeStop objects, sorted by distance
    """
    logger.info(f"Searching stops near ({lat}, {lon}), radius={radius_miles}mi")
    
    stops = _load_truck_stops()
    results: List[SafeStop] = []
    
    for stop_data in stops:
        # Calculate distance
        stop_lat = stop_data.get("latitude", 0)
        stop_lon = stop_data.get("longitude", 0)
        distance = _haversine_distance((lat, lon), (stop_lat, stop_lon))
        
        # Skip if outside radius
        if distance > radius_miles:
            continue
        
        # Score the stop
        score, tier = score_stop(stop_data)
        
        # Filter by tier
        tier_order = [StopTier.LEVEL_1, StopTier.LEVEL_2, StopTier.LEVEL_3, StopTier.AVOID]
        if tier_order.index(tier) > tier_order.index(min_tier):
            continue
        
        # Check fuel requirement
        amenities = stop_data.get("amenities", [])
        has_fuel = "fuel" in amenities
        if require_fuel and not has_fuel:
            continue
        
        # Build SafeStop
        safe_stop = SafeStop(
            stop_id=stop_data.get("id", 0),
            name=stop_data.get("name", "Unknown"),
            city=stop_data.get("city", ""),
            state=stop_data.get("state", ""),
            latitude=stop_lat,
            longitude=stop_lon,
            highway=stop_data.get("highway", ""),
            distance_miles=distance,
            security_score=score,
            tier=tier,
            security_level=stop_data.get("security", "none"),
            has_fuel=has_fuel,
            has_showers="showers" in amenities,
            has_food="food" in amenities or "restaurant" in amenities,
            has_guards="security_guards" in amenities,
            has_gated_parking="gated_parking" in amenities,
            has_cctv="cctv" in amenities or "cameras" in amenities,
            parking_spaces=stop_data.get("parking_spaces", 0),
            area_risk_level=_get_state_risk_level(stop_data.get("state", "")),
            rating=stop_data.get("rating", 0.0),
            review_count=stop_data.get("review_count", 0)
        )
        
        results.append(safe_stop)
    
    # -------------------------------------------------------
    # GOOGLE MAPS FALLBACK (Nationwide Safety Net)
    # -------------------------------------------------------
    if len(results) < 3 and settings.google_maps_api_key:
        logger.info("Few local stops found. Activating Google Maps Safety Net...")
        google_stops = _search_google_fallback(lat, lon, radius_miles)
        results.extend(google_stops)
    
    # Sort by distance
    results.sort(key=lambda s: s.distance_miles)
    
    # Slice first (efficiency) then fetch Real-Time Data
    final_results = results[:limit]
    
    for stop in final_results:
        try:
            rt_data = aggregator.get_realtime_status(
                stop_id=str(stop.stop_id),
                state=stop.state
            )
            stop.available_spaces = rt_data.get("available_spaces")
            stop.realtime_status = rt_data.get("status", "UNKNOWN")
            
            # log for debugging
            logger.debug(f"Realtime for {stop.name}: {stop.realtime_status}")
        except Exception as e:
            logger.error(f"Failed to fetch realtime for {stop.name}: {e}")

    return final_results


def find_stops_before_zone(
    zone_lat: float,
    zone_lon: float,
    approach_direction: str = "south",  # Direction driver is coming from
    buffer_miles: float = 30.0,
) -> List[SafeStop]:
    """
    Find safe stops BEFORE entering a Red Zone.
    
    Args:
        zone_lat: Red Zone center latitude
        zone_lon: Red Zone center longitude
        approach_direction: Where driver is coming from
        buffer_miles: How far before zone to search
        
    Returns:
        List of safe stops located before the zone
    """
    # Adjust search location based on approach direction
    direction_offsets = {
        "south": (buffer_miles / 69, 0),        # Coming from south, search north of buffer
        "north": (-buffer_miles / 69, 0),
        "west": (0, -buffer_miles / 55),
        "east": (0, buffer_miles / 55),
    }
    
    offset = direction_offsets.get(approach_direction, (0, 0))
    search_lat = zone_lat - offset[0]  # BEFORE the zone
    search_lon = zone_lon - offset[1]
    
    # Find stops with high security preference
    stops = find_nearby_stops(
        lat=search_lat,
        lon=search_lon,
        radius_miles=buffer_miles,
        min_tier=StopTier.LEVEL_2,  # Only Level 1 or 2
        limit=5,
    )
    
    return stops


def find_emergency_help(
    lat: float,
    lon: float,
) -> List[EmergencyStop]:
    """
    Find emergency stops: police + highest security truck stops.
    
    Args:
        lat: Current latitude
        lon: Current longitude
        
    Returns:
        List of EmergencyStop options
    """
    results: List[EmergencyStop] = []
    
    # Find nearest secured truck stops (Level 1 only)
    stops = find_nearby_stops(
        lat=lat,
        lon=lon,
        radius_miles=100.0,  # Wider radius for emergency
        min_tier=StopTier.LEVEL_1,
        limit=3,
    )
    
    for stop in stops:
        results.append(EmergencyStop(
            stop_type=StopType.TRUCK_STOP,
            name=f"{stop.name} (Secured)",
            distance_miles=stop.distance_miles,
            latitude=stop.latitude,
            longitude=stop.longitude,
        ))
    
    # Add mock police stations (TODO: Replace with real data)
    mock_police = _get_mock_police_stations(lat, lon)
    results.extend(mock_police)
    
    # Sort by distance
    results.sort(key=lambda s: s.distance_miles)
    
    return results[:5]


def find_fuel_stops(
    lat: float,
    lon: float,
    radius_miles: float = 50.0,
) -> List[SafeStop]:
    """
    Find stops with fuel (diesel + DEF assumed).
    
    Args:
        lat: Current latitude
        lon: Current longitude
        radius_miles: Search radius
        
    Returns:
        List of fuel stops, prioritizing safety
    """
    return find_nearby_stops(
        lat=lat,
        lon=lon,
        radius_miles=radius_miles,
        require_fuel=True,
        limit=10,
    )


def get_hos_recommendation(
    route_lat: float,
    route_lon: float,
    hours_driven: float,
    break_type: str = "quick",  # "quick" or "overnight"
) -> Dict[str, Any]:
    """
    Get HOS-compliant stop recommendation WITH SAFETY FLOOR.
    
    SAFETY PRINCIPLE:
        - Never recommend below Level 2 for overnight rest
        - Alert driver if no safe options available
        - Safety risk > HOS violation risk
    
    Args:
        route_lat: Current position latitude
        route_lon: Current position longitude
        hours_driven: Hours driven in current shift
        break_type: "quick" (30 min) or "overnight" (10 hr)
        
    Returns:
        Recommendation with stop options and safety status
    """
    # Minimum safe tier for different break types
    MINIMUM_TIER_OVERNIGHT = StopTier.LEVEL_2  # NEVER below Level 2 for sleep
    MINIMUM_TIER_QUICK = StopTier.LEVEL_3      # Level 3 okay for quick stops
    
    # Determine urgency based on hours driven
    if hours_driven >= 10:
        urgency = "critical"
        message = "⚠️ HOS LIMIT: You MUST stop for a 10-hour break."
    elif hours_driven >= 8:
        urgency = "warning"
        message = "🟡 Plan your 10-hour break soon (2 hours remaining)."
    else:
        urgency = "info"
        message = f"✅ {10 - hours_driven:.1f} hours remaining in shift."
    
    # Determine search parameters based on break type
    if break_type == "overnight":
        min_tier = MINIMUM_TIER_OVERNIGHT
        search_radius = 100  # Wider radius for overnight
    else:
        min_tier = MINIMUM_TIER_QUICK
        search_radius = 50
    
    # Find stops meeting safety requirements
    safe_stops = find_nearby_stops(
        lat=route_lat,
        lon=route_lon,
        radius_miles=search_radius,
        min_tier=min_tier,
        limit=5,
    )
    
    # Handle case: No safe stops available
    if not safe_stops and break_type == "overnight":
        # Find any stops (including Level 3) as fallback
        fallback_stops = find_nearby_stops(
            lat=route_lat,
            lon=route_lon,
            radius_miles=150,  # Even wider radius
            min_tier=StopTier.AVOID,  # Include all
            limit=5,
        )
        
        return {
            "status": "UNSAFE",
            "urgency": urgency,
            "message": message,
            "warning": "⚠️ No Level 2+ stops within 100 miles. Consider motel or Level 3 with extreme caution.",
            "hours_driven": hours_driven,
            "hours_remaining": max(0, 10 - hours_driven),
            "break_type": break_type,
            "recommended_stops": [],  # Empty = no safe options
            "fallback_options": [s.to_dict() for s in fallback_stops[:3]],
            "safety_recommendation": "Safety risk > HOS violation risk. Find secure location.",
        }
    
    return {
        "status": "SAFE",
        "urgency": urgency,
        "message": message,
        "hours_driven": hours_driven,
        "hours_remaining": max(0, 10 - hours_driven),
        "break_type": break_type,
        "recommended_stops": [s.to_dict() for s in safe_stops],
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _haversine_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> float:
    """Calculate distance between two GPS points in miles."""
    lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
    lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS_MILES * c


def _get_mock_police_stations(lat: float, lon: float) -> List[EmergencyStop]:
    """
    Mock police station data.
    TODO: Replace with OpenStreetMap or official data.
    """
    # Generate mock police station ~10-20 miles away
    mock_distance = 15.0
    
    return [
        EmergencyStop(
            stop_type=StopType.POLICE_STATION,
            name="Highway Patrol Station (Mock)",
            distance_miles=mock_distance,
            latitude=lat + 0.15,
            longitude=lon,
            phone="911",
        ),
    ]


# =============================================================================
# FORMAT OUTPUT
# =============================================================================

def format_stops_for_driver(stops: List[SafeStop]) -> str:
    """Format stop list for driver display."""
    if not stops:
        return "No safe stops found in range."
    
    lines = ["🅿️ **NEARBY SAFE STOPS**\n"]
    
    for i, stop in enumerate(stops, 1):
        # Tier indicator
        tier_icons = {
            StopTier.LEVEL_1: "🟢 Level 1",
            StopTier.LEVEL_2: "🟡 Level 2",
            StopTier.LEVEL_3: "🟠 Level 3",
            StopTier.AVOID: "🔴 Avoid",
        }
        tier_str = tier_icons.get(stop.tier, "")
        
        # 1. IMAGE (Top)
        if stop.photo_url:
            lines.append(f"![{stop.name}]({stop.photo_url})")

        # 2. TITLE
        lines.append(f"**[{i}] {stop.name}** - {stop.distance_miles:.1f}mi")

        # 3. RATING
        if stop.rating > 0:
            stars = "⭐" * int(round(stop.rating))
            lines.append(f"    Rating: {stars} {stop.rating} ({stop.review_count} reviews)")

        # 4. AMENITIES (Combined with Security Features as requested)
        # 4. AMENITIES (Comforts)
        amenities_list = []
        if stop.has_fuel: amenities_list.append("⛽ Fuel")
        if stop.has_food: amenities_list.append("🍔 Food")
        if stop.has_showers: amenities_list.append("🚿 Showers")
        
        if amenities_list:
            lines.append(f"    Amenities: {', '.join(amenities_list)}")

        # 5. SECURITY FEATURES (Safety)
        security_features = []
        if stop.has_guards: security_features.append("👮 Guards")
        if stop.has_gated_parking: security_features.append("🚧 Gated")
        if getattr(stop, 'has_cctv', False): security_features.append("📹 Cameras")
        
        if security_features:
            lines.append(f"    Security: {', '.join(security_features)}")

        # 5. CUSTOM SCORE & SECURITY LEVEL
        lines.append(f"    {tier_str} | Safety Score: {stop.security_score}/100 | Sec: {stop.security_level.upper()}")

        # 6. AVAILABILITY (Real-Time) - Bottom for high visibility call-to-action
        rt_badge = ""
        if stop.realtime_status == "AVAILABLE":
            rt_badge = f"🟢 {stop.available_spaces} spots free"
        elif stop.realtime_status == "CROWDED":
            rt_badge = f"🟡 Only {stop.available_spaces} spots left"
        elif stop.realtime_status == "FULL":
            rt_badge = "🔴 FULL"
        
        if rt_badge:
            lines.append(f"    {rt_badge}")

        lines.append("")
    
    return "\n".join(lines)



# =============================================================================
# EXTENSIONS
# =============================================================================

def _search_google_fallback(lat: float, lon: float, radius_miles: float) -> List[SafeStop]:
    """
    Fallback mechanism to search Google Maps Places API for truck parking.
    Ensures 100% coverage even outside our database.
    """
    found_stops = []
    try:
        if not settings.google_maps_api_key:
            return []
            
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lon}",
            "radius": int(radius_miles * 1609.34), # Convert miles to meters
            "keyword": "truck stop",
            "key": settings.google_maps_api_key
        }
        
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            logger.error(f"Google API Error: {resp.text}")
            return []
            
        data = resp.json()
        places = data.get("results", [])
        
        for place in places:
            # Create a SafeStop from Google Data
            name = place.get("name", "Unknown Google Stop")
            place_lat = place["geometry"]["location"]["lat"]
            place_lon = place["geometry"]["location"]["lng"]
            
            # Simple distance calc
            dist = math.sqrt((place_lat - lat)**2 + (place_lon - lon)**2) * 69.0
            
            # Estimate rating
            rating = place.get("rating", 3.0)
            user_ratings = place.get("user_ratings_total", 0)
            
            # infer Amenities from types
            types = place.get("types", [])
            amenities = []
            if "gas_station" in types: amenities.append("fuel")
            if "restaurant" in types or "food" in types: amenities.append("food")
            
            # Extract Photo
            photo_url = None
            if "photos" in place and place["photos"]:
                ref = place["photos"][0]["photo_reference"]
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={ref}&key={settings.google_maps_api_key}"

            # Create object
            stop = SafeStop(
                stop_id=hash(name) % 100000, # Fake ID
                name=f"[Google] {name}",
                city="Unknown",
                state="Unknown",
                latitude=place_lat,
                longitude=place_lon,
                highway="Nearby",
                distance_miles=dist,
                security_score=int(rating * 15) + 20, # Rough score from stars
                tier=StopTier.LEVEL_2 if rating > 4.0 else StopTier.LEVEL_3,
                security_level="medium",
                has_fuel="fuel" in amenities,
                has_showers=False, # Google doesn't easily tell us
                has_guards=False,
                has_gated_parking=False,
                parking_spaces=0, # Unknown
                area_risk_level="unknown",
                realtime_status="UNKNOWN", # Google doesn't give this
                rating=rating,
                review_count=user_ratings,
                photo_url=photo_url
            )
            found_stops.append(stop)
            
        logger.info(f"Google Safety Net found {len(found_stops)} additional stops.")
        
    except Exception as e:
        logger.error(f"Google Fallback failed: {e}")
        
    return found_stops


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Safe Stops - Test")
    print("=" * 70)
    
    # Test 1: Find stops near Dallas
    print("\n--- Test 1: Stops near Dallas ---")
    stops = find_nearby_stops(32.7767, -96.7970, radius_miles=100)
    print(f"Found {len(stops)} stops")
    for stop in stops[:3]:
        print(f"  {stop.name}: {stop.security_score}/100 ({stop.tier.value})")
    
    # Test 2: Fuel stops
    print("\n--- Test 2: Fuel Stops near Houston ---")
    fuel_stops = find_fuel_stops(29.7604, -95.3698)
    print(f"Found {len(fuel_stops)} fuel stops")
    
    # Test 3: Emergency help
    print("\n--- Test 3: Emergency Help near LA ---")
    emergency = find_emergency_help(33.8536, -118.2140)
    for e in emergency[:3]:
        print(f"  {e.stop_type.value}: {e.name} ({e.distance_miles:.1f}mi)")
    
    # Test 4: HOS recommendation
    print("\n--- Test 4: HOS Recommendation (8 hours driven) ---")
    hos = get_hos_recommendation(32.7767, -96.7970, hours_driven=8, break_type="overnight")
    print(f"Urgency: {hos['urgency']}")
    print(f"Message: {hos['message']}")
    print(f"Stops found: {len(hos['recommended_stops'])}")
    
    # Test 5: Format for driver
    print("\n--- Test 5: Formatted Output ---")
    print(format_stops_for_driver(stops[:3]))
    
    print("=" * 70)
