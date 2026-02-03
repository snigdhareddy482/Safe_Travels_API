"""
Crimeo Raw Data API Test

Calls the Raw Data endpoint for downtown Chicago,
prints a summary, and saves the full response as JSON.

Usage (from project root):
    python src/tests/test_crimeo_api.py
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# --------------- Config ---------------

# Load .env from project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("CRIMEO_API")
if not API_KEY:
    print("ERROR: CRIMEO_API not found in .env file.")
    sys.exit(1)

BASE_URL = "https://api.crimeometer.com/v1/incidents/raw-data"

# Downtown Chicago (The Loop)
LAT = "41.8781"
LON = "-87.6298"
DISTANCE = "2mi"

# 6-month lookback
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=180)
DATETIME_INI = START_DATE.strftime("%Y-%m-%dT00:00:00.000Z")
DATETIME_END = END_DATE.strftime("%Y-%m-%dT00:00:00.000Z")

OUTPUT_FILE = Path(__file__).resolve().parent / "crimeo_raw_data_chicago.json"

# --------------- Main ---------------

def main():
    print("=== Crimeo Raw Data API Test ===")
    print(f"Location: lat={LAT}, lon={LON} (Downtown Chicago)")
    print(f"Radius: {DISTANCE}")
    print(f"Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print()

    response = requests.get(
        BASE_URL,
        params={
            "lat": LAT,
            "lon": LON,
            "distance": DISTANCE,
            "datetime_ini": DATETIME_INI,
            "datetime_end": DATETIME_END,
            "page": 1,
        },
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        timeout=30,
    )

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response body: {response.text}")
        sys.exit(1)

    data = response.json()

    # API may return a list with one element or a dict directly
    result = data[0] if isinstance(data, list) else data

    total = result.get("total_incidents", 0)
    pages = result.get("total_pages", 0)
    incidents = result.get("incidents", [])

    print(f"Total incidents: {total}")
    print(f"Total pages: {pages}")
    print(f"Incidents on this page: {len(incidents)}")
    print()

    if incidents:
        # Crime type breakdown
        offense_counts = Counter(i.get("incident_offense", "Unknown") for i in incidents)
        print("Crime Type Breakdown:")
        for offense, count in offense_counts.most_common(10):
            print(f"  {offense}: {count}")
        print()

        # Category breakdown (Person / Property / Society)
        category_counts = Counter(i.get("incident_offense_crime_against", "Unknown") for i in incidents)
        print("Category Breakdown:")
        for cat, count in category_counts.most_common():
            print(f"  {cat}: {count}")
        print()

    # Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
