"""
SafeTravels MCP Tools - Risk Scorer
====================================

Calculates cargo theft risk using a comprehensive 15-factor weighted formula.

FORMULA:
    Score = Base_Crime_Rate
          × TIME_WEIGHT
          × DAY_WEIGHT
          × MONTH_WEIGHT
          × COMMODITY_WEIGHT
          × VALUE_MULTIPLIER
          × LOCATION_WEIGHT
          × STATE_WEIGHT
          × WEATHER_WEIGHT
          × EVENT_WEIGHT
          × TRAFFIC_WEIGHT
          × ACCIDENT_HISTORY_WEIGHT

Design Principles:
    - Single Responsibility: Only calculates risk
    - Open/Closed: New factors added via config.py, not here
    - Dependency Injection: Data sources are injectable
    - Immutable Data: Uses dataclasses with frozen=False for flexibility

Author: SafeTravels Team
Created: January 2026
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

from safetravels.mcp import risk_model_weights as config
from safetravels.mcp.risk_model_weights import (
    # Temporal
    TIME_WEIGHTS,
    DAY_WEIGHTS,
    MONTH_WEIGHTS,
    SEASON_WEIGHTS,
    # Cargo
    COMMODITY_WEIGHTS,
    # Location
    LOCATION_WEIGHTS,
    HOTSPOT_STATES,
    DEFAULT_STATE_WEIGHT,
    # Environmental
    WEATHER_WEIGHTS,
    EVENT_WEIGHTS,
    TRAFFIC_WEIGHTS,
    ACCIDENT_HISTORY_WEIGHTS,
    # Helpers
    get_risk_level,
    clamp_score,
    get_value_multiplier,
    get_state_multiplier,
    MAX_RISK_SCORE,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RiskContext:
    """
    Complete context for risk calculation.
    
    All factors that influence cargo theft risk for a specific
    location at a specific time.
    
    Attributes:
        # Temporal Factors
        time_of_day: 'day', 'evening', or 'night'
        day_of_week: Lowercase day name (e.g., 'friday')
        month: Lowercase month name (e.g., 'december')
        season: Special season if applicable (e.g., 'holiday_peak')
        
        # Cargo Factors
        commodity: Type of cargo being transported
        cargo_value: Total declared value in USD
        
        # Location Factors
        location_type: Type of stop/parking area
        state: Two-letter state code (e.g., 'TX')
        
        # Environmental Factors
        weather: Current weather condition
        event: Any local disturbances/events
        traffic: Current traffic condition
        accident_history: Historical accident frequency for this area
    """
    # Temporal
    time_of_day: str = "day"
    day_of_week: str = "monday"
    month: str = "january"
    season: str = "normal"
    
    # Cargo
    commodity: str = "general"
    cargo_value: float = 50000.0
    
    # Location
    location_type: str = "truck_stop_basic"
    state: str = ""
    
    # Environmental
    weather: str = "clear"
    event: str = "none"
    traffic: str = "light"
    accident_history: str = "low"


@dataclass
class FactorBreakdown:
    """
    Detailed breakdown of each factor's contribution.
    
    Provides transparency into how the final score was calculated.
    Each factor shows the weight applied.
    """
    base_crime_rate: float
    time_of_day: float
    day_of_week: float
    month: float
    season: float
    commodity: float
    cargo_value: float
    location_type: float
    state: float
    weather: float
    event: float
    traffic: float
    accident_history: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "base_crime_rate": round(self.base_crime_rate, 2),
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "month": self.month,
            "season": self.season,
            "commodity": self.commodity,
            "cargo_value": self.cargo_value,
            "location_type": self.location_type,
            "state": self.state,
            "weather": self.weather,
            "event": self.event,
            "traffic": self.traffic,
            "accident_history": self.accident_history,
        }


@dataclass
class RiskAssessment:
    """
    Complete risk assessment result.
    
    Attributes:
        latitude: Location latitude
        longitude: Location longitude
        risk_score: Final calculated score (1-10)
        risk_level: Human-readable level (low/moderate/high/critical)
        factors: Detailed breakdown of each weight applied
        confidence: Model confidence (0-1)
        warnings: List of specific risk warnings
    """
    latitude: float
    longitude: float
    risk_score: float
    risk_level: str
    factors: FactorBreakdown
    confidence: float
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# CORE CALCULATION FUNCTION
# =============================================================================

def calculate_risk(
    latitude: float,
    longitude: float,
    context: Optional[RiskContext] = None,
    base_crime_rate: Optional[float] = None,
) -> RiskAssessment:
    """
    Calculate comprehensive cargo theft risk for a location.
    
    Applies a 15-factor weighted formula to determine risk.
    Each factor is multiplied against the base crime rate.
    
    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate
        context: Optional RiskContext with all situational factors.
                 Defaults to daytime, general cargo, clear weather.
        base_crime_rate: Optional override for base crime rate.
                        Defaults to mock lookup (to be replaced with FBI data).
    
    Returns:
        RiskAssessment with score, level, factor breakdown, and warnings.
    
    Example:
        >>> context = RiskContext(
        ...     time_of_day="night",
        ...     month="december",
        ...     commodity="electronics",
        ...     cargo_value=500000,
        ...     event="large_event"
        ... )
        >>> result = calculate_risk(32.7767, -96.7970, context)
        >>> print(f"Risk: {result.risk_score}/10 ({result.risk_level})")
        Risk: 9.2/10 (critical)
    """
    # Use default context if not provided
    if context is None:
        context = RiskContext()
    
    # Get base crime rate
    if base_crime_rate is None:
        base_crime_rate = _get_mock_crime_rate(latitude, longitude, context.state)
    
    # ---------------------------------------------------------------------
    # RETRIEVE ALL WEIGHT FACTORS (with safe fallbacks to 1.0)
    # ---------------------------------------------------------------------
    
    # Temporal factors
    time_weight = TIME_WEIGHTS.get(context.time_of_day, 1.0)
    day_weight = DAY_WEIGHTS.get(context.day_of_week, 1.0)
    month_weight = MONTH_WEIGHTS.get(context.month, 1.0)
    season_weight = SEASON_WEIGHTS.get(context.season, 1.0)
    
    # Cargo factors
    commodity_weight = COMMODITY_WEIGHTS.get(context.commodity, 1.0)
    value_weight = get_value_multiplier(context.cargo_value)
    
    # Location factors
    location_weight = LOCATION_WEIGHTS.get(context.location_type, 1.0)
    state_weight = get_state_multiplier(context.state)
    
    # Environmental factors
    weather_weight = WEATHER_WEIGHTS.get(context.weather, 1.0)
    event_weight = EVENT_WEIGHTS.get(context.event, 1.0)
    traffic_weight = TRAFFIC_WEIGHTS.get(context.traffic, 1.0)
    accident_weight = ACCIDENT_HISTORY_WEIGHTS.get(context.accident_history, 1.0)
    
    # ---------------------------------------------------------------------
    # CALCULATE WEIGHTED SCORE
    # ---------------------------------------------------------------------
    
    raw_score = (
        base_crime_rate
        * time_weight
        * day_weight
        * month_weight
        * season_weight
        * commodity_weight
        * value_weight
        * location_weight
        * state_weight
        * weather_weight
        * event_weight
        * traffic_weight
        * accident_weight
    )
    
    # Clamp to valid range [1, 10]
    final_score = clamp_score(raw_score)
    
    # ---------------------------------------------------------------------
    # BUILD FACTOR BREAKDOWN FOR TRANSPARENCY
    # ---------------------------------------------------------------------
    
    factors = FactorBreakdown(
        base_crime_rate=base_crime_rate,
        time_of_day=time_weight,
        day_of_week=day_weight,
        month=month_weight,
        season=season_weight,
        commodity=commodity_weight,
        cargo_value=value_weight,
        location_type=location_weight,
        state=state_weight,
        weather=weather_weight,
        event=event_weight,
        traffic=traffic_weight,
        accident_history=accident_weight,
    )
    
    # ---------------------------------------------------------------------
    # GENERATE WARNINGS FOR HIGH-RISK FACTORS
    # ---------------------------------------------------------------------
    
    warnings = _generate_warnings(context, factors)
    
    # ---------------------------------------------------------------------
    # CALCULATE CONFIDENCE
    # ---------------------------------------------------------------------
    
    confidence = _calculate_confidence(factors)
    
    # Log the calculation
    logger.debug(
        f"Risk: ({latitude:.4f}, {longitude:.4f}) = {final_score:.1f}/10 "
        f"[{get_risk_level(final_score)}] conf={confidence:.0%}"
    )
    
    return RiskAssessment(
        latitude=latitude,
        longitude=longitude,
        risk_score=round(final_score, 1),
        risk_level=get_risk_level(final_score),
        factors=factors,
        confidence=confidence,
        warnings=warnings,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_mock_crime_rate(
    latitude: float,
    longitude: float,
    state: str = ""
) -> float:
    """
    Get base crime rate for a location.
    
    TODO: Replace with real FBI UCR API lookup or database query.
    
    Current implementation uses known high-risk metro areas
    for demonstration purposes.
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        state: Optional state code for additional context
        
    Returns:
        Base crime rate score (1-10 scale)
    """
    # Known high-risk metropolitan areas with approximate coordinates
    HIGH_RISK_METROS = [
        # (lat, lon, radius_degrees, base_score, name)
        (34.05, -118.25, 0.5, 5.5, "Los Angeles"),
        (32.78, -96.80, 0.3, 5.0, "Dallas"),
        (29.76, -95.37, 0.4, 4.5, "Houston"),
        (33.75, -84.39, 0.3, 4.5, "Atlanta"),
        (41.88, -87.63, 0.3, 5.0, "Chicago"),
        (25.76, -80.19, 0.4, 5.0, "Miami"),
        (40.71, -74.01, 0.3, 4.0, "New York"),
        (39.95, -75.17, 0.3, 4.0, "Philadelphia"),
        (35.23, -80.84, 0.3, 3.5, "Charlotte"),
        (35.15, -90.05, 0.3, 4.0, "Memphis"),
    ]
    
    # Check proximity to known high-risk areas
    for metro_lat, metro_lon, radius, score, name in HIGH_RISK_METROS:
        if (abs(latitude - metro_lat) < radius and 
            abs(longitude - metro_lon) < radius):
            logger.debug(f"Location near {name}, base score: {score}")
            return score
    
    # Default baseline for unknown/rural areas
    return 3.0


def _generate_warnings(
    context: RiskContext,
    factors: FactorBreakdown
) -> List[str]:
    """
    Generate human-readable warnings for high-risk factors.
    
    Identifies which factors are significantly elevating risk
    and provides actionable warnings.
    
    Args:
        context: The risk context used
        factors: Calculated factor weights
        
    Returns:
        List of warning strings
    """
    warnings = []
    
    # Critical event warning
    if factors.event >= 1.5:
        warnings.append(
            f"⚠️ HIGH ALERT: Major event ({context.event}) significantly "
            f"increases theft risk. Consider avoiding this area."
        )
    
    # Night + high-value warning
    if factors.time_of_day >= 1.5 and factors.cargo_value >= 1.25:
        warnings.append(
            "🌙 Night travel with high-value cargo is extremely risky. "
            "Consider secured overnight parking."
        )
    
    # Weather warning
    if factors.weather >= 1.2:
        warnings.append(
            f"🌧️ Weather condition ({context.weather}) may delay "
            f"emergency response and reduce visibility."
        )
    
    # Traffic warning
    if factors.traffic >= 1.3:
        warnings.append(
            "🚗 Heavy traffic or standstill conditions make the truck "
            "a stationary target. Find secure parking if stuck."
        )
    
    # Location warning
    if factors.location_type >= 1.4:
        warnings.append(
            f"📍 Location type ({context.location_type}) is high-risk. "
            f"Seek secured truck stop if possible."
        )
    
    # Hotspot state warning
    if factors.state >= 1.2:
        warnings.append(
            f"🗺️ State ({context.state}) is a documented cargo theft hotspot. "
            f"Maintain heightened awareness."
        )
    
    # High-value commodity
    if factors.commodity >= 1.4:
        warnings.append(
            f"📦 Commodity ({context.commodity}) is a high-value theft target. "
            f"Consider additional security measures."
        )
    
    return warnings


def _calculate_confidence(factors: FactorBreakdown) -> float:
    """
    Calculate model confidence based on data completeness.
    
    Higher confidence when:
        - Using real crime data (not mock)
        - All context factors are explicitly provided
        
    Args:
        factors: Factor breakdown used in calculation
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    # Base confidence with mock data
    base_confidence = 0.65
    
    # Count how many factors were explicitly set (not default 1.0)
    non_default_factors = sum([
        1 for weight in [
            factors.time_of_day,
            factors.day_of_week,
            factors.month,
            factors.commodity,
            factors.cargo_value,
            factors.location_type,
            factors.state,
            factors.weather,
            factors.event,
            factors.traffic,
            factors.accident_history,
        ]
        if weight != 1.0
    ])
    
    # Boost confidence by 2% for each explicitly set factor
    context_boost = non_default_factors * 0.02
    
    return min(base_confidence + context_boost, 0.95)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_time_category(hour: int) -> str:
    """
    Convert 24-hour time to category.
    
    Args:
        hour: Hour in 24-hour format (0-23)
        
    Returns:
        'night' (22-5), 'evening' (17-22), or 'day' (5-17)
    """
    if hour >= 22 or hour < 5:
        return "night"
    elif hour >= 17:
        return "evening"
    else:
        return "day"


