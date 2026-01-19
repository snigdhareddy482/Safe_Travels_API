"""
SafeTravels Agents - Multi-Agent Graph
========================================

Orchestrates the Planner → Analyst → Critic workflow using LangGraph.

WORKFLOW:
    1. Planner generates route options
    2. Analyst provides recommendation with reasoning
    3. Critic verifies (citations, logic)
    4. If APPROVED → Return final plan
    5. If NEEDS_REVISION → Loop back to Analyst (max 3 times)

USAGE:
    from safetravels.agents.multi_agent_graph import run_agent_pipeline
    
    result = run_agent_pipeline(
        query="Plan safest route Dallas to Chicago",
        trip_request=TripRequest(...)
    )

Author: SafeTravels Team
Created: January 2026
"""

from typing import Dict, Any, Optional
import logging

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None
    END = None
    
from safetravels.agents.state import (
    AgentState,
    TripRequest,
    create_initial_state,
    add_reasoning_step,
)
from safetravels.agents.planner import plan_routes, format_routes_for_driver
from safetravels.agents.analyst import analyze_routes, format_analysis_for_driver
from safetravels.agents.critic import review_analysis, format_review_for_developer

logger = logging.getLogger(__name__)


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_planning_graph():
    """
    Build the LangGraph workflow for route planning.
    
    NODES:
        - planner: Generate route options
        - analyst: Analyze and recommend
        - critic: Verify analysis
        - finalize: Prepare final output
    
    EDGES:
        - planner → analyst
        - analyst → critic
        - critic → (approve) → finalize
        - critic → (revise) → analyst
    
    Returns:
        Compiled LangGraph application
    """
    if StateGraph is None:
        logger.error("LangGraph not installed. Cannot build graph.")
        return None
    
    # Create graph with our state type
    workflow = StateGraph(AgentState)
    
    # -----------------------------------------------------------------
    # Add nodes
    # -----------------------------------------------------------------
    workflow.add_node("planner", plan_routes)
    workflow.add_node("analyst", analyze_routes)
    workflow.add_node("critic", review_analysis)
    workflow.add_node("finalize", _finalize_plan)
    
    # -----------------------------------------------------------------
    # Define edges
    # -----------------------------------------------------------------
    
    # Start with planner
    workflow.set_entry_point("planner")
    
    # Planner → Analyst
    workflow.add_edge("planner", "analyst")
    
    # Analyst → Critic
    workflow.add_edge("analyst", "critic")
    
    # Critic → Conditional (approve or revise)
    workflow.add_conditional_edges(
        "critic",
        _route_after_critic,
        {
            "approve": "finalize",
            "revise": "analyst",
        }
    )
    
    # Finalize → END
    workflow.add_edge("finalize", END)
    
    # Compile
    app = workflow.compile()
    logger.info("Planning graph compiled successfully")
    
    return app


def _route_after_critic(state: AgentState) -> str:
    """
    Conditional router after critic review.
    
    Returns:
        "approve" if analysis is approved
        "revise" if needs revision
    """
    review = state.get("critic_review", {})
    verdict = review.get("verdict", "needs_revision")
    revision_count = state.get("revision_count", 0)
    
    # Force approve after max revisions
    if revision_count >= 3:
        logger.warning("Max revisions reached, forcing approval")
        return "approve"
    
    if verdict == "approved":
        return "approve"
    else:
        return "revise"


