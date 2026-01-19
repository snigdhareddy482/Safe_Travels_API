"""
SafeTravels Agents - Analyst
=============================

The Analyst agent examines route options and provides detailed,
explainable risk assessments with cited sources.

RESPONSIBILITIES:
    1. Select best route from options (based on risk)
    2. Explain WHY using reasoning chain
    3. Cite specific sources for each claim
    4. List risk factors and recommendations
    5. Provide confidence score

OUTPUT:
    AnalysisResult with full explanation and citations

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from safetravels.agents.state import (
    AgentState,
    AnalysisResult,
    add_reasoning_step,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Confidence adjustments
BASE_CONFIDENCE: float = 0.7
SOURCE_BOOST: float = 0.05    # +5% per source
RED_ZONE_PENALTY: float = 0.1 # -10% per red zone


# =============================================================================
# MAIN ANALYST FUNCTION
# =============================================================================

def analyze_routes(state: AgentState) -> AgentState:
    """
    Analyze route options and provide explainable recommendation.
    
    This is a LangGraph node that:
        1. Reviews route_options from planner
        2. Selects the safest/recommended route
        3. Builds reasoning chain with citations
        4. Returns analysis result
    
    Args:
        state: Current agent state with route_options
        
    Returns:
        Updated state with analysis populated
    """
    logger.info("--- ANALYST: Analyzing route options ---")
    
    route_options = state.get("route_options", [])
    trip_request = state.get("trip_request", {})
    documents = state.get("documents", [])
    
    if not route_options:
        state["analysis"] = None
        state["warnings"].append("No routes to analyze")
        return state
    
    add_reasoning_step(state, "Beginning route analysis")
    
    # Select the recommended route (already sorted by planner)
    recommended = next(
        (r for r in route_options if r.get("is_recommended")),
        route_options[0]
    )
    
    selected_id = recommended["route_id"]
    add_reasoning_step(state, f"Selected {selected_id} as recommended route")
    
    # Build claims with sources
    claims = _build_claims(recommended, trip_request, documents)
    
    # Identify risk factors
    risk_factors = _identify_risk_factors(recommended, trip_request)
    
    # Generate recommendations
    recommendations = _generate_recommendations(recommended, trip_request)
    
    # Build full reasoning
    reasoning = _build_reasoning(recommended, claims, risk_factors)
    
    # Calculate confidence
    confidence = _calculate_confidence(
        route=recommended,
        claims=claims,
        sources=documents,
    )
    
    # Create analysis result
    analysis = AnalysisResult(
        selected_route_id=selected_id,
        reasoning=reasoning,
        claims=claims,
        risk_factors=risk_factors,
        recommendations=recommendations,
        confidence=confidence,
    )
    
    state["analysis"] = analysis.to_dict()
    state["selected_route"] = selected_id
    add_reasoning_step(state, f"Analysis complete. Confidence: {confidence:.0%}")
    
    logger.info(f"Analyst selected {selected_id} with {confidence:.0%} confidence")
    return state


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_claims(
    route: Dict[str, Any],
    trip: Dict[str, Any],
    documents: List[str],
) -> List[Dict[str, str]]:
    """
    Build a list of claims with their sources.
    
    Each claim is a statement the analyst makes, linked to evidence.
    This enables the Critic to verify claims aren't hallucinated.
    """
    claims = []
    
    # Claim 1: Risk score
    claims.append({
        "claim": f"Route has a risk score of {route['risk_score']}/10 ({route['risk_level']})",
        "source": "SafeTravels Route Scanner (15-factor weighted formula)",
        "verifiable": True,
    })
    
    # Claim 2: Red zones
    if route.get("red_zone_count", 0) > 0:
        claims.append({
            "claim": f"Route contains {route['red_zone_count']} high-risk zone(s)",
            "source": "Route Scanner Red Zone Detection",
            "verifiable": True,
        })
    else:
        claims.append({
            "claim": "Route contains no high-risk zones",
            "source": "Route Scanner Red Zone Detection",
            "verifiable": True,
        })
    
    # Claim 3: Hotspot avoidance
    if route.get("avoids_hotspots"):
        claims.append({
            "claim": "Route successfully avoids known theft hotspots",
            "source": "Planner Hotspot Database",
            "verifiable": True,
        })
    else:
        claims.append({
            "claim": "Route passes through known theft hotspots",
            "source": "Planner Hotspot Database",
            "verifiable": True,
        })
    
    # Claim 4: Commodity risk (from trip request)
    commodity = trip.get("commodity", "general")
    if commodity in ["electronics", "pharmaceuticals"]:
        claims.append({
            "claim": f"Cargo type ({commodity}) is a high-value theft target",
            "source": "CargoNet Theft Statistics",
            "verifiable": True,
        })
    
    # Claim 5: Use any retrieved documents
    for i, doc in enumerate(documents[:2]):  # First 2 docs
        doc_preview = doc[:100] if len(doc) > 100 else doc
        claims.append({
            "claim": f"Supporting evidence from retrieved data",
            "source": f"Retrieved Document #{i+1}",
            "verifiable": True,
        })
    
    return claims


def _identify_risk_factors(
    route: Dict[str, Any],
    trip: Dict[str, Any],
) -> List[str]:
    """
    Identify key risk factors for this route.
    """
    factors = []
    
    # Risk level
    if route["risk_score"] >= 7:
        factors.append(f"🔴 Critical risk level: {route['risk_score']}/10")
    elif route["risk_score"] >= 5:
        factors.append(f"🟡 Elevated risk level: {route['risk_score']}/10")
    
    # Red zones
    if route.get("red_zone_count", 0) > 0:
        factors.append(f"⚠️ {route['red_zone_count']} Red Zone(s) on route")
    
    # Hotspots
    if not route.get("avoids_hotspots", True):
        factors.append("📍 Route passes through theft hotspots")
    
    # Distance (long haul = more exposure)
    if route.get("total_miles", 0) > 1000:
        factors.append(f"📏 Long haul ({route['total_miles']:.0f}mi) = extended exposure")
    
    # Commodity
    commodity = trip.get("commodity", "general")
    if commodity in ["electronics", "pharmaceuticals"]:
        factors.append(f"📦 High-value cargo: {commodity}")
    
    # Cargo value
    value = trip.get("cargo_value", 0)
    if value >= 500000:
        factors.append(f"💰 Very high cargo value: ${value:,.0f}")
    elif value >= 100000:
        factors.append(f"💵 High cargo value: ${value:,.0f}")
    
    return factors


def _generate_recommendations(
    route: Dict[str, Any],
    trip: Dict[str, Any],
) -> List[str]:
    """
    Generate actionable recommendations based on analysis.
    """
    recommendations = []
    
    # Based on risk level
    if route["risk_score"] >= 7:
        recommendations.append(
            "⚠️ Consider additional security measures for this route"
        )
        recommendations.append(
            "🕐 Plan to drive through high-risk segments during daylight"
        )
    
    # Based on red zones
    if route.get("red_zone_count", 0) > 0:
        recommendations.append(
            "🚫 Do NOT stop in Red Zones - proceed through quickly"
        )
        recommendations.append(
            "🅿️ Plan rest stops BEFORE entering Red Zones"
        )
    
    # Based on cargo
    commodity = trip.get("commodity", "general")
    value = trip.get("cargo_value", 0)
    
    if commodity in ["electronics", "pharmaceuticals"] or value >= 250000:
        recommendations.append(
            "🔒 Use secured truck stops only (fenced, guards, CCTV)"
        )
        recommendations.append(
            "📡 Keep tracking active and check in with dispatch regularly"
        )
    
    # General
    recommendations.append(
        "✅ Report any suspicious activity immediately"
    )
    
    return recommendations


def _build_reasoning(
    route: Dict[str, Any],
    claims: List[Dict[str, str]],
    risk_factors: List[str],
) -> str:
    """
    Build a full reasoning paragraph explaining the recommendation.
    """
    lines = []
    
    lines.append(f"**Analysis Summary for {route['name']}**")
    lines.append("")
    
    # Opening
    lines.append(
        f"Based on comprehensive analysis using our 15-factor risk model, "
        f"this route scores **{route['risk_score']}/10** ({route['risk_level']} risk)."
    )
    lines.append("")
    
    # Key findings
    lines.append("**Key Findings:**")
    for factor in risk_factors[:3]:  # Top 3
        lines.append(f"- {factor}")
    lines.append("")
    
    # Citations
    lines.append("**Evidence:**")
    for claim in claims[:3]:  # Top 3
        lines.append(f"- {claim['claim']} (Source: {claim['source']})")
    lines.append("")
    
    # Conclusion
    if route.get("is_recommended"):
        lines.append(
            "✅ This route is **RECOMMENDED** as the safest option "
            "among alternatives analyzed."
        )
    else:
        lines.append(
            "⚠️ This route is NOT recommended. Please review alternatives."
        )
    
    return "\n".join(lines)


def _calculate_confidence(
    route: Dict[str, Any],
    claims: List[Dict[str, str]],
    sources: List[str],
) -> float:
    """
    Calculate analyst confidence based on evidence quality.
    """
    confidence = BASE_CONFIDENCE
    
    # Boost for each verified claim
    verifiable_claims = sum(1 for c in claims if c.get("verifiable"))
    confidence += verifiable_claims * 0.02  # +2% per claim
    
    # Boost for sources
    confidence += min(len(sources), 5) * SOURCE_BOOST
    
    # Penalty for red zones (less certainty in dangerous areas)
    red_zones = route.get("red_zone_count", 0)
    confidence -= red_zones * RED_ZONE_PENALTY
    
    # Clamp
    return max(0.5, min(confidence, 0.95))


# =============================================================================
# FORMAT OUTPUT
# =============================================================================

def format_analysis_for_driver(analysis: Dict[str, Any]) -> str:
    """
    Format analysis as readable text for driver.
    """
    if not analysis:
        return "No analysis available."
    
    lines = [
        "📊 **ROUTE ANALYSIS**",
        "",
        analysis["reasoning"],
        "",
        "**Recommendations:**",
    ]
    
    for rec in analysis["recommendations"][:5]:
        lines.append(f"  {rec}")
    
    lines.append("")
    lines.append(f"**Confidence:** {analysis['confidence']:.0%}")
    
    return "\n".join(lines)


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    from safetravels.agents.state import create_initial_state, TripRequest
    from safetravels.agents.planner import plan_routes
    
    print("=" * 70)
    print("SafeTravels Analyst - Test")
    print("=" * 70)
    
    # Create test trip
    trip = TripRequest(
        origin_lat=32.7767,
        origin_lon=-96.7970,
        destination_lat=41.8781,
        destination_lon=-87.6298,
        commodity="electronics",
        cargo_value=250000,
    )
    
    state = create_initial_state(
        query="Analyze route options for Dallas to Chicago",
        trip_request=trip,
    )
    
    # Run planner first
    state = plan_routes(state)
    
    # Run analyst
    state = analyze_routes(state)
    
    # Display results
    print("\n" + format_analysis_for_driver(state.get("analysis")))
    
    print("\n--- Claims Made ---")
    for claim in state["analysis"]["claims"]:
        print(f"  • {claim['claim']}")
        print(f"    Source: {claim['source']}")
    
    print("\n" + "=" * 70)
    print("✅ Analyst test complete!")
    print("=" * 70)
