"""
SafeTravels Real-Time - Suggestions
=====================================

Generates route suggestions for the driver when conditions change.
Driver CHOOSES which option to take (no auto-reroute).

FEATURES:
    - Monitor condition changes (weather, traffic, incidents)
    - Generate alternative options when risk increases
    - Let driver select preferred option
    - Track suggestion history

DESIGN PRINCIPLE:
    No auto-rerouting! Driver is in control.
    System suggests, driver decides.

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SuggestionTrigger(Enum):
    """What triggered the suggestion."""
    WEATHER_CHANGE = "weather_change"
    TRAFFIC_INCIDENT = "traffic_incident"
    NEW_RED_ZONE = "new_red_zone"
    THEFT_ALERT = "theft_alert"
    DRIVER_REQUEST = "driver_request"


class OptionType(Enum):
    """Type of route option."""
    CONTINUE = "continue"        # Stay on current route
    ALTERNATE = "alternate"      # Take different route
    STOP_NOW = "stop_now"       # Stop at next safe location
    WAIT = "wait"               # Wait for conditions to clear


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RouteAlternative:
    """
    A single route alternative for the driver.
    """
    option_id: str
    option_type: OptionType
    description: str
    risk_change: str          # e.g., "5.1 → 7.8"
    new_risk: float
    additional_miles: float
    additional_time_min: float
    is_recommended: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "option_type": self.option_type.value,
            "description": self.description,
            "risk_change": self.risk_change,
            "new_risk": self.new_risk,
            "additional_miles": self.additional_miles,
            "additional_time_min": self.additional_time_min,
            "is_recommended": self.is_recommended,
        }


@dataclass
class RouteSuggestion:
    """
    A suggestion presented to the driver.
    """
    suggestion_id: str
    trigger: SuggestionTrigger
    reason: str
    urgency: str              # "low", "medium", "high"
    options: List[RouteAlternative]
    recommended_option_id: str
    timestamp: str
    expires_in_minutes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "trigger": self.trigger.value,
            "reason": self.reason,
            "urgency": self.urgency,
            "options": [o.to_dict() for o in self.options],
            "recommended_option_id": self.recommended_option_id,
            "timestamp": self.timestamp,
            "expires_in_minutes": self.expires_in_minutes,
        }


# =============================================================================
# SUGGESTION GENERATOR
# =============================================================================

class SuggestionGenerator:
    """
    Generates route suggestions when conditions change.
    """
    
    def __init__(self):
        self._suggestion_counter = 0
        self._active_suggestions: Dict[str, RouteSuggestion] = {}
    
    def generate_suggestion(
        self,
        trigger: SuggestionTrigger,
        reason: str,
        current_risk: float,
        new_risk: float,
        current_route: str,
        alternatives: List[Dict[str, Any]],
    ) -> RouteSuggestion:
        """
        Generate a new suggestion for the driver.
        
        Args:
            trigger: What caused this suggestion
            reason: Human-readable explanation
            current_risk: Current route risk score
            new_risk: Updated risk score
            current_route: Current route ID
            alternatives: List of alternative route data
            
        Returns:
            RouteSuggestion for driver to review
        """
        self._suggestion_counter += 1
        suggestion_id = f"sug_{self._suggestion_counter:04d}"
        
        # Determine urgency
        risk_delta = new_risk - current_risk
        if risk_delta >= 2.0 or new_risk >= 8.0:
            urgency = "high"
            expires = 10
        elif risk_delta >= 1.0 or new_risk >= 6.0:
            urgency = "medium"
            expires = 30
        else:
            urgency = "low"
            expires = 60
        
        # Build options
        options = self._build_options(
            current_risk, new_risk, current_route, alternatives
        )
        
        # Find recommended option (lowest risk that isn't "continue")
        recommended = options[0].option_id  # Default to first
        for opt in options:
            if opt.is_recommended:
                recommended = opt.option_id
                break
        
        suggestion = RouteSuggestion(
            suggestion_id=suggestion_id,
            trigger=trigger,
            reason=reason,
            urgency=urgency,
            options=options,
            recommended_option_id=recommended,
            timestamp=datetime.utcnow().isoformat(),
            expires_in_minutes=expires,
        )
        
        self._active_suggestions[suggestion_id] = suggestion
        logger.info(f"Generated suggestion {suggestion_id}: {reason}")
        
        return suggestion
    
    def _build_options(
        self,
        current_risk: float,
        new_risk: float,
        current_route: str,
        alternatives: List[Dict[str, Any]],
    ) -> List[RouteAlternative]:
        """Build list of options for the driver."""
        options = []
        
        # Option A: Stay on current route (with updated risk)
        options.append(RouteAlternative(
            option_id="opt_A",
            option_type=OptionType.CONTINUE,
            description=f"Stay on {current_route} (risk increased)",
            risk_change=f"{current_risk:.1f} → {new_risk:.1f}",
            new_risk=new_risk,
            additional_miles=0,
            additional_time_min=0,
            is_recommended=False,
        ))
        
        # Option B, C: Alternative routes
        for i, alt in enumerate(alternatives[:2], start=1):
            alt_risk = alt.get("risk_score", current_risk)
            options.append(RouteAlternative(
                option_id=f"opt_{chr(65 + i)}",  # B, C
                option_type=OptionType.ALTERNATE,
                description=alt.get("name", f"Alternative Route {i}"),
                risk_change=f"{current_risk:.1f} → {alt_risk:.1f}",
                new_risk=alt_risk,
                additional_miles=alt.get("extra_miles", 20),
                additional_time_min=alt.get("extra_time", 30),
                is_recommended=(alt_risk < new_risk),
            ))
        
        # Option: Stop at safe location
        options.append(RouteAlternative(
            option_id="opt_STOP",
            option_type=OptionType.STOP_NOW,
            description="Stop at next safe truck stop",
            risk_change=f"{current_risk:.1f} → 1.0",
            new_risk=1.0,
            additional_miles=5,
            additional_time_min=0,  # Depends on how long they stay
            is_recommended=(new_risk >= 8.0),
        ))
        
        return options
    
    def driver_selects_option(
        self,
        suggestion_id: str,
        selected_option_id: str,
    ) -> Dict[str, Any]:
        """
        Process driver's selection.
        
        Args:
            suggestion_id: Which suggestion they're responding to
            selected_option_id: Which option they chose
            
        Returns:
            Confirmation with next steps
        """
        suggestion = self._active_suggestions.get(suggestion_id)
        
        if not suggestion:
            return {"error": "Suggestion not found or expired"}
        
        selected = None
        for opt in suggestion.options:
            if opt.option_id == selected_option_id:
                selected = opt
                break
        
        if not selected:
            return {"error": "Invalid option selected"}
        
        # Remove from active
        del self._active_suggestions[suggestion_id]
        
        logger.info(
            f"Driver selected {selected_option_id} for {suggestion_id}: "
            f"{selected.description}"
        )
        
        return {
            "success": True,
            "selected": selected.to_dict(),
            "action": self._get_action_steps(selected),
        }
    
    def _get_action_steps(self, option: RouteAlternative) -> str:
        """Get action steps for the selected option."""
        if option.option_type == OptionType.CONTINUE:
            return "Continuing on current route. Risk monitoring active."
        elif option.option_type == OptionType.ALTERNATE:
            return f"Rerouting via {option.description}. GPS updating..."
        elif option.option_type == OptionType.STOP_NOW:
            return "Finding nearest safe truck stop. Proceed to next exit."
        elif option.option_type == OptionType.WAIT:
            return "Monitoring conditions. Will alert when clear."
        return "Processing selection..."
    
    def get_active_suggestions(self) -> List[Dict[str, Any]]:
        """Get all active suggestions."""
        return [s.to_dict() for s in self._active_suggestions.values()]


# =============================================================================
# FORMAT FOR DRIVER
# =============================================================================

def format_suggestion_for_driver(suggestion: RouteSuggestion) -> str:
    """
    Format a suggestion as a message for the driver.
    """
    # Urgency indicators
    urgency_icons = {
        "high": "🔴 URGENT",
        "medium": "🟡 ATTENTION",
        "low": "🔵 INFO",
    }
    
    lines = [
        "=" * 50,
        f"{urgency_icons.get(suggestion.urgency, '📢')} ROUTE UPDATE",
        "=" * 50,
        "",
        f"**Reason:** {suggestion.reason}",
        "",
        "**Your Options:**",
    ]
    
    for opt in suggestion.options:
        rec_mark = "✅ " if opt.is_recommended else "   "
        lines.append(f"{rec_mark}[{opt.option_id}] {opt.description}")
        lines.append(f"      Risk: {opt.risk_change}")
        if opt.additional_miles > 0:
            lines.append(f"      +{opt.additional_miles:.0f}mi, +{opt.additional_time_min:.0f}min")
        lines.append("")
    
    lines.append(f"**Recommended:** {suggestion.recommended_option_id}")
    lines.append(f"**Expires in:** {suggestion.expires_in_minutes} minutes")
    lines.append("")
    lines.append("Reply with option ID (e.g., 'opt_B') to select.")
    lines.append("=" * 50)
    
    return "\n".join(lines)


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Suggestion System - Test")
    print("=" * 70)
    
    generator = SuggestionGenerator()
    
    # Simulate condition change
    suggestion = generator.generate_suggestion(
        trigger=SuggestionTrigger.TRAFFIC_INCIDENT,
        reason="Major accident ahead on I-35. 2-hour delay expected.",
        current_risk=5.1,
        new_risk=7.8,
        current_route="route_A",
        alternatives=[
            {"name": "I-40 Bypass", "risk_score": 4.2, "extra_miles": 45, "extra_time": 50},
            {"name": "US-75 Route", "risk_score": 5.5, "extra_miles": 30, "extra_time": 35},
        ],
    )
    
    # Display for driver
    print("\n" + format_suggestion_for_driver(suggestion))
    
    # Simulate driver selection
    print("\n--- Driver selects opt_B ---")
    result = generator.driver_selects_option(
        suggestion.suggestion_id,
        "opt_B"
    )
    print(f"Result: {result['action']}")
    
    print("\n" + "=" * 70)
    print("✅ Suggestion System test complete!")
    print("=" * 70)
