# SafeTravels API Refactor Plan

> **MISSION**: Build a clean, elegant API that takes a start address and destination address, returns multiple routes with AI-generated crime risk scores (1-100) and summaries for each route.

---

## Core Principles

1. **KISS (Keep It Simple, Stupid)** - No excess code. Clean, readable, elegant.
2. **Research First** - Before each phase, deeply research to understand EXACTLY what will be implemented and HOW.
3. **Ask Questions** - ALWAYS ask clarifying questions before starting any major phase.
4. **Test to Verify** - Each phase has a corresponding test that MUST pass before moving to the next.
5. **Zero Context Execution** - This plan should be executable by someone with ZERO knowledge of the codebase.

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST                                   │
│                    POST /analyze-route                                   │
│                    {start: "123 Main St", destination: "456 Oak Ave"}   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     safe_travels_api.py (FastAPI)                        │
│                     - Receives POST request                              │
│                     - Calls safe_travels.py                              │
│                     - Returns JSON response                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     safe_travels.py (Orchestrator)                       │
│                     1. Call use_google_maps(start, destination)          │
│                     2. For each route, spawn agent in parallel           │
│                     3. Collect results, return to API                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
┌───────────────────────────┐   ┌───────────────────────────────────────┐
│  helper_functions/        │   │  safe_travels_agent.py                 │
│  google_maps.py           │   │  - PydanticAI Agent                    │
│                           │   │  - System prompt                       │
│  use_google_maps(         │   │  - Connected to Crime MCP Server       │
│    start: str,            │   │  - Output: {score: 1-100, summary: str}│
│    destination: str       │   │                                        │
│  ) -> List[RouteData]     │   └───────────────────────────────────────┘
└───────────────────────────┘                   │
                                               │
                                               ▼
                                ┌───────────────────────────────────────┐
                                │  MCP_Servers/crime_mcp/               │
                                │  - Streamable HTTP transport          │
                                │  - Tools for querying crime data      │
                                │  - Uses Crimeometer (or alternative)  │
                                └───────────────────────────────────────┘
```

---

## Final File Structure

```
src/
├── safe_travels.py              # Main orchestrator script
├── safe_travels_api.py          # FastAPI application
├── safe_travels_agent.py        # PydanticAI agent definition
├── helper_functions/
│   └── google_maps.py           # Google Maps API wrapper
├── MCP_Servers/
│   └── crime_mcp/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── config.py            # Settings (API keys, etc.)
│       ├── functions.py         # Crime API implementation
│       └── server.py            # FastMCP server definition
└── tests/
    ├── test_phase1_crime_mcp.py
    ├── test_phase2_google_maps.py
    ├── test_phase3_agent.py
    ├── test_phase4_orchestrator.py
    └── test_phase5_api.py
```

---

## Final API Response Format

```json
{
  "routes": [
    {
      "route_id": 1,
      "risk_score": 75,
      "risk_summary": "High crime corridor through downtown Chicago with elevated theft rates in areas near I-94. Multiple property crime incidents reported in the last 30 days along this route.",
      "status": "success"
    },
    {
      "route_id": 2,
      "risk_score": 42,
      "risk_summary": "Lower risk suburban route avoiding high-crime areas. Some minor incident reports near shopping centers but overall safer corridor.",
      "status": "success"
    },
    {
      "route_id": 3,
      "risk_score": null,
      "risk_summary": null,
      "status": "failed",
      "error": "Crime API timeout"
    }
  ]
}
```

---

# PHASE 1: Crime MCP Server

## Objective
Create an MCP server that provides crime data tools for the AI agent.

## Pre-Phase Research (REQUIRED)

Before writing ANY code, the implementer MUST:

### 1.1 Research Crime APIs

**Current Top Choice**: Crimeometer

**Research the following APIs and document findings**:
- **Crimeometer** (https://crimeometer.com/api-documentation)
  - Coverage: 30+ US cities (Austin, Chicago, Dallas, Houston, LA, Miami, etc.)
  - Endpoints: Raw Data, Stats, Crowdsourced Data
  - Parameters needed: lat/lng, datetime_ini, datetime_end, distance (radius)

- **SpotCrime** (https://spotcrime.com/api)
  - Check coverage and pricing

- **CrimeMapping** (https://www.crimemapping.com/api)
  - Check coverage and pricing

- **FBI UCR API** (https://crime-data-explorer.fr.cloud.gov/api)
  - Free, but aggregated annual data (not real-time)

**Questions to answer during research**:
1. Which API has the best coverage for our target cities?
2. What are the rate limits?
3. What parameters does each endpoint accept?
4. How is the data structured in responses?
5. What's the pricing model?

**Document your findings in**: `src/MCP_Servers/crime_mcp/API_RESEARCH.md`

### 1.2 Study Reference Materials

Read and understand these files thoroughly:

1. **MCP Server Boilerplate**: `docs/Search_MCP/src/Example_MCP/`
   - `server.py` - How to define MCP tools with FastMCP
   - `config.py` - How to use pydantic-settings for configuration
   - `functions.py` - How to implement tool logic separately

2. **Existing MCP Server**: `safetravels/mcp/server.py`
   - Follow this structure as closely as possible
   - Note how tools are decorated with `@mcp.tool()`
   - Note the docstrings format (the LLM reads these!)

3. **Crimeometer Documentation**: `docs/crime_platform/crimeo_docs.md`
   - Understand the available endpoints
   - Note the FBI-NIBRS standard for offense types

## Implementation Steps

### Step 1.1: Create Directory Structure

```bash
mkdir -p src/MCP_Servers/crime_mcp
touch src/MCP_Servers/crime_mcp/__init__.py
touch src/MCP_Servers/crime_mcp/__main__.py
touch src/MCP_Servers/crime_mcp/config.py
touch src/MCP_Servers/crime_mcp/functions.py
touch src/MCP_Servers/crime_mcp/server.py
```

### Step 1.2: Create config.py

```python
"""Crime MCP Server Configuration.

Environment variables:
- CRIME_API_KEY: API key for the crime data provider
- CRIME_API_BASE_URL: Base URL for the API (default based on provider)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class CrimeMCPSettings(BaseSettings):
    """Settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )

    CRIME_API_KEY: str
    CRIME_API_BASE_URL: str = "https://api.crimeometer.com/v1"
