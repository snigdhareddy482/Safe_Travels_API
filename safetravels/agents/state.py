"""
SafeTravels Agents - Shared State
==================================

Defines the state that flows between agents in the LangGraph workflow.
All agents read from and write to this shared state.

STATE STRUCTURE:
    - Input: User query, origin, destination, cargo info
    - Working: Documents, route options, analysis
    - Output: Final plan, recommendations, confidence

Design Principles:
    - TypedDict for type safety
    - Immutable-style updates (agents return new state)
    - Clear separation of input/working/output data

Author: SafeTravels Team
Created: January 2026
"""

from typing import TypedDict, List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class AgentMode(Enum):
    """Which agent mode is active."""
    PLANNING = "planning"        # Initial route planning
    MONITORING = "monitoring"    # Real-time during trip
    REPLANNING = "replanning"   # Suggesting new routes


class CriticVerdict(Enum):
    """Critic's decision on the analysis."""
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TripRequest:
    """
    User's trip request with all context.
    """
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    commodity: str = "general"
    cargo_value: float = 50000.0
    departure_time: Optional[str] = None
    special_requirements: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": {"lat": self.origin_lat, "lon": self.origin_lon},
            "destination": {"lat": self.destination_lat, "lon": self.destination_lon},
            "commodity": self.commodity,
            "cargo_value": self.cargo_value,
            "departure_time": self.departure_time,
        }


@dataclass
class RouteOption:
    """
    A single route option with risk assessment.
    """
    route_id: str                    # "route_a", "route_b", etc.
    name: str                        # "I-35 → I-44 → I-55"
    total_miles: float
    estimated_hours: float
    risk_score: float                # 1-10
    risk_level: str                  # low/moderate/high/critical
    red_zone_count: int
    red_zones: List[Dict[str, Any]]
    avoids_hotspots: bool            # Did we route around hotspots?
    is_recommended: bool             # System recommendation
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_id": self.route_id,
            "name": self.name,
            "total_miles": round(self.total_miles, 1),
            "estimated_hours": round(self.estimated_hours, 1),
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "red_zone_count": self.red_zone_count,
            "avoids_hotspots": self.avoids_hotspots,
            "is_recommended": self.is_recommended,
        }


@dataclass
class AnalysisResult:
    """
    Analyst's assessment with full reasoning.
    """
    selected_route_id: str
    reasoning: str                   # Full explanation
    claims: List[Dict[str, str]]     # [{"claim": "...", "source": "..."}]
    risk_factors: List[str]
    recommendations: List[str]
    confidence: float                # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_route_id": self.selected_route_id,
            "reasoning": self.reasoning,
            "claims": self.claims,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
        }


@dataclass
class CriticReview:
    """
    Critic's verification of the analysis.
    """
    verdict: CriticVerdict
    citation_check: bool             # All claims have sources?
    logic_check: bool                # Math/scores consistent?
    confidence_score: float          # Critic's confidence
    issues: List[str]                # Any problems found
    feedback: str                    # Feedback for analyst
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "citation_check": self.citation_check,
            "logic_check": self.logic_check,
            "confidence_score": self.confidence_score,
            "issues": self.issues,
            "feedback": self.feedback,
        }


@dataclass
class RouteSuggestion:
    """
    Real-time route suggestion for driver (NOT auto-reroute).
    """
    reason: str                      # Why suggesting change
    current_risk_change: str         # "5.1 → 7.8"
    options: List[Dict[str, Any]]    # Alternative options
    recommended_option: str          # Which one we suggest
    urgency: str                     # "low", "medium", "high"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "current_risk_change": self.current_risk_change,
            "options": self.options,
            "recommended_option": self.recommended_option,
            "urgency": self.urgency,
        }


# =============================================================================
# MAIN AGENT STATE
# =============================================================================

class AgentState(TypedDict):
    """
    Shared state passed between all agents in the workflow.
    
    FLOW:
        1. User provides trip_request
        2. Planner generates route_options
        3. Analyst creates analysis
        4. Critic reviews → verdict
        5. If approved → final_plan
        6. If needs_revision → back to analyst
    """
    # --- INPUT ---
    trip_request: Optional[Dict[str, Any]]
    query: str                           # Natural language query
    
    # --- RETRIEVAL ---
    documents: List[str]                 # Retrieved documents
    tool_results: Dict[str, Any]         # Results from MCP tools
    
    # --- PLANNING ---
    route_options: List[Dict[str, Any]]  # Multiple route choices
    selected_route: Optional[str]        # User or system selection
    
    # --- ANALYSIS ---
    analysis: Optional[Dict[str, Any]]   # Analyst's assessment
    reasoning_chain: List[str]           # Step-by-step reasoning
    
    # --- VERIFICATION ---
    critic_review: Optional[Dict[str, Any]]
    revision_count: int                  # How many times revised
    
    # --- OUTPUT ---
    final_plan: Optional[Dict[str, Any]]
    confidence: float
    warnings: List[str]
    
    # --- REAL-TIME ---
    mode: str                            # planning/monitoring/replanning
    current_position: Optional[Dict[str, float]]
    active_suggestions: List[Dict[str, Any]]
    
    # --- MEMORY ---
    driver_id: Optional[str]
    trip_history: List[Dict[str, Any]]


# =============================================================================
# STATE FACTORY
# =============================================================================

def create_initial_state(
    query: str = "",
    trip_request: Optional[TripRequest] = None,
    driver_id: Optional[str] = None,
) -> AgentState:
    """
    Create a fresh agent state for a new query.
    
    Args:
        query: Natural language query from user
        trip_request: Structured trip request
        driver_id: Optional driver ID for memory
        
    Returns:
        Initialized AgentState
    """
    return AgentState(
        # Input
        trip_request=trip_request.to_dict() if trip_request else None,
        query=query,
        
        # Retrieval
        documents=[],
        tool_results={},
        
        # Planning
        route_options=[],
        selected_route=None,
        
        # Analysis
        analysis=None,
        reasoning_chain=[],
        
        # Verification
        critic_review=None,
        revision_count=0,
        
        # Output
        final_plan=None,
        confidence=0.0,
        warnings=[],
        
        # Real-time
        mode=AgentMode.PLANNING.value,
        current_position=None,
        active_suggestions=[],
        
        # Memory
        driver_id=driver_id,
        trip_history=[],
    )


# =============================================================================
# STATE HELPERS
# =============================================================================

def add_reasoning_step(state: AgentState, step: str) -> AgentState:
    """Add a step to the reasoning chain."""
    state["reasoning_chain"].append(f"[{datetime.utcnow().isoformat()}] {step}")
    return state


def increment_revision(state: AgentState) -> AgentState:
    """Increment revision count for loop limit."""
    state["revision_count"] += 1
    return state


def should_stop_revising(state: AgentState, max_revisions: int = 3) -> bool:
    """Check if we've hit the revision limit."""
    return state["revision_count"] >= max_revisions
