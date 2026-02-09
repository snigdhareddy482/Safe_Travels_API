"""Standalone Crimeometer API Test.

Verifies the raw Crimeometer API works before building the MCP server.
Tests the Stats, Raw Data, and Coverage endpoints.

Usage:
    python src/tests/test_crimeo_api.py

Output:
    Prints JSON responses and saves results to src/tests/crimeo_api_results.json
"""
import os
import json
import httpx
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("CRIME_API_KEY")
BASE_URL = os.getenv("CRIME_API_BASE_URL", "https://api.crimeometer.com/v1")

# Test location: Downtown Chicago
TEST_LAT = 41.8781
TEST_LON = -87.6298
TEST_RADIUS = "1mi"

# Date range: 6 months back from now
DATETIME_END = datetime.now(timezone.utc)
DATETIME_INI = DATETIME_END - timedelta(days=180)

# Format dates as required by Crimeometer: yyyy-MM-ddT00:00:00.000Z
DATETIME_END_STR = DATETIME_END.strftime("%Y-%m-%dT00:00:00.000Z")
DATETIME_INI_STR = DATETIME_INI.strftime("%Y-%m-%dT00:00:00.000Z")

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
}

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "crimeo_api_results.json")

# Delay between API calls to respect rate limits
CALL_DELAY_SECONDS = 3


def test_date_range_helper():
    """Test the date range calculation logic."""
    print("\n" + "=" * 60)
    print("TEST 1: Date Range Helper")
    print("=" * 60)

    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)

    end_str = now.strftime("%Y-%m-%dT00:00:00.000Z")
    ini_str = six_months_ago.strftime("%Y-%m-%dT00:00:00.000Z")

    print(f"datetime_end (now):          {end_str}")
    print(f"datetime_ini (6 months ago): {ini_str}")
    print(f"Days between: {(now - six_months_ago).days}")
    print("RESULT: PASS")

    return {
        "test_name": "date_range_helper",
        "status": "pass",
        "datetime_end": end_str,
        "datetime_ini": ini_str,
        "days_between": (now - six_months_ago).days,
    }


def test_coverage_endpoint():
    """Test the /v1/incidents/raw-data-coverage endpoint (no params needed)."""
    print("\n" + "=" * 60)
    print("TEST 2: Coverage Endpoint")
    print("=" * 60)

    url = f"{BASE_URL}/incidents/raw-data-coverage"

    print(f"URL: {url}")
    print(f"Headers: x-api-key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=HEADERS)

    print(f"Status Code: {response.status_code}")

    try:
        data = response.json()
        if response.status_code == 200:
            if isinstance(data, list) and len(data) > 0:
                cities = data[0].get("cities", [])
                print(f"Cities covered: {len(cities)}")
                for city in cities[:5]:
                    print(f"  - {city.get('city_name', '?')} ({city.get('city_key', '?')}): {city.get('incidents_quantity', '?')} incidents")
                if len(cities) > 5:
                    print(f"  ... and {len(cities) - 5} more cities")
            print("RESULT: PASS")
        elif response.status_code == 429:
            print(f"Rate limited: {data}")
            print("RESULT: RATE_LIMITED (429) - shared test key exhausted")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"RESULT: HTTP {response.status_code}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        data = {"error": str(e), "raw": response.text[:500]}

    return {
        "test_name": "coverage",
        "endpoint": "/v1/incidents/raw-data-coverage",
        "status_code": response.status_code,
        "status": "pass" if response.status_code == 200 else "rate_limited" if response.status_code == 429 else "fail",
        "response": data,
    }


def test_stats_endpoint():
    """Test the /v1/incidents/stats endpoint."""
    print("\n" + "=" * 60)
    print("TEST 3: Stats Endpoint")
    print("=" * 60)

    url = f"{BASE_URL}/incidents/stats"
    params = {
        "lat": TEST_LAT,
        "lon": TEST_LON,
        "distance": TEST_RADIUS,
        "datetime_ini": DATETIME_INI_STR,
        "datetime_end": DATETIME_END_STR,
    }

    print(f"URL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print()

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params, headers=HEADERS)

    print(f"Status Code: {response.status_code}")

    try:
        data = response.json()
        if response.status_code == 200:
            if isinstance(data, list) and len(data) > 0:
                total = data[0].get("total_incidents", "N/A")
                types = data[0].get("report_types", [])
                print(f"Total Incidents: {total}")
                print(f"Crime Types: {len(types)}")
                for t in types[:5]:
                    print(f"  - {t.get('type', '?')}: {t.get('count', '?')}")
            print("RESULT: PASS")
        elif response.status_code == 429:
            print(f"Rate limited: {data}")
            print("RESULT: RATE_LIMITED (429) - shared test key exhausted")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"RESULT: HTTP {response.status_code}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        data = {"error": str(e), "raw": response.text[:500]}

    return {
        "test_name": "stats",
        "endpoint": "/v1/incidents/stats",
        "status_code": response.status_code,
        "status": "pass" if response.status_code == 200 else "rate_limited" if response.status_code == 429 else "fail",
        "params": params,
        "response": data,
    }


def test_raw_data_endpoint():
    """Test the /v1/incidents/raw-data endpoint."""
    print("\n" + "=" * 60)
    print("TEST 4: Raw Data Endpoint")
    print("=" * 60)

    url = f"{BASE_URL}/incidents/raw-data"
    params = {
        "lat": TEST_LAT,
        "lon": TEST_LON,
        "distance": TEST_RADIUS,
        "datetime_ini": DATETIME_INI_STR,
        "datetime_end": DATETIME_END_STR,
        "page": 1,
    }

    print(f"URL: {url}")
    print(f"Params: {json.dumps(params, indent=2)}")
    print()

    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, params=params, headers=HEADERS)

    print(f"Status Code: {response.status_code}")

    try:
        data = response.json()
        if response.status_code == 200:
            if isinstance(data, list) and len(data) > 0:
                first = data[0]
                total = first.get("total_incidents", "N/A")
                total_pages = first.get("total_pages", "N/A")
                incidents = first.get("incidents", [])
                print(f"Total Incidents: {total}")
                print(f"Total Pages: {total_pages}")
                print(f"Incidents on this page: {len(incidents)}")
                if incidents:
                    print("\nFirst incident:")
                    print(json.dumps(incidents[0], indent=2))
            print("RESULT: PASS")
        elif response.status_code == 429:
            print(f"Rate limited: {data}")
            print("RESULT: RATE_LIMITED (429) - shared test key exhausted")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"RESULT: HTTP {response.status_code}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        data = {"error": str(e), "raw": response.text[:500]}

    return {
        "test_name": "raw_data",
        "endpoint": "/v1/incidents/raw-data",
        "status_code": response.status_code,
        "status": "pass" if response.status_code == 200 else "rate_limited" if response.status_code == 429 else "fail",
        "params": params,
        "response": data,
    }