```

### Step 1.3: Create functions.py

Implement the actual crime API calls. Based on research, you'll likely need:

```python
"""Crime API implementation functions.

This file contains the actual logic for calling crime APIs.
Keep business logic separate from the MCP server definition.
"""
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


async def get_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float = 1.0,
    days_back: int = 30,
    api_key: str = "",
    base_url: str = ""
) -> Dict[str, Any]:
    """
    Get crime statistics for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        radius_miles: Search radius in miles
        days_back: Number of days to look back
        api_key: Crime API key
        base_url: Crime API base URL

    Returns:
        Dictionary with crime statistics
    """
    # Implementation depends on chosen API
    # See Crimeometer Stats endpoint documentation
    pass


async def get_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float = 1.0,
    days_back: int = 30,
    api_key: str = "",
    base_url: str = ""
) -> List[Dict[str, Any]]:
    """
    Get raw crime incident data for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        radius_miles: Search radius in miles
        days_back: Number of days to look back
        api_key: Crime API key
        base_url: Crime API base URL

    Returns:
        List of crime incidents
    """
    # Implementation depends on chosen API
    # See Crimeometer Raw Data endpoint documentation
    pass
```

### Step 1.4: Create server.py

```python
"""Crime MCP Server.

Provides crime data tools for AI agents to analyze route safety.

Running the Server:
    python -m src.MCP_Servers.crime_mcp
"""
import logging
import sys
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastmcp import FastMCP

from .config import CrimeMCPSettings
from .functions import get_crime_stats, get_crime_incidents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("crime-mcp")

# Global HTTP client
http_client: Optional[httpx.AsyncClient] = None

# Load settings
settings = CrimeMCPSettings()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    """Lifecycle manager for the MCP server."""
    global http_client

    logger.info("Crime MCP server starting...")
    http_client = httpx.AsyncClient(timeout=30.0)

    yield

    logger.info("Crime MCP server shutting down...")
    if http_client and not http_client.is_closed:
        await http_client.aclose()
        http_client = None


# Initialize MCP server
mcp = FastMCP(
    name="crime-analysis",
    instructions=(
        "Crime data analysis tools for route safety assessment. "
        "Use these tools to query crime statistics and incidents "
        "at specific locations along a route."
    ),
    lifespan=lifespan
)


@mcp.tool(
    description=(
        "Get crime statistics for a specific location. "
        "Returns total incidents and breakdown by crime type. "
        "Use this to assess the overall crime level at a point along a route."
    )
)
async def get_location_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float = 1.0,
    days_back: int = 30
) -> dict:
    """
    Query crime statistics for a geographic location.

    Args:
        latitude: GPS latitude of the location
        longitude: GPS longitude of the location
        radius_miles: Search radius in miles (default: 1.0)
        days_back: Number of days to look back (default: 30)

    Returns:
        Dictionary containing:
        - total_incidents: Total crime count
        - by_type: Breakdown by offense type
        - location: Queried coordinates
    """
    try:
        result = await get_crime_stats(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            days_back=days_back,
            api_key=settings.CRIME_API_KEY,
            base_url=settings.CRIME_API_BASE_URL
        )
        return result
    except Exception as e:
        logger.error(f"Crime stats error: {e}")
        return {"error": str(e)}


@mcp.tool(
    description=(
        "Get detailed crime incident data for a location. "
        "Returns individual crime reports with offense types, dates, and descriptions. "
        "Use this for deeper analysis of specific areas."
    )
)
async def get_location_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float = 0.5,
    days_back: int = 30,
    limit: int = 50
) -> dict:
    """
    Query raw crime incident data for a location.

    Args:
        latitude: GPS latitude of the location
        longitude: GPS longitude of the location
        radius_miles: Search radius in miles (default: 0.5)
        days_back: Number of days to look back (default: 30)
        limit: Maximum incidents to return (default: 50)

    Returns:
        Dictionary containing:
        - incidents: List of crime incidents
        - count: Number of incidents returned
        - location: Queried coordinates
    """
    try:
        incidents = await get_crime_incidents(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            days_back=days_back,
            api_key=settings.CRIME_API_KEY,
            base_url=settings.CRIME_API_BASE_URL
        )
        return {
            "incidents": incidents[:limit],
            "count": len(incidents[:limit]),
            "location": {"lat": latitude, "lon": longitude}
        }
    except Exception as e:
        logger.error(f"Crime incidents error: {e}")
        return {"error": str(e)}


