"""
SafeTravels Agents - Memory System
===================================

Manages driver trip history and learning from feedback.

FEATURES:
    - Store past trip data (routes taken, stops used)
    - Remember driver preferences
    - Learn from feedback (safe/unsafe stop ratings)
    - Personalize recommendations

USAGE:
    from safetravels.agents.memory import TripMemory
    
    memory = TripMemory(driver_id="driver_001")
    memory.record_trip(...)
    past_trips = memory.get_recent_trips(limit=5)

Author: SafeTravels Team
Created: January 2026
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default storage directory (can be overridden)
DEFAULT_MEMORY_DIR = Path("./trip_memory")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TripRecord:
    """
    Record of a completed trip.
    """
    trip_id: str
    driver_id: str
    timestamp: str
    origin: Dict[str, float]          # {"lat": ..., "lon": ...}
    destination: Dict[str, float]
    route_taken: str                   # route_id
    commodity: str
    cargo_value: float
    total_miles: float
    actual_duration_hours: float
    incidents: List[str] = field(default_factory=list)
    stop_ratings: Dict[str, int] = field(default_factory=dict)  # stop_id -> 1-5
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StopFeedback:
    """
    Driver feedback about a stop.
    """
    stop_id: str
    stop_name: str
    driver_id: str
    rating: int                        # 1-5 (1=unsafe, 5=very safe)
    comments: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# MEMORY CLASS
# =============================================================================

class TripMemory:
    """
    Manages trip history and driver preferences.
    
    Storage is file-based (JSON) for simplicity.
    In production, use a database (PostgreSQL, Redis).
    """
    
    def __init__(
        self,
        driver_id: str,
        storage_dir: Optional[Path] = None,
    ):
        """
        Initialize memory for a driver.
        
        Args:
            driver_id: Unique driver identifier
            storage_dir: Directory for storing memory files
        """
        self.driver_id = driver_id
        self.storage_dir = storage_dir or DEFAULT_MEMORY_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._trips: List[TripRecord] = []
        self._feedback: List[StopFeedback] = []
        self._preferences: Dict[str, Any] = {}
        
        # Load existing data
        self._load()
    
    # -------------------------------------------------------------------------
    # TRIP RECORDING
    # -------------------------------------------------------------------------
    
    def record_trip(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        route_taken: str,
        commodity: str = "general",
        cargo_value: float = 50000,
        total_miles: float = 0,
        actual_duration_hours: float = 0,
    ) -> str:
        """
        Record a completed trip.
        
        Returns:
            trip_id of the recorded trip
        """
        trip_id = f"trip_{self.driver_id}_{len(self._trips) + 1}"
        
        trip = TripRecord(
            trip_id=trip_id,
            driver_id=self.driver_id,
            timestamp=datetime.utcnow().isoformat(),
            origin=origin,
            destination=destination,
            route_taken=route_taken,
            commodity=commodity,
            cargo_value=cargo_value,
            total_miles=total_miles,
            actual_duration_hours=actual_duration_hours,
        )
        
        self._trips.append(trip)
        self._save()
        
        logger.info(f"Recorded trip {trip_id}")
        return trip_id
    
    def get_recent_trips(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most recent trips for this driver.
        """
        recent = sorted(
            self._trips,
            key=lambda t: t.timestamp,
            reverse=True,
        )[:limit]
        
        return [t.to_dict() for t in recent]
    
    # -------------------------------------------------------------------------
    # STOP FEEDBACK
    # -------------------------------------------------------------------------
    
    def record_stop_feedback(
        self,
        stop_id: str,
        stop_name: str,
        rating: int,
        comments: str = "",
    ) -> None:
        """
        Record driver feedback about a stop.
        
        Args:
            stop_id: Unique stop identifier
            stop_name: Human-readable stop name
            rating: 1-5 (1=unsafe, 5=very safe)
            comments: Optional comments
        """
        feedback = StopFeedback(
            stop_id=stop_id,
            stop_name=stop_name,
            driver_id=self.driver_id,
            rating=max(1, min(5, rating)),  # Clamp to 1-5
            comments=comments,
            timestamp=datetime.utcnow().isoformat(),
        )
        
        self._feedback.append(feedback)
        self._save()
        
        logger.info(f"Recorded feedback for {stop_name}: {rating}/5")
    
    def get_stop_ratings(self, stop_id: str) -> Dict[str, Any]:
        """
        Get aggregated ratings for a stop.
        """
        ratings = [f for f in self._feedback if f.stop_id == stop_id]
        
        if not ratings:
            return {"stop_id": stop_id, "avg_rating": None, "count": 0}
        
        avg = sum(f.rating for f in ratings) / len(ratings)
        
        return {
            "stop_id": stop_id,
            "avg_rating": round(avg, 1),
            "count": len(ratings),
            "recent_comments": [f.comments for f in ratings[-3:] if f.comments],
        }
    
    def get_unsafe_stops(self) -> List[str]:
        """
        Get list of stops this driver rated as unsafe (1-2).
        """
        unsafe = set()
        for f in self._feedback:
            if f.rating <= 2:
                unsafe.add(f.stop_id)
        return list(unsafe)
    
    # -------------------------------------------------------------------------
    # PREFERENCES
    # -------------------------------------------------------------------------
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a driver preference."""
        self._preferences[key] = value
        self._save()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a driver preference."""
        return self._preferences.get(key, default)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences."""
        return self._preferences.copy()
    
    # -------------------------------------------------------------------------
    # LEARNING
    # -------------------------------------------------------------------------
    
    def get_route_history(
        self,
        origin_area: Optional[str] = None,
        destination_area: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get past routes for similar trips (for learning).
        """
        # TODO: Implement area matching
        return [t.to_dict() for t in self._trips]
    
    def get_personalized_recommendations(self) -> List[str]:
        """
        Generate personalized recommendations based on history.
        """
        recommendations = []
        
        # Check unsafe stops
        unsafe = self.get_unsafe_stops()
        if unsafe:
            recommendations.append(
                f"Based on your feedback, avoiding {len(unsafe)} stops you rated as unsafe."
            )
        
        # Check preferred stop types
        pref = self.get_preference("preferred_stop_type")
        if pref:
            recommendations.append(
                f"Prioritizing {pref} stops based on your preferences."
            )
        
        return recommendations
    
    # -------------------------------------------------------------------------
    # PERSISTENCE
    # -------------------------------------------------------------------------
    
    def _get_file_path(self) -> Path:
        """Get file path for this driver's memory."""
        return self.storage_dir / f"{self.driver_id}_memory.json"
    
    def _save(self) -> None:
        """Save memory to file."""
        data = {
            "driver_id": self.driver_id,
            "trips": [t.to_dict() for t in self._trips],
            "feedback": [f.to_dict() for f in self._feedback],
            "preferences": self._preferences,
        }
        
        with open(self._get_file_path(), "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self) -> None:
        """Load memory from file."""
        path = self._get_file_path()
        
        if not path.exists():
            return
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            self._trips = [
                TripRecord(**t) for t in data.get("trips", [])
            ]
            self._feedback = [
                StopFeedback(**f) for f in data.get("feedback", [])
            ]
            self._preferences = data.get("preferences", {})
            
            logger.info(f"Loaded {len(self._trips)} trips for {self.driver_id}")
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SafeTravels Memory System - Test")
    print("=" * 70)
    
    # Create memory for test driver
    memory = TripMemory(driver_id="test_driver_001")
    
    # Record a trip
    trip_id = memory.record_trip(
        origin={"lat": 32.7767, "lon": -96.7970},
        destination={"lat": 41.8781, "lon": -87.6298},
        route_taken="route_B",
        commodity="electronics",
        cargo_value=250000,
        total_miles=920,
        actual_duration_hours=14.5,
    )
    print(f"\nRecorded trip: {trip_id}")
    
    # Record stop feedback
    memory.record_stop_feedback(
        stop_id="pilot_432",
        stop_name="Pilot Travel Center #432",
        rating=4,
        comments="Well-lit, good security cameras",
    )
    
    memory.record_stop_feedback(
        stop_id="random_rest_123",
        stop_name="I-35 Rest Area Mile 123",
        rating=2,
        comments="Poor lighting, felt unsafe",
    )
    
    # Get recent trips
    print("\n--- Recent Trips ---")
    for trip in memory.get_recent_trips(3):
        print(f"  {trip['trip_id']}: {trip['route_taken']}")
    
    # Get unsafe stops
    print("\n--- Unsafe Stops ---")
    for stop in memory.get_unsafe_stops():
        print(f"  ⚠️ {stop}")
    
    # Get recommendations
    print("\n--- Personalized Recommendations ---")
    for rec in memory.get_personalized_recommendations():
        print(f"  {rec}")
    
    print("\n" + "=" * 70)
    print("✅ Memory System test complete!")
    print("=" * 70)