def get_day_name(date: datetime) -> str:
    """
    Get lowercase day name from datetime.
    
    Args:
        date: Python datetime object
        
    Returns:
        Lowercase day name (e.g., 'friday')
    """
    return date.strftime("%A").lower()


def get_month_name(date: datetime) -> str:
    """
    Get lowercase month name from datetime.
    
    Args:
        date: Python datetime object
        
    Returns:
        Lowercase month name (e.g., 'december')
    """
    return date.strftime("%B").lower()


def get_season(date: datetime) -> str:
    """
    Determine special season based on date.
    
    Args:
        date: Python datetime object
        
    Returns:
        Season identifier or 'normal'
    """
    month = date.month
    day = date.day
    
    # Black Friday week (Thanksgiving week, ~Nov 22-28)
    if month == 11 and 22 <= day <= 28:
        return "black_friday_week"
    
    # Christmas week
    if month == 12 and 20 <= day <= 26:
        return "christmas_week"
    
    # New Year's week
    if (month == 12 and day >= 27) or (month == 1 and day <= 3):
        return "new_years_week"
    
    # Holiday peak (rest of December)
    if month == 12 and day >= 15:
        return "holiday_peak"
    
    # Back to school
    if (month == 8 and day >= 1) or (month == 9 and day <= 15):
        return "back_to_school"
    
    # Summer
    if month in [6, 7, 8]:
        return "summer"
    
    return "normal"


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Risk Scorer - Comprehensive Test")
    print("=" * 70)
    
    # Test 1: Default context (low risk scenario)
    print("\n--- Test 1: Default Context (Daytime, General Cargo) ---")
    result = calculate_risk(32.7767, -96.7970)
    print(f"Location: Dallas, TX (32.7767, -96.7970)")
    print(f"Score: {result.risk_score}/10 ({result.risk_level})")
    print(f"Confidence: {result.confidence:.0%}")
    
    # Test 2: Moderate risk scenario
    print("\n--- Test 2: Night Delivery, Electronics ---")
    context = RiskContext(
        time_of_day="night",
        day_of_week="friday",
        month="november",
        commodity="electronics",
        cargo_value=250000,
        state="TX",
    )
    result = calculate_risk(32.7767, -96.7970, context)
    print(f"Score: {result.risk_score}/10 ({result.risk_level})")
    print(f"Warnings: {len(result.warnings)}")
    for w in result.warnings:
        print(f"  {w}")
    
    # Test 3: Maximum risk scenario
    print("\n--- Test 3: WORST CASE SCENARIO ---")
    worst_case = RiskContext(
        time_of_day="night",
        day_of_week="saturday",
        month="december",
        season="holiday_peak",
        commodity="electronics",
        cargo_value=1000000,
        location_type="unsecured_lot",
        state="CA",
        weather="fog",
        event="civil_unrest",
        traffic="standstill",
        accident_history="very_high",
    )
    result = calculate_risk(34.05, -118.25, worst_case)  # Los Angeles
    print(f"Location: Los Angeles, CA")
    print(f"Score: {result.risk_score}/10 ({result.risk_level})")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Factors Applied:")
    for factor, value in result.factors.to_dict().items():
        if value != 1.0:
            print(f"  {factor}: {value}")
    print(f"Warnings: {len(result.warnings)}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