def run_server():
    """Start the MCP server."""
    logger.info("Starting Crime MCP server on port 8001...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8001,
        path="/mcp",
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
```

### Step 1.5: Create __main__.py

```python
"""Entry point for running the Crime MCP server."""
from .server import run_server

if __name__ == "__main__":
    run_server()
```

## Phase 1 Test

Create `src/tests/test_phase1_crime_mcp.py`:

```python
"""Phase 1 Test: Crime MCP Server.

This test verifies that:
1. The MCP server starts successfully
2. Tools are accessible via HTTP
3. Crime data queries return valid responses
"""
import pytest
import httpx
import asyncio
import subprocess
import time
import signal
import os


# Server configuration
MCP_URL = "http://localhost:8001/mcp"
TIMEOUT = 30.0


@pytest.fixture(scope="module")
def mcp_server():
    """Start the MCP server for testing."""
    # Start server as subprocess
    env = os.environ.copy()
    env["CRIME_API_KEY"] = os.getenv("CRIME_API_KEY", "test-key")

    process = subprocess.Popen(
        ["python", "-m", "src.MCP_Servers.crime_mcp"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(3)

    yield process

    # Cleanup
    process.send_signal(signal.SIGTERM)
    process.wait(timeout=5)


@pytest.mark.asyncio
async def test_server_health(mcp_server):
    """Test that the server is running and responding."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # MCP servers respond to tool listing
        response = await client.post(
            MCP_URL,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data or "tools" in data


@pytest.mark.asyncio
async def test_crime_stats_tool(mcp_server):
    """Test the get_location_crime_stats tool."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Call the crime stats tool
        response = await client.post(
            MCP_URL,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_location_crime_stats",
                    "arguments": {
                        "latitude": 41.8781,
                        "longitude": -87.6298,
                        "radius_miles": 1.0,
                        "days_back": 30
                    }
                },
                "id": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should have result or error (both are valid responses)
        assert "result" in data or "error" in data


@pytest.mark.asyncio
async def test_crime_incidents_tool(mcp_server):
    """Test the get_location_crime_incidents tool."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            MCP_URL,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get_location_crime_incidents",
                    "arguments": {
                        "latitude": 41.8781,
                        "longitude": -87.6298,
                        "radius_miles": 0.5,
                        "days_back": 30
                    }
                },
                "id": 3
            }
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Phase 1 Completion Criteria

- [ ] MCP server starts without errors
- [ ] Server accessible at `http://localhost:8001/mcp`
- [ ] `tools/list` returns available tools
- [ ] `get_location_crime_stats` tool callable via HTTP
- [ ] `get_location_crime_incidents` tool callable via HTTP
- [ ] All tests in `test_phase1_crime_mcp.py` pass

---

# PHASE 2: Google Maps Helper Function

## Objective
Create a function that takes start and destination addresses, returns route data including waypoints needed for crime analysis.

## Pre-Phase Research (REQUIRED)

### 2.1 Study Google Maps Services

Read these files thoroughly:

1. **Python Client**: `google-maps-services-python/`
   - `googlemaps/directions.py` - Directions API
   - `googlemaps/geocoding.py` - Geocoding and reverse geocoding
   - `googlemaps/client.py` - How to initialize the client

2. **Key Parameters**:
   - `alternatives=True` - Returns multiple route options
   - `mode="driving"` - Vehicle routing
   - Route response includes: legs, steps, polyline, duration, distance

### 2.2 Understand What Crime MCP Needs

The crime tools need coordinates (lat/lng). The Google Maps function must extract:
- Route polyline (encoded path)
- Waypoints at intervals for crime queries
- Cities/areas the route passes through

### 2.3 Plan the Data Extraction

For a route, we need to extract points at regular intervals (e.g., every 5 miles or at population centers) for crime analysis. Consider:
- Decode the polyline to get coordinate points
- Sample points at reasonable intervals
- Use reverse geocoding to get city names (optional, for summary)

## Implementation Steps

### Step 2.1: Install Dependencies

```bash
pip install googlemaps polyline
```

### Step 2.2: Create google_maps.py

```python
"""Google Maps helper functions.

Provides route data extraction for crime analysis.
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import googlemaps
import polyline as polyline_lib
from math import radians, sin, cos, sqrt, atan2


# Initialize Google Maps client
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


@dataclass
class RoutePoint:
    """A point along a route."""
    latitude: float
    longitude: float
    description: Optional[str] = None  # City name or area


@dataclass
class RouteData:
    """Complete route data for crime analysis."""
    route_id: int
    summary: str  # e.g., "I-90 W"
    distance_miles: float
    duration_minutes: int
    start_address: str
    end_address: str
    waypoints: List[RoutePoint]  # Points for crime analysis
    polyline: str  # Encoded polyline


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def sample_points_from_polyline(
    encoded_polyline: str,
    interval_miles: float = 5.0
) -> List[RoutePoint]:
    """
    Extract waypoints from a polyline at regular intervals.

    Args:
        encoded_polyline: Google's encoded polyline string
        interval_miles: Distance between sample points

    Returns:
        List of RoutePoint objects
    """
    # Decode the polyline
    coords = polyline_lib.decode(encoded_polyline)

    if not coords:
        return []

    waypoints = [RoutePoint(latitude=coords[0][0], longitude=coords[0][1])]
    accumulated_distance = 0.0

    for i in range(1, len(coords)):
        prev_lat, prev_lon = coords[i-1]
        curr_lat, curr_lon = coords[i]

        segment_distance = haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
        accumulated_distance += segment_distance

        # Add point if we've traveled far enough
        if accumulated_distance >= interval_miles:
            waypoints.append(RoutePoint(latitude=curr_lat, longitude=curr_lon))
            accumulated_distance = 0.0

    # Always include the final point
    if len(coords) > 1:
        final = coords[-1]
        if waypoints[-1].latitude != final[0] or waypoints[-1].longitude != final[1]:
            waypoints.append(RoutePoint(latitude=final[0], longitude=final[1]))

    return waypoints


def use_google_maps(start: str, destination: str) -> List[RouteData]:
    """
    Get route alternatives between two addresses with waypoints for crime analysis.

    Args:
        start: Starting address (e.g., "123 Main St, Chicago, IL")
        destination: Destination address (e.g., "456 Oak Ave, Chicago, IL")

    Returns:
        List of RouteData objects, one per route alternative
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    # Get directions with alternatives
    directions_result = gmaps.directions(
        origin=start,
        destination=destination,
        mode="driving",
        alternatives=True  # Request multiple routes
    )

    routes = []

    for idx, route in enumerate(directions_result):
        # Extract basic info
        leg = route["legs"][0]  # Single leg for direct A to B

        # Get distance and duration
        distance_meters = leg["distance"]["value"]
        distance_miles = distance_meters / 1609.34

        duration_seconds = leg["duration"]["value"]
        duration_minutes = duration_seconds // 60

        # Get the overview polyline
        overview_polyline = route["overview_polyline"]["points"]

        # Sample waypoints for crime analysis
        # For urban routes (~1 hour), sample every 2-3 miles
        interval = 3.0 if distance_miles < 30 else 5.0
        waypoints = sample_points_from_polyline(overview_polyline, interval_miles=interval)

        route_data = RouteData(
            route_id=idx + 1,
            summary=route.get("summary", f"Route {idx + 1}"),
            distance_miles=round(distance_miles, 1),
            duration_minutes=int(duration_minutes),
            start_address=leg["start_address"],
            end_address=leg["end_address"],
            waypoints=waypoints,
            polyline=overview_polyline
        )

        routes.append(route_data)

    return routes


# Optional: Add reverse geocoding for waypoint descriptions
def enrich_waypoints_with_locations(
    routes: List[RouteData],
    gmaps_client: googlemaps.Client
) -> List[RouteData]:
    """
    Add city/area descriptions to waypoints via reverse geocoding.

    Note: This makes additional API calls. Use sparingly to avoid rate limits.
    """
    for route in routes:
        for waypoint in route.waypoints:
            try:
                result = gmaps_client.reverse_geocode(
                    (waypoint.latitude, waypoint.longitude),
                    result_type=["locality", "administrative_area_level_2"]
                )
                if result:
                    # Extract city name
                    for component in result[0].get("address_components", []):
                        if "locality" in component.get("types", []):
                            waypoint.description = component["long_name"]
                            break
            except Exception:
                pass  # Continue without description

    return routes
```

## Phase 2 Test

Create `src/tests/test_phase2_google_maps.py`:

```python
"""Phase 2 Test: Google Maps Helper Function.

This test verifies that:
1. use_google_maps returns valid route data
2. Multiple route alternatives are returned
3. Waypoints are properly extracted
4. Data structure matches expected format
"""
import pytest
import os
from src.helper_functions.google_maps import (
    use_google_maps,
    sample_points_from_polyline,
    RouteData,
    RoutePoint
)


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_MAPS_API_KEY"),
    reason="GOOGLE_MAPS_API_KEY not set"
)


def test_use_google_maps_returns_routes():
    """Test that use_google_maps returns a list of routes."""
    routes = use_google_maps(
        start="Willis Tower, Chicago, IL",
        destination="Navy Pier, Chicago, IL"
    )

    assert isinstance(routes, list)
    assert len(routes) >= 1


def test_route_data_structure():
    """Test that route data has all required fields."""
    routes = use_google_maps(
        start="Union Station, Chicago, IL",
        destination="O'Hare Airport, Chicago, IL"
    )

    route = routes[0]

    assert isinstance(route, RouteData)
    assert route.route_id >= 1
    assert route.distance_miles > 0
    assert route.duration_minutes > 0
    assert len(route.waypoints) >= 2  # At least start and end
    assert route.polyline  # Non-empty polyline


def test_waypoints_have_coordinates():
    """Test that waypoints have valid coordinates."""
    routes = use_google_maps(
        start="Millennium Park, Chicago, IL",
        destination="Lincoln Park Zoo, Chicago, IL"
    )

    for route in routes:
        for waypoint in route.waypoints:
            assert isinstance(waypoint, RoutePoint)
            assert -90 <= waypoint.latitude <= 90
            assert -180 <= waypoint.longitude <= 180


def test_polyline_sampling():
    """Test that polyline sampling produces reasonable waypoints."""
    # Sample encoded polyline (Chicago area)
    test_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

    waypoints = sample_points_from_polyline(test_polyline, interval_miles=1.0)

    assert len(waypoints) >= 1
    assert all(isinstance(wp, RoutePoint) for wp in waypoints)


def test_multiple_alternatives():
    """Test that alternatives are returned for routes with options."""
    routes = use_google_maps(
        start="Downtown Chicago, IL",
        destination="Evanston, IL"
    )

    # Should get at least 1 route, possibly more
    assert len(routes) >= 1

    # Each route should have unique ID
    route_ids = [r.route_id for r in routes]
    assert len(route_ids) == len(set(route_ids))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Phase 2 Completion Criteria

- [ ] `use_google_maps()` function implemented
- [ ] Returns list of `RouteData` objects
- [ ] Each route has waypoints with lat/lng coordinates
- [ ] Polyline is decoded and sampled correctly
- [ ] All tests in `test_phase2_google_maps.py` pass

---

# PHASE 3: SafeTravels AI Agent

## Objective
Create a PydanticAI agent that connects to the Crime MCP server and analyzes route safety.

## Pre-Phase Research (REQUIRED)

### 3.1 Study PydanticAI Thoroughly

**CRITICAL**: Read these files in order:

1. **Agent Reference** (`docs/agent_zero.py`):
   - This is the PRIMARY reference for implementation
   - Shows how to connect to MCP servers with `MCPServerStreamableHTTP`
   - Shows the AgentZero class pattern
   - Shows async query method

2. **Basic Agent Example** (`docs/Pydantic_AI/agent.py`):
   - Simple MCP connection example
   - Chat loop pattern

3. **PydanticAI Agents Documentation** (`docs/Pydantic_AI/pydantic_ai_docs/agents.md`):
   - System prompts (static and dynamic)
   - Running agents (run, run_sync, run_stream)
   - Model settings

4. **Output Types** (`docs/Pydantic_AI/pydantic_ai_docs/output.md`):
   - How to define structured output types
   - Pydantic models as output_type
   - Output validation

5. **MCP Client** (`docs/Pydantic_AI/pydantic_ai_docs/mcp_client.md`):
   - `MCPServerStreamableHTTP` usage
   - `agent.run_mcp_servers()` context manager

### 3.2 Understand the Agent's Task

The agent will:
1. Receive route data (waypoints with coordinates)
2. Make MULTIPLE calls to the Crime MCP server (one per waypoint)
3. Analyze the crime data holistically
4. Return a score (1-100) and summary

### 3.3 Design the System Prompt

The system prompt is CRITICAL. It must tell the agent:
- Its purpose (route safety analyst)
- How to use the crime tools (query each waypoint)
- How to interpret crime data
- How to calculate the final score
- How to write the summary

## Implementation Steps

### Step 3.1: Create Output Types

```python
"""Agent output types."""
from pydantic import BaseModel, Field


class RouteAnalysisResult(BaseModel):
    """Structured output from the route analysis agent."""

    risk_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Risk score from 1 (safest) to 100 (most dangerous)"
    )
    risk_summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Detailed summary explaining the risk assessment"
    )
```

### Step 3.2: Create the Agent

Create `src/safe_travels_agent.py`:

```python
"""SafeTravels Route Analysis Agent.

A PydanticAI agent that analyzes route safety using crime data.
"""
import os
import logging
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStreamableHTTP

# Load environment
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# OUTPUT TYPES
# =============================================================================

class RouteAnalysisResult(BaseModel):
    """Structured output from the route analysis agent."""

    risk_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Risk score from 1 (safest) to 100 (most dangerous)"
    )
    risk_summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Detailed summary explaining the risk assessment"
    )


# =============================================================================
# AGENT INPUT
# =============================================================================

@dataclass
class RouteAnalysisInput:
    """Input data for route analysis."""
    route_id: int
    summary: str
    distance_miles: float
    duration_minutes: int
    waypoints: List[dict]  # List of {"latitude": float, "longitude": float}


# =============================================================================
# CONFIGURATION
# =============================================================================

# LLM Configuration (via OpenRouter)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

# MCP Server URL
CRIME_MCP_URL = os.getenv("CRIME_MCP_URL", "http://localhost:8001/mcp")

# Initialize model
model = OpenAIModel(
    LLM_MODEL,
    provider=OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    ),
)

# Initialize MCP server connection
crime_mcp = MCPServerStreamableHTTP(url=CRIME_MCP_URL)


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a Route Safety Analyst AI specializing in crime risk assessment for travel routes.

## YOUR MISSION
Analyze a driving route and provide a crime risk score (1-100) with a detailed summary.

## SCORING SCALE
- 1-20: Very Safe - Minimal crime activity, safe at any time
- 21-40: Safe - Low crime, normal precautions advised
- 41-60: Moderate Risk - Some crime activity, stay aware of surroundings
- 61-80: High Risk - Significant crime, avoid stopping in this area if possible
- 81-100: Very High Risk - High crime concentration, strongly consider alternative routes

## HOW TO ANALYZE A ROUTE

You will receive route data including waypoints (coordinates along the route).

1. **Query Crime Data**: For EACH waypoint provided, use the `get_location_crime_stats` tool to get crime statistics. This is CRITICAL - you must query multiple points to get a complete picture.

2. **Aggregate Findings**: After querying all waypoints:
   - Count total incidents across the route
   - Identify crime types (property crime, violent crime, theft, etc.)
   - Note any high-crime "hotspots"

3. **Calculate Score**: Base your score on:
   - Total crime volume relative to route length
   - Severity of crimes (violent > property > minor)
   - Concentration (spread out vs hotspots)
   - Recent trends (if available)

4. **Write Summary**: Your summary MUST include:
   - Overall assessment in one sentence
   - Key risk areas (if any)
   - Types of crimes most common
   - Specific recommendations

## IMPORTANT RULES
- ALWAYS query crime data for AT LEAST 3-5 waypoints along the route
- If a tool call fails, note it but continue with available data
- Never fabricate crime data - only use what the tools return
- Be specific about locations and crime types in your summary
- Keep the summary concise but informative (100-300 words ideal)

## EXAMPLE OUTPUT
Risk Score: 65
Summary: This route through downtown Chicago presents moderate-to-high risk primarily due to elevated property crime rates in the Loop and Near West Side areas. Crime data shows 47 incidents within the last 30 days along this corridor, with motor vehicle theft (32%) and larceny (28%) being most prevalent. The highest concentration appears near the intersection of State and Madison. Consider avoiding extended stops in this area, especially during evening hours. The suburban portions of the route show significantly lower crime rates.
"""


# =============================================================================
# AGENT DEFINITION
# =============================================================================

agent = Agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    output_type=RouteAnalysisResult,
    mcp_servers=[crime_mcp],
    retries=2,
)


# =============================================================================
# AGENT CLASS
# =============================================================================

class SafeTravelsAgent:
    """
    SafeTravels Route Analysis Agent.

    Analyzes route safety using crime data from MCP tools.
    """

    def __init__(self):
        """Initialize the agent."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPEN_ROUTER_API_KEY environment variable not set")

    async def analyze_route(
        self,
        route_input: RouteAnalysisInput
    ) -> dict:
        """
        Analyze a route for crime risk.

        Args:
            route_input: RouteAnalysisInput with route data

        Returns:
            Dictionary with risk_score, risk_summary, and status
        """
        # Format the prompt with route data
        waypoint_list = "\n".join([
            f"  - Point {i+1}: ({wp['latitude']:.6f}, {wp['longitude']:.6f})"
            for i, wp in enumerate(route_input.waypoints)
        ])

        prompt = f"""Analyze the following route for crime risk:

Route: {route_input.summary}
Distance: {route_input.distance_miles} miles
Duration: {route_input.duration_minutes} minutes

Waypoints to analyze:
{waypoint_list}

Please query crime data for these waypoints and provide your risk assessment."""

        try:
            # Run the agent with MCP servers
            async with agent.run_mcp_servers():
                result = await agent.run(prompt)

                return {
                    "route_id": route_input.route_id,
                    "risk_score": result.output.risk_score,
                    "risk_summary": result.output.risk_summary,
                    "status": "success"
                }
        except Exception as e:
            logger.exception(f"Route analysis failed: {e}")
            return {
                "route_id": route_input.route_id,
                "risk_score": None,
                "risk_summary": None,
                "status": "failed",
                "error": str(e)
            }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def analyze_single_route(route_data: dict) -> dict:
    """
    Convenience function to analyze a single route.

    Args:
        route_data: Dictionary with route_id, summary, distance_miles,
                   duration_minutes, and waypoints

    Returns:
        Analysis result dictionary
    """
    agent_instance = SafeTravelsAgent()

    input_data = RouteAnalysisInput(
        route_id=route_data["route_id"],
        summary=route_data["summary"],
        distance_miles=route_data["distance_miles"],
        duration_minutes=route_data["duration_minutes"],
        waypoints=route_data["waypoints"]
    )

    return await agent_instance.analyze_route(input_data)
```

## Phase 3 Test

Create `src/tests/test_phase3_agent.py`:

```python
"""Phase 3 Test: SafeTravels AI Agent.

This test verifies that:
1. Agent initializes correctly
2. Agent connects to Crime MCP server
3. Agent returns properly structured output
4. Output validation works (score 1-100, summary present)
"""
import pytest
import asyncio
import os
from src.safe_travels_agent import (
    SafeTravelsAgent,
    RouteAnalysisInput,
    RouteAnalysisResult,
    analyze_single_route
)


# Skip if required env vars not set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPEN_ROUTER_API_KEY"),
    reason="OPEN_ROUTER_API_KEY not set"
)


# Sample route data for testing
SAMPLE_ROUTE = {
    "route_id": 1,
    "summary": "Test Route - Downtown Chicago",
    "distance_miles": 5.2,
    "duration_minutes": 15,
    "waypoints": [
        {"latitude": 41.8781, "longitude": -87.6298},  # Downtown Chicago
        {"latitude": 41.8827, "longitude": -87.6233},  # Near Millennium Park
        {"latitude": 41.8902, "longitude": -87.6172},  # Near Navy Pier
    ]
}


@pytest.fixture
def agent():
    """Create agent instance."""
    return SafeTravelsAgent()


def test_agent_initialization():
    """Test that agent initializes without errors."""
    agent = SafeTravelsAgent()
    assert agent is not None


@pytest.mark.asyncio
async def test_analyze_route_returns_dict(agent):
    """Test that analyze_route returns a dictionary."""
    input_data = RouteAnalysisInput(**SAMPLE_ROUTE)
    result = await agent.analyze_route(input_data)

    assert isinstance(result, dict)
    assert "route_id" in result
    assert "status" in result


@pytest.mark.asyncio
async def test_successful_analysis_structure(agent):
    """Test that successful analysis has correct structure."""
    input_data = RouteAnalysisInput(**SAMPLE_ROUTE)
    result = await agent.analyze_route(input_data)

    if result["status"] == "success":
        assert "risk_score" in result
        assert "risk_summary" in result
        assert 1 <= result["risk_score"] <= 100
        assert len(result["risk_summary"]) >= 50


@pytest.mark.asyncio
async def test_output_type_validation():
    """Test that RouteAnalysisResult validates correctly."""
    # Valid result
    valid = RouteAnalysisResult(
        risk_score=65,
        risk_summary="This is a moderately risky route due to several factors that increase the overall danger level."
    )
    assert valid.risk_score == 65

    # Invalid score (out of range)
    with pytest.raises(ValueError):
        RouteAnalysisResult(risk_score=150, risk_summary="Too high score")

    # Invalid summary (too short)
    with pytest.raises(ValueError):
        RouteAnalysisResult(risk_score=50, risk_summary="Short")


@pytest.mark.asyncio
async def test_convenience_function():
    """Test the analyze_single_route convenience function."""
    result = await analyze_single_route(SAMPLE_ROUTE)

    assert isinstance(result, dict)
    assert result["route_id"] == SAMPLE_ROUTE["route_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Phase 3 Completion Criteria

- [ ] `SafeTravelsAgent` class implemented
- [ ] Agent connects to Crime MCP server
- [ ] Agent uses `output_type=RouteAnalysisResult` for structured output
- [ ] System prompt is comprehensive and clear
- [ ] `analyze_route()` returns properly structured results
- [ ] All tests in `test_phase3_agent.py` pass

---

# PHASE 4: Orchestrator Script

## Objective
Create `safe_travels.py` that coordinates Google Maps and parallel agent calls.

## Pre-Phase Research (REQUIRED)

### 4.1 Study Python Async Patterns

Understand:
- `asyncio.gather()` for parallel execution
- Error handling with `return_exceptions=True`
- Timeout handling

### 4.2 Plan the Flow

```
1. Receive start and destination addresses
2. Call use_google_maps() to get routes
3. For each route, prepare agent input
4. Run all agent analyses in parallel
5. Collect results (including partial failures)
6. Return consolidated response
```

## Implementation Steps

Create `src/safe_travels.py`:

```python
"""SafeTravels Route Analysis Orchestrator.

Coordinates Google Maps routing and parallel crime analysis.
"""
import asyncio
import logging
from typing import List, Dict, Any
from dataclasses import asdict

from src.helper_functions.google_maps import use_google_maps, RouteData
from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_route_with_timeout(
    agent: SafeTravelsAgent,
    route_input: RouteAnalysisInput,
    timeout_seconds: float = 60.0
) -> Dict[str, Any]:
    """
    Analyze a route with timeout protection.

    Args:
        agent: SafeTravelsAgent instance
        route_input: Route data to analyze
        timeout_seconds: Maximum time to wait

    Returns:
        Analysis result dictionary
    """
    try:
        result = await asyncio.wait_for(
            agent.analyze_route(route_input),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Route {route_input.route_id} analysis timed out")
        return {
            "route_id": route_input.route_id,
            "risk_score": None,
            "risk_summary": None,
            "status": "failed",
            "error": "Analysis timed out"
        }
    except Exception as e:
        logger.exception(f"Route {route_input.route_id} analysis failed")
        return {
            "route_id": route_input.route_id,
            "risk_score": None,
            "risk_summary": None,
            "status": "failed",
            "error": str(e)
        }


def route_data_to_input(route: RouteData) -> RouteAnalysisInput:
    """Convert RouteData to RouteAnalysisInput."""
    return RouteAnalysisInput(
        route_id=route.route_id,
        summary=route.summary,
        distance_miles=route.distance_miles,
        duration_minutes=route.duration_minutes,
        waypoints=[
            {"latitude": wp.latitude, "longitude": wp.longitude}
            for wp in route.waypoints
        ]
    )


async def analyze_routes(
    start: str,
    destination: str,
    timeout_per_route: float = 60.0
) -> Dict[str, Any]:
    """
    Analyze all routes between start and destination.

    This is the main orchestration function that:
    1. Gets routes from Google Maps
    2. Runs parallel agent analyses
    3. Returns consolidated results

    Args:
        start: Starting address
        destination: Destination address
        timeout_per_route: Max seconds per route analysis

    Returns:
        Dictionary with routes list and metadata
    """
    logger.info(f"Analyzing routes from '{start}' to '{destination}'")

    # Step 1: Get routes from Google Maps
    try:
        routes = use_google_maps(start, destination)
        logger.info(f"Found {len(routes)} route alternatives")
    except Exception as e:
        logger.exception("Google Maps API failed")
        return {
            "routes": [],
            "error": f"Failed to get routes: {str(e)}",
            "status": "failed"
        }

    if not routes:
        return {
            "routes": [],
            "error": "No routes found between locations",
            "status": "failed"
        }

    # Step 2: Prepare agent inputs
    agent = SafeTravelsAgent()
    inputs = [route_data_to_input(route) for route in routes]

    # Step 3: Run analyses in parallel
    logger.info(f"Starting parallel analysis of {len(inputs)} routes")

    tasks = [
        analyze_route_with_timeout(agent, route_input, timeout_per_route)
        for route_input in inputs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Step 4: Process results
    successful = sum(1 for r in results if r.get("status") == "success")
    logger.info(f"Analysis complete: {successful}/{len(results)} routes succeeded")

    return {
        "routes": results,
        "total_routes": len(results),
        "successful_analyses": successful,
        "status": "success" if successful > 0 else "partial_failure"
    }


# =============================================================================
# SYNCHRONOUS WRAPPER
# =============================================================================

def analyze_routes_sync(start: str, destination: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for analyze_routes.

    Use this when not in an async context.
    """
    return asyncio.run(analyze_routes(start, destination))


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python safe_travels.py <start_address> <destination_address>")
        print("Example: python safe_travels.py 'Willis Tower, Chicago' 'Navy Pier, Chicago'")
        sys.exit(1)

    start_addr = sys.argv[1]
    dest_addr = sys.argv[2]

    print(f"Analyzing routes from '{start_addr}' to '{dest_addr}'...")

    result = analyze_routes_sync(start_addr, dest_addr)

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(json.dumps(result, indent=2))
```

## Phase 4 Test

Create `src/tests/test_phase4_orchestrator.py`:

```python
"""Phase 4 Test: Orchestrator Script.

This test verifies that:
1. analyze_routes coordinates Google Maps and agent correctly
2. Parallel execution works
3. Partial failures are handled gracefully
4. Results are properly structured
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from src.safe_travels import (
    analyze_routes,
    analyze_routes_sync,
    route_data_to_input,
    analyze_route_with_timeout
)
from src.helper_functions.google_maps import RouteData, RoutePoint
from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput


# Skip if required env vars not set
pytestmark = pytest.mark.skipif(
    not (os.getenv("GOOGLE_MAPS_API_KEY") and os.getenv("OPEN_ROUTER_API_KEY")),
    reason="Required API keys not set"
)


def create_mock_route(route_id: int = 1) -> RouteData:
    """Create a mock RouteData for testing."""
    return RouteData(
        route_id=route_id,
        summary=f"Test Route {route_id}",
        distance_miles=5.0,
        duration_minutes=15,
        start_address="Start Address",
        end_address="End Address",
        waypoints=[
            RoutePoint(latitude=41.8781, longitude=-87.6298),
            RoutePoint(latitude=41.8827, longitude=-87.6233),
        ],
        polyline="test_polyline"
    )


def test_route_data_to_input():
    """Test conversion from RouteData to RouteAnalysisInput."""
    route = create_mock_route()
    input_data = route_data_to_input(route)

    assert isinstance(input_data, RouteAnalysisInput)
    assert input_data.route_id == route.route_id
    assert input_data.summary == route.summary
    assert len(input_data.waypoints) == len(route.waypoints)


@pytest.mark.asyncio
async def test_analyze_route_with_timeout_handles_timeout():
    """Test that timeout is handled gracefully."""
    agent = Mock(spec=SafeTravelsAgent)

    async def slow_analysis(*args, **kwargs):
        await asyncio.sleep(10)  # Longer than timeout
        return {"status": "success"}

    agent.analyze_route = slow_analysis

    input_data = RouteAnalysisInput(
        route_id=1,
        summary="Test",
        distance_miles=5.0,
        duration_minutes=15,
        waypoints=[{"latitude": 41.0, "longitude": -87.0}]
    )

    result = await analyze_route_with_timeout(agent, input_data, timeout_seconds=0.1)

    assert result["status"] == "failed"
    assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_analyze_routes_returns_structure():
    """Test that analyze_routes returns proper structure."""
    # This is an integration test - requires live APIs
    result = await analyze_routes(
        start="Willis Tower, Chicago, IL",
        destination="Navy Pier, Chicago, IL",
        timeout_per_route=120.0
    )

    assert isinstance(result, dict)
    assert "routes" in result
    assert "status" in result
    assert isinstance(result["routes"], list)


@pytest.mark.asyncio
async def test_analyze_routes_handles_invalid_address():
    """Test handling of invalid addresses."""
    result = await analyze_routes(
        start="This is not a real address 12345xyz",
        destination="Another fake address 67890abc"
    )

    # Should fail gracefully
    assert "error" in result or len(result.get("routes", [])) == 0


def test_sync_wrapper():
    """Test the synchronous wrapper function."""
    result = analyze_routes_sync(
        start="Millennium Park, Chicago",
        destination="Lincoln Park Zoo, Chicago"
    )

    assert isinstance(result, dict)
    assert "routes" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Phase 4 Completion Criteria

- [ ] `safe_travels.py` orchestrates Google Maps and agent
- [ ] Parallel agent execution works correctly
- [ ] Timeout handling prevents hung requests
- [ ] Partial failures return results for successful routes
- [ ] Sync wrapper available for non-async contexts
- [ ] CLI interface works
- [ ] All tests in `test_phase4_orchestrator.py` pass

---

# PHASE 5: FastAPI Application

## Objective
Create the REST API that exposes the route analysis functionality.

## Pre-Phase Research (REQUIRED)

### 5.1 Review FastAPI Patterns

Study:
- Request/Response models with Pydantic
- Async endpoints
- Error handling
- CORS configuration
- Health check endpoints

## Implementation Steps

Create `src/safe_travels_api.py`:

```python
"""SafeTravels FastAPI Application.

REST API for route crime risk analysis.
"""
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.safe_travels import analyze_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RouteAnalysisRequest(BaseModel):
    """Request body for route analysis."""

    start: str = Field(
        ...,
        min_length=3,
        description="Starting address (e.g., '123 Main St, Chicago, IL')"
    )
    destination: str = Field(
        ...,
        min_length=3,
        description="Destination address (e.g., '456 Oak Ave, Chicago, IL')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start": "Willis Tower, Chicago, IL",
                "destination": "Navy Pier, Chicago, IL"
            }
        }


class RouteResult(BaseModel):
    """Result for a single route."""

    route_id: int
    risk_score: Optional[int] = Field(None, ge=1, le=100)
    risk_summary: Optional[str] = None
    status: str
    error: Optional[str] = None


class RouteAnalysisResponse(BaseModel):
    """Response body for route analysis."""

    routes: List[RouteResult]
    total_routes: int = 0
    successful_analyses: int = 0
    status: str
    error: Optional[str] = None


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("SafeTravels API starting up...")
    yield
    logger.info("SafeTravels API shutting down...")


app = FastAPI(
    title="SafeTravels API",
    description=(
        "Route crime risk analysis API. Provides AI-powered risk scores "
        "for driving routes based on crime data analysis."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "safetravels-api"}


@app.post("/analyze-route", response_model=RouteAnalysisResponse)
async def analyze_route(request: RouteAnalysisRequest):
    """
    Analyze routes between two addresses for crime risk.

    Returns multiple route alternatives with risk scores (1-100) and
    detailed summaries explaining the assessment.
    """
    logger.info(f"Analyzing route: {request.start} -> {request.destination}")

    try:
        result = await analyze_routes(
            start=request.start,
            destination=request.destination,
            timeout_per_route=120.0
        )

        # Convert to response model
        routes = [RouteResult(**r) for r in result.get("routes", [])]

        return RouteAnalysisResponse(
            routes=routes,
            total_routes=result.get("total_routes", len(routes)),
            successful_analyses=result.get("successful_analyses", 0),
            status=result.get("status", "unknown"),
            error=result.get("error")
        )

    except Exception as e:
        logger.exception("Route analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SafeTravels API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze-route": "Analyze routes for crime risk",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Phase 5 Test

Create `src/tests/test_phase5_api.py`:

```python
"""Phase 5 Test: FastAPI Application.

This test verifies that:
1. API starts and responds to requests
2. Endpoints return correct response structure
3. Input validation works
4. Error handling is proper
"""
import pytest
from fastapi.testclient import TestClient
import os
from src.safe_travels_api import app


# Skip if required env vars not set
pytestmark = pytest.mark.skipif(
    not (os.getenv("GOOGLE_MAPS_API_KEY") and os.getenv("OPEN_ROUTER_API_KEY")),
    reason="Required API keys not set"
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    assert "service" in response.json()
    assert "endpoints" in response.json()


def test_analyze_route_validation(client):
    """Test input validation."""
    # Missing fields
    response = client.post("/analyze-route", json={})
    assert response.status_code == 422  # Validation error

    # Empty strings
    response = client.post("/analyze-route", json={
        "start": "",
        "destination": ""
    })
    assert response.status_code == 422


def test_analyze_route_success(client):
    """Test successful route analysis."""
    response = client.post("/analyze-route", json={
        "start": "Willis Tower, Chicago, IL",
        "destination": "Navy Pier, Chicago, IL"
    })

    assert response.status_code == 200
    data = response.json()

    assert "routes" in data
    assert "status" in data
    assert isinstance(data["routes"], list)


def test_analyze_route_response_structure(client):
    """Test that response matches expected structure."""
    response = client.post("/analyze-route", json={
        "start": "Millennium Park, Chicago",
        "destination": "Lincoln Park Zoo, Chicago"
    })

    assert response.status_code == 200
    data = response.json()

    assert "total_routes" in data
    assert "successful_analyses" in data

    if data["routes"]:
        route = data["routes"][0]
        assert "route_id" in route
        assert "status" in route


def test_docs_endpoint(client):
    """Test that OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/analyze-route" in schema["paths"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Phase 5 Completion Criteria

- [ ] FastAPI application created with proper structure
- [ ] `/analyze-route` POST endpoint works
- [ ] `/health` endpoint returns healthy status
- [ ] Request/response models validate properly
- [ ] CORS configured
- [ ] OpenAPI docs available at `/docs`
- [ ] All tests in `test_phase5_api.py` pass

---

# Environment Setup

## Required Environment Variables

Create a `.env` file in the project root:

```bash
# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# LLM (OpenRouter)
OPEN_ROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=openai/gpt-4o-mini

# Crime API
CRIME_API_KEY=your_crimeometer_api_key
CRIME_API_BASE_URL=https://api.crimeometer.com/v1

# MCP Server
CRIME_MCP_URL=http://localhost:8001/mcp
```

## Dependencies

Add to `requirements.txt`:

```
# API
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.0.0

# Google Maps
googlemaps>=4.10.0
polyline>=2.0.0

# AI Agent
pydantic-ai>=0.0.19
openai>=1.12.0

# MCP Server
fastmcp>=2.0.0
httpx>=0.27.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0

# Environment
python-dotenv>=1.0.0
```

---

# Running the Complete System

## 1. Start the Crime MCP Server

```bash
python -m src.MCP_Servers.crime_mcp
```

Server will be available at `http://localhost:8001/mcp`

## 2. Start the SafeTravels API

```bash
python src/safe_travels_api.py
```

API will be available at `http://localhost:8000`

## 3. Test the API

```bash
curl -X POST http://localhost:8000/analyze-route \
  -H "Content-Type: application/json" \
  -d '{"start": "Willis Tower, Chicago, IL", "destination": "Navy Pier, Chicago, IL"}'
```

---

# Testing All Phases

Run all tests:

```bash
# From project root
cd src
pytest tests/ -v
```

Run specific phase:

```bash
pytest tests/test_phase1_crime_mcp.py -v
pytest tests/test_phase2_google_maps.py -v
pytest tests/test_phase3_agent.py -v
pytest tests/test_phase4_orchestrator.py -v
pytest tests/test_phase5_api.py -v
```

---

# Summary Checklist

## Before Starting Each Phase

- [ ] Read ALL referenced documentation
- [ ] Ask clarifying questions if anything is unclear
- [ ] Understand exactly what will be built

## Phase Completion

- [ ] **Phase 1**: Crime MCP Server running on port 8001
- [ ] **Phase 2**: `use_google_maps()` returns route data with waypoints
- [ ] **Phase 3**: AI agent analyzes routes and returns structured output
- [ ] **Phase 4**: Orchestrator coordinates parallel analysis
- [ ] **Phase 5**: FastAPI serves route analysis requests

## Final Validation

- [ ] All tests pass
- [ ] API responds correctly to sample requests
- [ ] Error handling works for edge cases
- [ ] Documentation is complete

---

# Appendix: Key Reference Files

| File | Purpose |
|------|---------|
| `docs/agent_zero.py` | **PRIMARY** PydanticAI agent reference |
| `docs/Pydantic_AI/agent.py` | Simple MCP connection example |
| `docs/Search_MCP/src/Example_MCP/` | MCP server boilerplate |
| `safetravels/mcp/server.py` | Existing MCP server (follow this structure) |
| `docs/crime_platform/crimeo_docs.md` | Crimeometer API documentation |
| `google-maps-services-python/` | Google Maps Python client reference |
| `docs/Pydantic_AI/pydantic_ai_docs/output.md` | Structured output documentation |
| `docs/Pydantic_AI/pydantic_ai_docs/mcp_client.md` | MCP client documentation |
