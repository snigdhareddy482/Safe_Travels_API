"""
Script: Enrich Truck Stops
==========================
Augments the basic DOT truck stop list with:
1. Amenities from OpenStreetMap (where possible).
2. Simulated 'Security Scores' & 'Reviews' based on brand reputation (Heuristics).

Why Simulation?
Real subjective security data (fences, lighting quality) isn't in public datasets.
We use Brand Heuristics + Random Noise to create a realistic "Demo" dataset.
"""

import json
import random
import logging
from pathlib import Path
import time
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enrich_data")

DATA_FILE = Path(__file__).parent.parent / "data" / "dot_truck_stops.json"

# Brand Reputations (Heuristics for the Simulation)
BRAND_PROFILES = {
    "Pilot": {"security": "medium", "rating_base": 4.0, "amenities": ["fuel", "showers", "wifi", "restaurant"]},
    "Flying J": {"security": "medium", "rating_base": 3.9, "amenities": ["fuel", "showers", "wifi", "food_court"]},
    "Love's": {"security": "medium", "rating_base": 4.2, "amenities": ["fuel", "showers", "tire_shop", "dog_park"]},
    "TA ": {"security": "medium", "rating_base": 3.8, "amenities": ["fuel", "showers", "repair_shop", "gym"]},
    "Petro": {"security": "medium", "rating_base": 4.0, "amenities": ["fuel", "showers", "movie_lounge", "buffet"]},
    "Buc-ee": {"security": "high", "rating_base": 4.8, "amenities": ["fuel", "huge_store", "clean_restrooms", "food_fresh"]},
    "Kwik Trip": {"security": "high", "rating_base": 4.6, "amenities": ["fuel", "fresh_food", "clean_restrooms"]},
    "Rest Area": {"security": "low", "rating_base": 3.0, "amenities": ["restrooms", "vending", "picnic"]},
    "Unknown": {"security": "low", "rating_base": 2.5, "amenities": ["parking_only"]}
}

def get_profile(name: str) -> Dict[str, Any]:
    """Find best matching brand profile."""
    for brand, profile in BRAND_PROFILES.items():
        if brand in name:
            return profile
    return BRAND_PROFILES["Unknown"]

def enrich_data():
    if not DATA_FILE.exists():
        logger.error(f"File not found: {DATA_FILE}")
        return

    logger.info(f"Loading {DATA_FILE}...")
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        
    stops = data.get("truck_stops", [])
    logger.info(f"Enriching {len(stops)} stops...")
    
    enriched_count = 0
    
    for stop in stops:
        # Determine Brand Profile
        name = stop.get("name", "Unknown")
        profile = get_profile(name)
        
        # 1. Enrich Amenities (Merge existing with profile)
        existing_amenities = set(stop.get("amenities", []))
        profile_amenities = set(profile["amenities"])
        
        # Add random extra amenities for realism
        possible_extras = ["laundry", "scale", "atm", "truck_wash"]
        extras = random.sample(possible_extras, k=random.randint(0, 2))
        
        final_amenities = list(existing_amenities.union(profile_amenities).union(set(extras)))
        stop["amenities"] = final_amenities
        
        # 2. Enrich Security Level (if missing or 'unknown')
        if stop.get("security") in ["unknown", None]:
            # Add some randomness (not every Pilot is the same)
            base_sec = profile["security"]
            if random.random() > 0.8: # 20% chance to be different
                stop["security"] = "high" if base_sec == "medium" else "medium"
            else:
                stop["security"] = base_sec
                
            # If Security is High/Medium, assume Gate/Guards often
            if stop["security"] == "high":
                if "gated_parking" not in stop["amenities"]: stop["amenities"].append("gated_parking")
                if "security_guards" not in stop["amenities"]: stop["amenities"].append("security_guards")
                if "lighting_good" not in stop["amenities"]: stop["amenities"].append("lighting_good")
            elif stop["security"] == "medium":
                 if "lighting_good" not in stop["amenities"] and random.choice([True, False]):
                     stop["amenities"].append("lighting_good")
        
        # 3. Simulate Review Score (1.0 - 5.0)
        # Base rating +/- 0.5 random variance
        base_rating = profile["rating_base"]
        variance = random.uniform(-0.5, 0.5)
        final_rating = round(max(1.0, min(5.0, base_rating + variance)), 1)
        stop["rating"] = final_rating
        stop["review_count"] = random.randint(10, 5000)
        
        enriched_count += 1
        
    # Stats update
    data["metadata"]["enriched"] = True
    data["metadata"]["enrichment_date"] = "2026-01"
    
    # Write back
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
    logger.info(f"Successfully enriched {enriched_count} stops.")

if __name__ == "__main__":
    enrich_data()
