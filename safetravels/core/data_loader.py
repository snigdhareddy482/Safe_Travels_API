"""
Unified Data Loader
===================

Loads and combines all data sources for the SafeTravels API.

Data Files:
- dot_truck_stops.json (40 original stops)
- osm_truck_stops.json (139 OpenStreetMap stops)
- fbi_crime_data.json (crime by county)
- high_risk_corridors.json (10 Red Zone corridors)
- cargo_theft_stats.json (theft by commodity)
- hos_regulations.json (HOS rules)
- us_holidays.json (holidays + risk periods)
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class TruckStop:
    """Unified truck stop model."""
    id: int
    name: str
    city: str
    state: str
    latitude: float
    longitude: float
    security_score: int
    tier: str
    parking_spaces: int
    amenities: List[str]
    brand: str = ""
    highway: str = ""
    has_security: bool = False
    has_cctv: bool = False
    is_24_hours: bool = True
    source: str = "dot"


@dataclass
class HighRiskCorridor:
    """Red Zone corridor model."""
    id: int
    name: str
    states: List[str]
    highways: List[str]
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    risk_level: str
    risk_score: float
    primary_threats: List[str]
    recommended_stops: List[str]


class DataLoader:
    """Unified data loader for all SafeTravels data sources."""
    
    _instance = None
    _loaded = False
    
    # Data caches
    truck_stops: List[TruckStop] = []
    high_risk_corridors: List[HighRiskCorridor] = []
    theft_hotspots: List[Dict] = []
    crime_data: Dict = {}
    cargo_theft_stats: Dict = {}
    hos_regulations: Dict = {}
    holidays: Dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_all(self) -> None:
        """Load all data sources."""
        if self._loaded:
            return
        
        logger.info("Loading all data sources...")
        
        self._load_truck_stops()
        self._load_high_risk_corridors()
        self._load_crime_data()
        self._load_cargo_theft_stats()
        self._load_hos_regulations()
        self._load_holidays()
        
        self._loaded = True
        logger.info(f"Data loaded: {len(self.truck_stops)} stops, {len(self.high_risk_corridors)} corridors")
    
    def _load_truck_stops(self) -> None:
        """Load and merge truck stops from all sources."""
        stops = []
        stop_id = 0
        
        # Load DOT truck stops
        dot_file = DATA_DIR / "dot_truck_stops.json"
        if dot_file.exists():
            with open(dot_file) as f:
                data = json.load(f)
                for stop in data.get("truck_stops", []):
                    stop_id += 1
                    stops.append(TruckStop(
                        id=stop_id,
                        name=stop.get("name", f"Stop #{stop_id}"),
                        city=stop.get("city", ""),
                        state=stop.get("state", ""),
                        latitude=stop.get("latitude", 0),
                        longitude=stop.get("longitude", 0),
                        security_score=self._calculate_security_score(stop),
                        tier=self._get_tier(stop),
                        parking_spaces=stop.get("parking_spaces", 50),
                        amenities=stop.get("amenities", []),
                        brand=stop.get("name", "").split()[0] if stop.get("name") else "",
                        highway=stop.get("highway", ""),
                        has_security="security" in str(stop.get("amenities", [])).lower(),
                        has_cctv="cctv" in str(stop.get("amenities", [])).lower(),
                        source="dot"
                    ))
            logger.info(f"Loaded {len(stops)} DOT truck stops")
        
        # Load OSM truck stops
        osm_file = DATA_DIR / "osm_truck_stops.json"
        if osm_file.exists():
            with open(osm_file) as f:
                data = json.load(f)
                osm_count = 0
                for stop in data.get("truck_stops", []):
                    stop_id += 1
                    osm_count += 1
                    stops.append(TruckStop(
                        id=stop_id,
                        name=stop.get("name", f"Truck Stop #{stop_id}"),
                        city=stop.get("city", stop.get("region", "")),
                        state=stop.get("state", ""),
                        latitude=stop.get("latitude", stop.get("lat", 0)),
                        longitude=stop.get("longitude", stop.get("lon", 0)),
                        security_score=stop.get("security_score", 70),
                        tier=stop.get("tier", "LEVEL_2"),
                        parking_spaces=stop.get("parking_spaces", 50),
                        amenities=stop.get("amenities", ["fuel", "diesel"]),
                        brand=stop.get("brand", ""),
                        has_security=stop.get("has_security", False),
                        has_cctv=stop.get("has_cctv", False),
                        source="osm"
                    ))
            logger.info(f"Loaded {osm_count} OSM truck stops")
        
        self.truck_stops = stops
    
    def _calculate_security_score(self, stop: Dict) -> int:
        """Calculate security score based on amenities."""
        score = 50  # Base score
        amenities = stop.get("amenities", [])
        
        if "security_guards" in amenities or "security" in str(amenities).lower():
            score += 20
        if "cctv" in str(amenities).lower() or "camera" in str(amenities).lower():
            score += 10
        if "gated" in str(amenities).lower():
            score += 15
        if "well_lit" in str(amenities).lower() or "lighting" in str(amenities).lower():
            score += 5
        
        # Risk score adjustment
        risk = stop.get("risk_score", 5)
        if risk <= 2:
            score += 10
        elif risk >= 7:
            score -= 15
        
        return max(20, min(100, score))
    
    def _get_tier(self, stop: Dict) -> str:
        """Get security tier from stop data."""
        security = stop.get("security", "").lower()
        if security == "high":
            return "LEVEL_1"
        elif security == "medium":
            return "LEVEL_2"
        elif security == "low":
            return "LEVEL_3"
        return "LEVEL_2"
    
    def _load_high_risk_corridors(self) -> None:
        """Load high-risk corridor data."""
        file_path = DATA_DIR / "high_risk_corridors.json"
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
                
                for corridor in data.get("high_risk_corridors", []):
                    self.high_risk_corridors.append(HighRiskCorridor(
                        id=corridor.get("id"),
                        name=corridor.get("name"),
                        states=corridor.get("states", []),
                        highways=corridor.get("highways", []),
                        start_lat=corridor.get("start_coords", {}).get("lat", 0),
                        start_lng=corridor.get("start_coords", {}).get("lng", 0),
                        end_lat=corridor.get("end_coords", {}).get("lat", 0),
                        end_lng=corridor.get("end_coords", {}).get("lng", 0),
                        risk_level=corridor.get("risk_level", "high"),
                        risk_score=corridor.get("risk_score", 7),
                        primary_threats=corridor.get("primary_threats", []),
                        recommended_stops=corridor.get("recommended_stops_before", [])
                    ))
                
                self.theft_hotspots = data.get("theft_hotspots", [])
                
            logger.info(f"Loaded {len(self.high_risk_corridors)} high-risk corridors")
    
    def _load_crime_data(self) -> None:
        """Load FBI crime data."""
        file_path = DATA_DIR / "fbi_crime_data.json"
        if file_path.exists():
            with open(file_path) as f:
                self.crime_data = json.load(f)
            logger.info("Loaded FBI crime data")
    
    def _load_cargo_theft_stats(self) -> None:
        """Load cargo theft statistics."""
        file_path = DATA_DIR / "cargo_theft_stats.json"
        if file_path.exists():
            with open(file_path) as f:
                self.cargo_theft_stats = json.load(f)
            logger.info("Loaded cargo theft stats")
    
    def _load_hos_regulations(self) -> None:
        """Load HOS regulations."""
        file_path = DATA_DIR / "hos_regulations.json"
        if file_path.exists():
            with open(file_path) as f:
                self.hos_regulations = json.load(f)
            logger.info("Loaded HOS regulations")
    
    def _load_holidays(self) -> None:
        """Load US holidays data."""
        file_path = DATA_DIR / "us_holidays.json"
        if file_path.exists():
            with open(file_path) as f:
                self.holidays = json.load(f)
            logger.info("Loaded US holidays data")
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_all_stops(self) -> List[TruckStop]:
        """Get all truck stops."""
        self.load_all()
        return self.truck_stops
    
    def get_stops_by_state(self, state: str) -> List[TruckStop]:
        """Get truck stops by state."""
        self.load_all()
        return [s for s in self.truck_stops if s.state.upper() == state.upper()]
    
    def get_stops_by_tier(self, tier: str) -> List[TruckStop]:
        """Get truck stops by security tier."""
        self.load_all()
        return [s for s in self.truck_stops if s.tier == tier]
    
    def get_corridor_by_name(self, name: str) -> Optional[HighRiskCorridor]:
        """Get corridor by name (partial match)."""
        self.load_all()
        name_lower = name.lower()
        for corridor in self.high_risk_corridors:
            if name_lower in corridor.name.lower():
                return corridor
        return None
    
    def get_commodity_risk(self, commodity: str) -> Dict:
        """Get theft risk for a commodity type."""
        self.load_all()
        return self.cargo_theft_stats.get("commodity_risk_scores", {}).get(commodity, {})
    
    def get_holiday_risk_multiplier(self, date: datetime) -> float:
        """Get risk multiplier for a given date."""
        self.load_all()
        date_str = date.strftime("%Y-%m-%d")
        
        for holiday in self.holidays.get("federal_holidays_2026", []):
            if holiday.get("date") == date_str:
                return holiday.get("theft_risk_multiplier", 1.0)
        
        return 1.0
    
    def is_in_high_risk_corridor(self, lat: float, lng: float) -> Optional[HighRiskCorridor]:
        """Check if a location is within a high-risk corridor."""
        self.load_all()
        
        for corridor in self.high_risk_corridors:
            # Simple bounding box check
            min_lat = min(corridor.start_lat, corridor.end_lat) - 0.5
            max_lat = max(corridor.start_lat, corridor.end_lat) + 0.5
            min_lng = min(corridor.start_lng, corridor.end_lng) - 0.5
            max_lng = max(corridor.start_lng, corridor.end_lng) + 0.5
            
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                return corridor
        
        return None


# Singleton instance
data_loader = DataLoader()


# Convenience functions
def get_all_truck_stops() -> List[TruckStop]:
    """Get all truck stops from all sources."""
    return data_loader.get_all_stops()


def get_high_risk_corridors() -> List[HighRiskCorridor]:
    """Get all high-risk corridors."""
    data_loader.load_all()
    return data_loader.high_risk_corridors


def get_theft_hotspots() -> List[Dict]:
    """Get theft hotspot locations."""
    data_loader.load_all()
    return data_loader.theft_hotspots


def check_corridor_risk(lat: float, lng: float) -> Optional[HighRiskCorridor]:
    """Check if location is in a high-risk corridor."""
    return data_loader.is_in_high_risk_corridor(lat, lng)


# Test if run directly
if __name__ == "__main__":
    loader = DataLoader()
    loader.load_all()
    
    print(f"\n=== Data Loader Test ===")
    print(f"Truck Stops: {len(loader.truck_stops)}")
    print(f"High-Risk Corridors: {len(loader.high_risk_corridors)}")
    print(f"Theft Hotspots: {len(loader.theft_hotspots)}")
    print(f"\nSample stops:")
    for stop in loader.truck_stops[:5]:
        print(f"  - {stop.name} ({stop.city}, {stop.state}) - Score: {stop.security_score}")
    print(f"\nCorridors:")
    for corridor in loader.high_risk_corridors[:3]:
        print(f"  - {corridor.name} (Risk: {corridor.risk_score})")
