"""
Fetch Nationwide Truck Stops from OpenStreetMap (Overpass API)
============================================================
Queries for `amenity=fuel` + `hgv=yes` OR `amenity=truck_stop`.
Iterates through all US states to gather maximum data.
Merges with existing DOT data to create a 'Comprehensive' dataset.
"""

import requests
import json
import logging
import time
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_osm_nationwide")

# Simplified State Bounding Boxes (Approximate Centers + Radius could be used, or just BBox)
# Just listing major regions to act as query centers to avoid single massive query timeout
REGIONS = [
    # Northeast
    {'name': 'Northeast', 'bbox': '40.0,-80.0,47.0,-67.0'},
    {'name': 'Mid-Atlantic', 'bbox': '36.0,-82.0,41.0,-74.0'},
    # Southeast
    {'name': 'Southeast', 'bbox': '24.0,-88.0,36.5,-75.0'},
    {'name': 'Deep South', 'bbox': '30.0,-94.0,36.0,-83.0'},
    # Midwest
    {'name': 'Midwest East', 'bbox': '38.0,-90.0,49.0,-80.0'},
    {'name': 'Midwest West', 'bbox': '37.0,-104.0,49.0,-90.0'},
    # Plains
    {'name': 'Plains', 'bbox': '32.0,-105.0,49.0,-95.0'},
    # South
    {'name': 'Texas/OK', 'bbox': '25.0,-106.0,37.0,-93.0'},
    # West
    {'name': 'Rockies', 'bbox': '31.0,-115.0,49.0,-104.0'},
    {'name': 'Southwest', 'bbox': '31.0,-120.0,42.0,-109.0'},
    {'name': 'Northwest', 'bbox': '42.0,-125.0,49.0,-111.0'},
    {'name': 'California', 'bbox': '32.0,-125.0,42.0,-114.0'},
]

DOT_FILE = Path(__file__).parent.parent / "data" / "dot_truck_stops.json"
OUTPUT_FILE = DOT_FILE # We will append to the main file

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance in miles between two points."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 3956 # Radius of earth in miles
    return c * r

def fetch_nationwide():
    logger.info("Starting Nationwide OSM Scan...")
    
    # 1. Load Existing Data
    existing_stops = []
    if DOT_FILE.exists():
        with open(DOT_FILE, 'r') as f:
            existing_data = json.load(f)
            existing_stops = existing_data.get("truck_stops", [])
    
    logger.info(f"Loaded {len(existing_stops)} existing DOT stops.")
    existing_ids = set() # Track by approximate location to deduplicate
    
    # Pre-build lookup for spatial deduplication (naive grid could work, simple list for now)
    # Using specific coord keys "lat,lon" rounded to 3 dec places (~100m)
    existing_coords = set()
    for s in existing_stops:
        lat = round(s.get("latitude", 0), 3)
        lon = round(s.get("longitude", 0), 3)
        existing_coords.add(f"{lat},{lon}")
    
    new_stops = []
    next_id = max([s.get("id", 0) for s in existing_stops] or [0]) + 1
    
    # 2. Query Regions
    for region in REGIONS:
        logger.info(f"Querying Region: {region['name']}...")
        bbox = region['bbox']
        
        # Query: Fuel with HGV access, OR specific truck stops
        query = f'''
        [out:json][timeout:60];
        (
          node["amenity"="fuel"]["hgv"="yes"]({bbox});
          node["amenity"="truck_stop"]({bbox});
        );
        out body;
        '''
        
        retries = 3
        while retries > 0:
            try:
                r = requests.post('https://overpass-api.de/api/interpreter', data={'data': query}, timeout=90)
                if r.status_code == 200:
                    elements = r.json().get('elements', [])
                    logger.info(f"  > Found {len(elements)} candidates.")
                    
                    for elem in elements:
                        lat = elem.get('lat')
                        lon = elem.get('lon')
                        if not lat or not lon: continue
                        
                        # Deduplicate
                        coord_key = f"{round(lat, 3)},{round(lon, 3)}"
                        if coord_key in existing_coords:
                            continue
                            
                        # It's new!
                        tags = elem.get('tags', {})
                        name = tags.get('name', tags.get('brand', 'Unknown Truck Stop'))
                        
                        # REAL Security Data Parsing (No Simulation)
                        is_lit = tags.get("lit") == "yes"
                        is_fenced = tags.get("fenced") == "yes" or "barrier" in tags
                        has_surveillance = tags.get("surveillance") in ["outdoor", "public", "yes"] or "cctv" in str(tags).lower()
                        
                        # Amenities Parsing
                        amenities = ["fuel", "restrooms"] # inferred base
                        if "shower" in str(tags): amenities.append("showers")
                        if "food" in str(tags) or "shop" in str(tags): amenities.append("food")
                        
                        # Add REAL security tags to amenities list causing them to appear in UI
                        if is_lit: amenities.append("lighting_good")
                        if is_fenced: amenities.append("gated_parking")
                        if has_surveillance: amenities.append("cctv")
                        
                        new_stop = {
                            "id": next_id,
                            "name": name,
                            "city": tags.get('addr:city', ''),
                            "state": tags.get('addr:state', ''), 
                            "latitude": lat,
                            "longitude": lon,
                            "parking_spaces": 0, 
                            "highway": tags.get("highway", "Unknown"),
                            "security": "high" if (is_fenced or has_surveillance) else "unknown", # Inferred from REAL tags
                            "amenities": amenities,
                            "risk_score": 5, 
                            "source": "OpenStreetMap",
                            "rating": 3.0,
                            "review_count": 0
                        }
                        
                        new_stops.append(new_stop)
                        existing_coords.add(coord_key)
                        next_id += 1
                        
                    break # Success
                elif r.status_code == 429:
                    logger.warning("  > Rate limit. Waiting 10s...")
                    time.sleep(10)
                    retries -= 1
                else:
                    logger.error(f"  > Error {r.status_code}")
                    retries -= 1
            except Exception as e:
                logger.error(f"  > Exception: {e}")
                retries -= 1
        
        time.sleep(2) # Be nice to public API
        
    logger.info(f"Scanned all regions. Found {len(new_stops)} NEW unique stops.")
    
    # 3. Save Combined Data
    total_stops = existing_stops + new_stops
    
    output_data = {
        "metadata": {
            "source": "US DOT + OpenStreetMap",
            "dataset": "Comprehensive Nationwide Truck Parking",
            "total_records": len(total_stops),
            "last_updated": "2026-01"
        },
        "truck_stops": total_stops
    }
    
    with open(DOT_FILE, "w") as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Successfully saved {len(total_stops)} stops to {DOT_FILE}")

if __name__ == "__main__":
    fetch_nationwide()
