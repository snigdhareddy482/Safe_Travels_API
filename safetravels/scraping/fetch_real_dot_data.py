"""
Script: Fetch Full DOT Truck Stop Data
======================================
Downloads the official 'Jason's Law' Truck Parking dataset from the Bureau of Transportation Statistics (BTS).
Converts the raw GeoJSON/CSV into our application's `dot_truck_stops.json` format.

Source: National Transportation Atlas Database (NTAD)
"""

import requests
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_dot_data")

# Correct URL for NTAD Truck Stop Parking (verified Jan 2026)
# Service Name: NTAD_Truck_Stop_Parking
DOT_DATA_URL = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Truck_Stop_Parking/FeatureServer/0/query"

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "dot_truck_stops.json"

def fetch_and_convert():
    logger.info("Downloading full dataset from DOT/NTAD (Paginated)...")
    
    all_features = []
    offset = 0
    batch_size = 2000 # Max allowed by ArcGIS usually
    
    while True:
        logger.info(f"Fetching batch starting at offset {offset}...")
        try:
            params = {
                "where": "1=1",
                "outFields": "*",
                "outSR": "4326", # Lat/Lon
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": batch_size
            }
            
            response = requests.get(DOT_DATA_URL, params=params)
            response.raise_for_status()
            raw_data = response.json()
            
            features = raw_data.get("features", [])
            
            if not features:
                break
                
            all_features.extend(features)
            logger.info(f"Got {len(features)} records. Total: {len(all_features)}")
            
            if len(features) < batch_size:
                break # End of data
                
            offset += batch_size
            
        except Exception as e:
            logger.error(f"Error fetching batch: {e}")
            break

    logger.info(f"Download complete. Total records: {len(all_features)}")
    
    processed_stops = []
    
    for idx, feature in enumerate(all_features):
        props = feature.get("attributes", {})
        geometry = feature.get("geometry", {})
            
        # Extract fields (mapping standard DOT fields to our schema)
        # Note: Field names vary by dataset version, these are common defaults
        name = props.get("name") or props.get("NAME") or "Unknown Stop"
        city = props.get("city") or props.get("CITY") or ""
        state = props.get("state") or props.get("STATE") or ""
        spaces = props.get("no_spaces") or props.get("SPACES") or 0
        
        # Only include valid records
        if not geometry.get("y") or not geometry.get("x"):
            continue
            
        stop = {
            "id": idx + 1,
            "name": name,
            "city": city,
            "state": state,
            "latitude": geometry.get("y"),
            "longitude": geometry.get("x"),
            "parking_spaces": int(spaces) if spaces else 0,
            "highway": props.get("highway") or props.get("HIGHWAY") or "Unknown",
            "security": "unknown", # DOT doesn't track this detailed level usually
            "amenities": [], # Will be populated by simple heuristics
            "risk_score": 5 # Default neutral score
        }
        
        # Simple Heuristics for amenities
        if "Pilot" in name or "Flying J" in name or "Love's" in name or "TA " in name:
            stop["amenities"] = ["fuel", "restaurant", "showers"]
            stop["security"] = "medium"
        elif "Rest Area" in name:
            stop["amenities"] = ["restrooms"]
            stop["security"] = "low"
        
        processed_stops.append(stop)
            
    # Save to file
    output_data = {
        "metadata": {
            "source": "US DOT / NTAD",
            "dataset": "Jason's Law Truck Parking Survey",
            "total_records": len(processed_stops),
            "last_updated": "2026-01"
        },
        "truck_stops": processed_stops
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Successfully saved {len(processed_stops)} stops to {OUTPUT_FILE}")
        

if __name__ == "__main__":
    fetch_and_convert()