def _finalize_plan(state: AgentState) -> AgentState:
    """
    Finalize the plan and prepare output.
    """
    logger.info("--- FINALIZE: Preparing final plan ---")
    
    add_reasoning_step(state, "Finalizing plan")
    
    # Build final plan
    final_plan = {
        "status": "complete",
        "route_options": state.get("route_options", []),
        "selected_route": state.get("selected_route"),
        "analysis": state.get("analysis"),
        "critic_review": state.get("critic_review"),
        "recommendations": state.get("analysis", {}).get("recommendations", []),
        "warnings": state.get("warnings", []),
    }
    
    # Calculate final confidence
    analysis_conf = state.get("analysis", {}).get("confidence", 0.7)
    critic_conf = state.get("critic_review", {}).get("confidence_score", 0.7)
    final_confidence = (analysis_conf + critic_conf) / 2
    
    state["final_plan"] = final_plan
    state["confidence"] = final_confidence
    
    return state


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_agent_pipeline(
    query: str,
    trip_request: Optional[TripRequest] = None,
    driver_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full agent pipeline for route planning.
    
    Args:
        query: Natural language query from user
        trip_request: Structured trip request
        driver_id: Optional driver ID for memory
        
    Returns:
        Dict with final plan, routes, analysis, and recommendations
    """
    logger.info(f"Running multi-agent pipeline: {query[:50]}...")
    
    # Create initial state
    state = create_initial_state(
        query=query,
        trip_request=trip_request,
        driver_id=driver_id,
    )
    
    # Build and run graph
    app = build_planning_graph()
    
    if app is None:
        # Fallback if LangGraph not available
        logger.warning("LangGraph not available, running agents manually")
        state = _run_agents_manually(state)
    else:
        # Run the graph
        result = app.invoke(state)
        state = result
    
    return {
        "success": True,
        "final_plan": state.get("final_plan"),
        "route_options": state.get("route_options"),
        "selected_route": state.get("selected_route"),
        "analysis": state.get("analysis"),
        "confidence": state.get("confidence"),
        "warnings": state.get("warnings"),
    }


def _run_agents_manually(state: AgentState) -> AgentState:
    """
    Fallback: Run agents sequentially without LangGraph.
    """
    # Planner
    state = plan_routes(state)
    
    # Analyst-Critic loop
    for i in range(3):
        state = analyze_routes(state)
        state = review_analysis(state)
        
        verdict = state.get("critic_review", {}).get("verdict", "")
        if verdict == "approved":
            break
    
    # Finalize
    state = _finalize_plan(state)
    
    return state


# =============================================================================
# FORMAT OUTPUT
# =============================================================================

def format_final_plan(result: Dict[str, Any]) -> str:
    """
    Format the final plan for the user.
    """
    if not result.get("success"):
        return "❌ Failed to generate plan."
    
    lines = ["=" * 60]
    lines.append("🚛 **SAFETRAVELS TRIP PLAN**")
    lines.append("=" * 60)
    lines.append("")
    
    # Route options
    if result.get("route_options"):
        lines.append(format_routes_for_driver(result["route_options"]))
        lines.append("")
    
    # Selected route
    if result.get("selected_route"):
        lines.append(f"✅ **RECOMMENDED:** {result['selected_route'].upper()}")
        lines.append("")
    
    # Recommendations
    recs = result.get("analysis", {}).get("recommendations", [])
    if recs:
        lines.append("📋 **RECOMMENDATIONS:**")
        for rec in recs[:5]:
            lines.append(f"  {rec}")
        lines.append("")
    
    lines.append(f"**Confidence:** {result.get('confidence', 0):.0%}")
    lines.append("")
    lines.append("💡 Select a route to begin navigation.")
    
    return "\n".join(lines)


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Multi-Agent Pipeline - Test")
    print("=" * 70)
    
    # Create test trip
    trip = TripRequest(
        origin_lat=32.7767,
        origin_lon=-96.7970,      # Dallas
        destination_lat=41.8781,
        destination_lon=-87.6298,  # Chicago
        commodity="electronics",
        cargo_value=250000,
    )
    
    # Run pipeline
    result = run_agent_pipeline(
        query="Plan safest route Dallas to Chicago",
        trip_request=trip,
    )
    
    # Display
    print("\n" + format_final_plan(result))
    
    print("\n--- Metrics ---")
    print(f"Success: {result.get('success')}")
    print(f"Routes: {len(result.get('route_options', []))}")
    print(f"Selected: {result.get('selected_route')}")
    print(f"Confidence: {result.get('confidence', 0):.0%}")
    
    print("\n" + "=" * 70)
    print("✅ Multi-Agent Pipeline test complete!")
    print("=" * 70)