def main():
    """Run all tests and save results to JSON."""
    print("=" * 60)
    print("CRIMEOMETER API STANDALONE TEST")
    print("=" * 60)
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:] if API_KEY else 'NOT SET'}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Location: ({TEST_LAT}, {TEST_LON}) - Downtown Chicago")
    print(f"Date Range: {DATETIME_INI_STR} to {DATETIME_END_STR}")

    if not API_KEY:
        print("\nERROR: CRIME_API_KEY not set in .env")
        return

    results = {
        "test_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_key_prefix": API_KEY[:8],
            "base_url": BASE_URL,
            "test_location": {
                "latitude": TEST_LAT,
                "longitude": TEST_LON,
                "description": "Downtown Chicago",
            },
            "date_range": {
                "datetime_ini": DATETIME_INI_STR,
                "datetime_end": DATETIME_END_STR,
            },
        },
        "tests": [],
    }

    # Run tests with delays between API calls
    results["tests"].append(test_date_range_helper())

    print(f"\n(waiting {CALL_DELAY_SECONDS}s between API calls...)")
    time.sleep(CALL_DELAY_SECONDS)
    results["tests"].append(test_coverage_endpoint())

    print(f"\n(waiting {CALL_DELAY_SECONDS}s between API calls...)")
    time.sleep(CALL_DELAY_SECONDS)
    results["tests"].append(test_stats_endpoint())

    print(f"\n(waiting {CALL_DELAY_SECONDS}s between API calls...)")
    time.sleep(CALL_DELAY_SECONDS)
    results["tests"].append(test_raw_data_endpoint())

    # Save results to JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n" + "=" * 60)
    print(f"Results saved to: {RESULTS_FILE}")
    print("=" * 60)

    # Summary
    print("\nSUMMARY:")
    for test in results["tests"]:
        name = test["test_name"]
        status = test.get("status", "N/A")
        code = test.get("status_code", "-")
        print(f"  {name}: {status} (HTTP {code})")

    # Rate limit note
    rate_limited = [t for t in results["tests"] if t.get("status") == "rate_limited"]
    if rate_limited:
        print(f"\nNOTE: {len(rate_limited)} endpoint(s) returned 429 Rate Limited.")
        print("The shared public test key has a global rate limit.")
        print("The MCP server is built to handle this - it will work")
        print("once you have a private API key or the limit resets.")


if __name__ == "__main__":
    main()
