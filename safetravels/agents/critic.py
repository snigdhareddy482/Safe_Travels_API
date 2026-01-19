"""
SafeTravels Agents - Critic
=============================

The Critic agent verifies the Analyst's work, checking for:
    - Citation accuracy (claims have valid sources)
    - Logic consistency (scores match calculations)
    - Confidence appropriateness

RESPONSIBILITIES:
    1. Verify each claim has a source
    2. Check if risk scores match tool outputs
    3. Identify any hallucinations or inconsistencies
    4. Approve or request revision
    5. Assign final confidence score

OUTPUT:
    CriticReview with verdict (APPROVED / NEEDS_REVISION)

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional
import logging

from safetravels.agents.state import (
    AgentState,
    CriticReview,
    CriticVerdict,
    add_reasoning_step,
    increment_revision,
    should_stop_revising,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Maximum revision attempts before forcing approval
MAX_REVISIONS: int = 3

# Minimum claims needed for valid analysis
MIN_CLAIMS: int = 2

# Minimum confidence for approval
MIN_CONFIDENCE: float = 0.6


# =============================================================================
# MAIN CRITIC FUNCTION
# =============================================================================

def review_analysis(state: AgentState) -> AgentState:
    """
    Review the Analyst's work and verify accuracy.
    
    This is a LangGraph node that:
        1. Checks citation validity
        2. Verifies logic consistency
        3. Returns verdict (APPROVED or NEEDS_REVISION)
    
    Args:
        state: Current agent state with analysis
        
    Returns:
        Updated state with critic_review populated
    """
    logger.info("--- CRITIC: Reviewing analysis ---")
    
    analysis = state.get("analysis")
    route_options = state.get("route_options", [])
    
    if not analysis:
        state["critic_review"] = CriticReview(
            verdict=CriticVerdict.REJECTED,
            citation_check=False,
            logic_check=False,
            confidence_score=0.0,
            issues=["No analysis provided"],
            feedback="Analyst must provide analysis before review.",
        ).to_dict()
        return state
    
    add_reasoning_step(state, "Beginning critical review of analysis")
    
    issues: List[str] = []
    
    # -----------------------------------------------------------------
    # CHECK 1: Citation Verification
    # -----------------------------------------------------------------
    citation_check, citation_issues = _verify_citations(analysis)
    issues.extend(citation_issues)
    add_reasoning_step(state, f"Citation check: {'PASS' if citation_check else 'FAIL'}")
    
    # -----------------------------------------------------------------
    # CHECK 2: Logic Consistency
    # -----------------------------------------------------------------
    logic_check, logic_issues = _verify_logic(analysis, route_options)
    issues.extend(logic_issues)
    add_reasoning_step(state, f"Logic check: {'PASS' if logic_check else 'FAIL'}")
    
    # -----------------------------------------------------------------
    # CHECK 3: Confidence Validation
    # -----------------------------------------------------------------
    confidence_valid = analysis.get("confidence", 0) >= MIN_CONFIDENCE
    if not confidence_valid:
        issues.append(f"Confidence too low: {analysis.get('confidence', 0):.0%}")
    
    # -----------------------------------------------------------------
    # DETERMINE VERDICT
    # -----------------------------------------------------------------
    all_checks_pass = citation_check and logic_check and confidence_valid
    
    if all_checks_pass:
        verdict = CriticVerdict.APPROVED
        feedback = "Analysis verified. All claims are supported by sources."
    elif should_stop_revising(state, MAX_REVISIONS):
        verdict = CriticVerdict.APPROVED  # Force approve after max retries
        feedback = f"Approved after {MAX_REVISIONS} revision attempts."
        issues.append("Forced approval due to revision limit")
    else:
        verdict = CriticVerdict.NEEDS_REVISION
        feedback = _generate_revision_feedback(issues)
        state = increment_revision(state)
    
    # Calculate critic's own confidence
    critic_confidence = _calculate_critic_confidence(
        citation_check, logic_check, len(issues)
    )
    
    # Create review
    review = CriticReview(
        verdict=verdict,
        citation_check=citation_check,
        logic_check=logic_check,
        confidence_score=critic_confidence,
        issues=issues,
        feedback=feedback,
    )
    
    state["critic_review"] = review.to_dict()
    add_reasoning_step(state, f"Verdict: {verdict.value}")
    
    logger.info(f"Critic verdict: {verdict.value}, issues: {len(issues)}")
    return state


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def _verify_citations(analysis: Dict[str, Any]) -> tuple:
    """
    Verify that all claims have valid sources.
    
    Returns:
        (passed: bool, issues: List[str])
    """
    issues = []
    claims = analysis.get("claims", [])
    
    if len(claims) < MIN_CLAIMS:
        issues.append(f"Insufficient claims: {len(claims)} < {MIN_CLAIMS} required")
        return False, issues
    
    for i, claim in enumerate(claims):
        # Check claim has text
        if not claim.get("claim"):
            issues.append(f"Claim #{i+1} is empty")
            continue
        
        # Check claim has source
        if not claim.get("source"):
            issues.append(f"Claim #{i+1} lacks source: '{claim.get('claim', '')[:50]}...'")
        
        # Check source isn't generic
        source = claim.get("source", "")
        if source.lower() in ["unknown", "none", "n/a", ""]:
            issues.append(f"Claim #{i+1} has invalid source: '{source}'")
    
    # Pass if at least 80% of claims have valid sources
    valid_claims = len(claims) - len(issues)
    passed = (valid_claims / max(len(claims), 1)) >= 0.8
    
    return passed, issues


def _verify_logic(
    analysis: Dict[str, Any],
    route_options: List[Dict[str, Any]],
) -> tuple:
    """
    Verify that analysis logic is consistent with data.
    
    Returns:
        (passed: bool, issues: List[str])
    """
    issues = []
    
    selected_id = analysis.get("selected_route_id")
    if not selected_id:
        issues.append("No route selected in analysis")
        return False, issues
    
    # Find selected route
    selected_route = next(
        (r for r in route_options if r.get("route_id") == selected_id),
        None
    )
    
    if not selected_route:
        issues.append(f"Selected route '{selected_id}' not found in options")
        return False, issues
    
    # Check if selected route is actually the recommended one
    if not selected_route.get("is_recommended"):
        # This might be intentional, but flag it
        safer_routes = [r for r in route_options if r["risk_score"] < selected_route["risk_score"]]
        if safer_routes:
            issues.append(
                f"Selected route is not the safest. "
                f"{len(safer_routes)} route(s) have lower risk."
            )
    
    # Verify risk factors match actual data
    risk_factors = analysis.get("risk_factors", [])
    actual_risk = selected_route.get("risk_score", 0)
    
    # Check if risk level in factors matches reality
    has_critical_factor = any("critical" in f.lower() for f in risk_factors)
    is_critical = actual_risk >= 7
    
    if is_critical and not has_critical_factor:
        issues.append("Analysis doesn't highlight critical risk level")
    
    passed = len(issues) == 0
    return passed, issues


def _calculate_critic_confidence(
    citation_check: bool,
    logic_check: bool,
    issue_count: int,
) -> float:
    """
    Calculate critic's confidence in the analysis.
    """
    confidence = 0.8
    
    if not citation_check:
        confidence -= 0.15
    if not logic_check:
        confidence -= 0.15
    
    # Reduce for each issue
    confidence -= issue_count * 0.05
    
    return max(0.4, min(confidence, 0.95))


def _generate_revision_feedback(issues: List[str]) -> str:
    """
    Generate constructive feedback for the Analyst.
    """
    lines = ["Please revise the analysis to address these issues:"]
    
    for i, issue in enumerate(issues[:5], 1):  # Top 5 issues
        lines.append(f"  {i}. {issue}")
    
    if len(issues) > 5:
        lines.append(f"  ... and {len(issues) - 5} more issues")
    
    return "\n".join(lines)


# =============================================================================
# DECISION FUNCTION (for LangGraph)
# =============================================================================

def should_revise(state: AgentState) -> str:
    """
    Conditional edge function for LangGraph.
    
    Returns:
        "revise" if needs revision, "approve" if approved
    """
    review = state.get("critic_review", {})
    verdict = review.get("verdict", "needs_revision")
    
    if verdict == "approved":
        return "approve"
    else:
        return "revise"


# =============================================================================
# FORMAT OUTPUT
# =============================================================================

def format_review_for_developer(review: Dict[str, Any]) -> str:
    """
    Format critic review for debugging/logging.
    """
    if not review:
        return "No review available"
    
    lines = [
        "🔍 **CRITIC REVIEW**",
        "",
        f"**Verdict:** {review['verdict'].upper()}",
        f"**Citation Check:** {'✅ PASS' if review['citation_check'] else '❌ FAIL'}",
        f"**Logic Check:** {'✅ PASS' if review['logic_check'] else '❌ FAIL'}",
        f"**Confidence:** {review['confidence_score']:.0%}",
        "",
    ]
    
    if review.get("issues"):
        lines.append("**Issues Found:**")
        for issue in review["issues"]:
            lines.append(f"  ⚠️ {issue}")
    else:
        lines.append("✅ No issues found")
    
    lines.append("")
    lines.append(f"**Feedback:** {review['feedback']}")
    
    return "\n".join(lines)


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    from safetravels.agents.state import create_initial_state, TripRequest
    from safetravels.agents.planner import plan_routes
    from safetravels.agents.analyst import analyze_routes
    
    print("=" * 70)
    print("SafeTravels Critic - Test")
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
        query="Verify analysis for Dallas to Chicago route",
        trip_request=trip,
    )
    
    # Run pipeline
    state = plan_routes(state)
    state = analyze_routes(state)
    state = review_analysis(state)
    
    # Display results
    print("\n" + format_review_for_developer(state.get("critic_review")))
    
    print("\n--- Full Reasoning Chain ---")
    for step in state["reasoning_chain"]:
        print(f"  {step}")
    
    print("\n" + "=" * 70)
    print("✅ Critic test complete!")
    print("=" * 70)
