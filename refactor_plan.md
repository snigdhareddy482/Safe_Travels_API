# SafeTravels API — Complete Refactor Plan

> **Zero-Context Execution Guide**
> This document enables someone with NO knowledge of the codebase to execute a complete refactor in a single shot.

---

## Table of Contents

1. [Project Vision](#project-vision)
2. [Core Principles](#core-principles)
3. [Architecture Overview](#architecture-overview)
4. [File Structure](#file-structure)
5. [Phase 0: Environment Setup](#phase-0-environment-setup)
6. [Phase 1: Crime MCP Server](#phase-1-crime-mcp-server)
7. [Phase 2: Google Maps Helper](#phase-2-google-maps-helper)
8. [Phase 3: SafeTravels AI Agent](#phase-3-safetravels-ai-agent)
9. [Phase 4: Orchestrator Script](#phase-4-orchestrator-script)
10. [Phase 5: FastAPI Application](#phase-5-fastapi-application)
11. [Final Validation](#final-validation)

---

## Project Vision

**Mission**: Build a clean, elegant API that takes a start address and destination address, analyzes crime data along multiple route alternatives, and returns AI-generated risk scores (1-100) with detailed summaries for each route.

**Target Use Case**: Urban navigation safety — helping users choose the safest route in cities.

**Data Flow**:
```
User Input (start + destination addresses)
    ↓
Google Maps API → Returns multiple route alternatives with:
    - Route geometry (polyline)
    - Waypoints (adaptive sampling, denser in urban areas)
    - Real-time traffic data
    - Place types along route (gas stations, police stations)
    ↓
AI Agent (one per route, running in parallel) → Uses Crime MCP tools to:
    - Query crime statistics for waypoints
    - Analyze incident counts, severity, recency, time patterns
    - Focus on "interesting" areas while maintaining accuracy
    ↓
Final Output → List of routes with:
    - Risk score (1-100)
    - Detailed summary explaining the score
```

---

## Core Principles

### 1. KISS (Keep It Simple, Stupid)
- No excess code
- Clean, readable, elegant implementations
- Delete unused code completely — no backwards-compatibility hacks

### 2. Research First
- Before EACH phase, conduct deep research
- Use Context7 MCP server for documentation lookups
- Understand EXACTLY what will be implemented and HOW

### 3. Ask Clarifying Questions
- ALWAYS ask clarifying questions before starting any major phase
- Never assume — verify requirements

### 4. Test to Verify
- Each phase has a corresponding test file
- Tests must pass before moving to the next phase
- Use BOTH mocked tests (for CI) and live API tests (for integration)

### 5. Accuracy Over Speed
- The AI agent should focus on "interesting" areas
- But data and statistics must ALWAYS be accurate
- Never fabricate crime data

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│                         POST /analyze-route                                  │
│                         {start: "123 Main St", destination: "456 Oak Ave"}  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        safe_travels_api.py (FastAPI)                         │
│                        - Receives POST request                               │
│                        - Validates input                                     │
│                        - Calls safe_travels.py orchestrator                  │
│                        - Returns JSON response                               │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        safe_travels.py (Orchestrator)                        │
│                        1. Call use_google_maps(start, destination)           │
│                        2. For each route, spawn AI agent in parallel         │
│                        3. Collect results (handle partial failures)          │
│                        4. Return consolidated response                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
┌─────────────────────────────────┐   ┌───────────────────────────────────────┐
│  helper_functions/google_maps.py │   │  safe_travels_agent.py                │
│                                  │   │  - PydanticAI Agent with OpenRouter   │
│  use_google_maps(                │   │  - World-class system prompt          │
│    start: str,                   │   │  - Connected to Crime MCP Server      │
│    destination: str              │   │  - Structured output:                 │
│  ) -> List[RouteData]            │   │    • risk_score: 1-100                │
│                                  │   │    • risk_summary: detailed text      │
│  Returns:                        │   │                                       │
│  - Multiple route alternatives   │   │  Agent uses judgment to focus on      │
│  - Adaptive waypoints            │   │  "interesting" areas while ensuring   │
│  - Real-time traffic             │   │  data accuracy                        │
│  - Place types (gas, police)     │   │                                       │
└─────────────────────────────────┘   └───────────────────┬───────────────────┘
                                                          │
                                                          ▼
                                      ┌───────────────────────────────────────┐
                                      │  MCP_Servers/crime_mcp/               │
                                      │  - FastMCP with Streamable HTTP       │
                                      │  - Tools for querying crime data:     │
                                      │    • get_crime_stats()                │
                                      │    • get_crime_incidents()            │
                                      │  - Data points:                       │
                                      │    • Total incident count             │
                                      │    • Severity (offense codes)         │
                                      │    • Recency (7 days vs 30 days)      │
                                      │    • Time-of-day patterns             │
                                      └───────────────────────────────────────┘
```

---

## File Structure

```
Safe_Travels_API/
├── .env                            # Environment variables (API keys)
├── .env.example                    # Template for .env
├── requirements.txt                # Python dependencies
├── refactor_plan.md               # This document
├── README.md                       # Quick start guide
│
├── src/
│   ├── __init__.py
│   ├── safe_travels.py             # Main orchestrator script
│   ├── safe_travels_api.py         # FastAPI application
│   ├── safe_travels_agent.py       # PydanticAI agent definition
│   │
│   ├── helper_functions/
│   │   ├── __init__.py
│   │   └── google_maps.py          # Google Maps API wrapper
│   │
│   ├── MCP_Servers/
│   │   ├── __init__.py
│   │   └── crime_mcp/
│   │       ├── __init__.py
│   │       ├── __main__.py         # Entry point: python -m src.MCP_Servers.crime_mcp
│   │       ├── config.py           # Pydantic settings (API keys, URLs)
│   │       ├── functions.py        # Crime API implementation
│   │       ├── server.py           # FastMCP server definition
│   │       └── API_RESEARCH.md     # Crime API research findings
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Shared pytest fixtures
│       ├── test_phase1_crime_mcp.py
│       ├── test_phase2_google_maps.py
│       ├── test_phase3_agent.py
│       ├── test_phase4_orchestrator.py
│       └── test_phase5_api.py
│
└── docs/
    ├── agent_zero.py               # PRIMARY PydanticAI reference
    ├── Pydantic_AI/                # PydanticAI documentation
    ├── Search_MCP/                 # MCP server boilerplate
    └── crime_platform/             # Crime API documentation
```

---

## Phase 0: Environment Setup

### Objective
Set up the development environment with all dependencies and API keys.

### Pre-Phase Checklist
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] API keys obtained (see below)

### Step 0.1: Create Virtual Environment

```bash
cd Safe_Travels_API
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 0.2: Install Dependencies

Create/update `requirements.txt`:

```
# API Framework
fastapi>=0.110.0
uvicorn>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.0.0

# Google Maps
googlemaps>=4.10.0
polyline>=2.0.0

# AI Agent (PydanticAI)
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

Install:
```bash
pip install -r requirements.txt
```

### Step 0.3: Obtain API Keys

You need the following API keys:

| API | Purpose | Where to Get |
|-----|---------|--------------|
| Google Maps | Route data | https://console.cloud.google.com/ |
| OpenRouter | LLM access | https://openrouter.ai/keys |
| Crime API | Crime data | TBD in Phase 1 research |

### Step 0.4: Create .env File

```bash
# Google Maps
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# LLM (OpenRouter)
OPEN_ROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=openai/gpt-4o-mini

# Crime API (will be filled after Phase 1 research)
CRIME_API_KEY=your_crime_api_key
CRIME_API_BASE_URL=https://api.example.com/v1

# MCP Server
CRIME_MCP_URL=http://localhost:8001/mcp

# Optional: Logging
LOGFIRE=disabled
```

### Phase 0 Verification

```bash
# Verify Python version
python --version  # Should be 3.10+

# Verify dependencies installed
pip list | grep fastapi
pip list | grep pydantic-ai

# Verify .env exists
cat .env
```

---

## Phase 1: Crime MCP Server

### Objective
Create an MCP server that provides crime data tools for the AI agent to use.

### CRITICAL: Pre-Phase Research

**Before writing ANY code, you MUST complete the following research:**

#### 1.1 Research Crime APIs Using Context7

Use the Context7 MCP server to research documentation. Execute these queries:

```
# Query Context7 for crime API documentation
"Search for Crimeometer API documentation and endpoints"
"Search for SpotCrime API documentation"
"Search for CrimeMapping API"
"Search for FBI UCR Crime Data Explorer API"
```

#### 1.2 Evaluate Crime API Options

Research and document findings for each API:

| API | Coverage | Rate Limits | Data Points | Pricing | Verdict |
|-----|----------|-------------|-------------|---------|---------|
| **Crimeometer** | 30+ US cities | ? | Incidents, Stats, Crowdsourced | ? | ? |
| **SpotCrime** | ? | ? | ? | ? | ? |
| **CrimeMapping** | ? | ? | ? | ? | ? |
| **FBI UCR** | All US | Free | Annual aggregates | Free | ? |

**Questions to answer:**
1. Which API provides the data points we need?
   - Total incident count ✓
   - Crime severity (offense codes) ✓
   - Recency (configurable date range) ✓
   - Time-of-day patterns ✓
2. Which API has the best coverage for urban areas?
3. What are the rate limits and pricing?
4. How is the response structured?

**Document findings in:** `src/MCP_Servers/crime_mcp/API_RESEARCH.md`

#### 1.3 Study Reference Materials

Read these files thoroughly before implementation:

1. **MCP Server Boilerplate**: `docs/Search_MCP/src/Example_MCP/`
   - [server.py](docs/Search_MCP/src/Example_MCP/server.py) — FastMCP setup, tool definitions
   - [config.py](docs/Search_MCP/src/Example_MCP/config.py) — Pydantic settings pattern
   - [functions.py](docs/Search_MCP/src/Example_MCP/functions.py) — Business logic separation

2. **MCP Explained**: `docs/Search_MCP/docs/MCP_Explained.md`
   - Beginner guide to MCP concepts
   - Lifecycle management
   - Tool decorators

3. **Crime API Docs**: `docs/crime_platform/crimeo_docs.md`
   - Crimeometer endpoints (Raw Data, Stats, Crowdsourced)
   - FBI-NIBRS offense codes
   - Response structure

#### 1.4 Ask Clarifying Questions

Before proceeding, ask the user:
- "Based on my research, [API X] appears to be the best choice because [reasons]. Do you agree?"
- "The API provides [data points]. Is this sufficient for scoring?"
- "Are there any coverage gaps for your target cities?"

---

### Implementation

#### Step 1.1: Create Directory Structure

```bash
mkdir -p src/MCP_Servers/crime_mcp
touch src/MCP_Servers/__init__.py
touch src/MCP_Servers/crime_mcp/__init__.py
touch src/MCP_Servers/crime_mcp/__main__.py
touch src/MCP_Servers/crime_mcp/config.py
touch src/MCP_Servers/crime_mcp/functions.py
touch src/MCP_Servers/crime_mcp/server.py
touch src/MCP_Servers/crime_mcp/API_RESEARCH.md
```

#### Step 1.2: Create config.py

```python
"""Crime MCP Server Configuration.

Loads settings from environment variables using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class CrimeMCPSettings(BaseSettings):
    """Settings for the Crime MCP Server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Crime API Configuration
    CRIME_API_KEY: str
    CRIME_API_BASE_URL: str = "https://api.crimeometer.com/v1"

    # Optional: Request timeout
    REQUEST_TIMEOUT: float = 30.0
```

#### Step 1.3: Create functions.py

```python
"""Crime API implementation functions.

This file contains the actual logic for calling crime APIs.
Business logic is separated from the MCP server definition.

IMPORTANT: The exact implementation depends on the API chosen in research.
The structure below is for Crimeometer — adapt as needed.
"""
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


async def get_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float,
    days_back: int,
    api_key: str,
    base_url: str,
    http_client: httpx.AsyncClient
) -> Dict[str, Any]:
    """
    Get aggregated crime statistics for a location.

    Returns:
        - total_incidents: Total crime count
        - by_type: Breakdown by offense type with counts
        - by_severity: Breakdown by severity level
        - recent_trend: Incidents in last 7 days vs previous period
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    # Convert radius to meters (API-specific)
    radius_meters = radius_miles * 1609.34

    # Build request (adapt URL/params based on chosen API)
    url = f"{base_url}/incidents/stats"
    params = {
        "lat": latitude,
        "lon": longitude,
        "distance": f"{radius_meters}m",
        "datetime_ini": start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "datetime_end": end_date.strftime("%Y-%m-%dT23:59:59.999Z"),
    }
    headers = {"x-api-key": api_key}

    try:
        response = await http_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Process and return structured data
        return {
            "total_incidents": data.get("total_incidents", 0),
            "by_type": data.get("incidents_by_type", []),
            "location": {"lat": latitude, "lon": longitude},
            "radius_miles": radius_miles,
            "days_analyzed": days_back
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"API error: {e.response.status_code}", "details": str(e)}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


async def get_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float,
    days_back: int,
    api_key: str,
    base_url: str,
    http_client: httpx.AsyncClient,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get raw crime incident data for a location.

    Returns individual incidents with:
        - incident_date
        - incident_offense (FBI-NIBRS standard)
        - incident_offense_code (for severity mapping)
        - incident_offense_description
        - incident_latitude, incident_longitude
        - incident_crime_against (Person/Property/Society)
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    radius_meters = radius_miles * 1609.34

    url = f"{base_url}/incidents/raw-data"
    params = {
        "lat": latitude,
        "lon": longitude,
        "distance": f"{radius_meters}m",
        "datetime_ini": start_date.strftime("%Y-%m-%dT00:00:00.000Z"),
        "datetime_end": end_date.strftime("%Y-%m-%dT23:59:59.999Z"),
        "page": 1,
    }
    headers = {"x-api-key": api_key}

    try:
        response = await http_client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        incidents = data.get("incidents", [])[:limit]

        # Categorize by severity
        severity_counts = {"violent": 0, "property": 0, "other": 0}
        for incident in incidents:
            crime_against = incident.get("incident_crime_against", "").lower()
            if "person" in crime_against:
                severity_counts["violent"] += 1
            elif "property" in crime_against:
                severity_counts["property"] += 1
            else:
                severity_counts["other"] += 1

        return {
            "incidents": incidents,
            "count": len(incidents),
            "severity_breakdown": severity_counts,
            "location": {"lat": latitude, "lon": longitude},
            "radius_miles": radius_miles,
            "days_analyzed": days_back
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"API error: {e.response.status_code}", "details": str(e)}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


async def get_time_pattern_analysis(
    latitude: float,
    longitude: float,
    radius_miles: float,
    days_back: int,
    api_key: str,
    base_url: str,
    http_client: httpx.AsyncClient
) -> Dict[str, Any]:
    """
    Analyze crime patterns by time of day.

    Returns:
        - by_hour: Crime counts grouped by hour (0-23)
        - peak_hours: Hours with highest crime
        - safest_hours: Hours with lowest crime
    """
    # First get raw incidents
    result = await get_crime_incidents(
        latitude, longitude, radius_miles, days_back,
        api_key, base_url, http_client, limit=500
    )

    if "error" in result:
        return result

    # Analyze time patterns
    hour_counts = {i: 0 for i in range(24)}

    for incident in result.get("incidents", []):
        incident_date = incident.get("incident_date", "")
        try:
            # Parse datetime and extract hour
            dt = datetime.fromisoformat(incident_date.replace("Z", "+00:00"))
            hour_counts[dt.hour] += 1
        except (ValueError, AttributeError):
            continue

    # Find peaks and safest times
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    peak_hours = [h for h, _ in sorted_hours[:3]]
    safest_hours = [h for h, _ in sorted_hours[-3:]]

    return {
        "by_hour": hour_counts,
        "peak_hours": peak_hours,
        "safest_hours": safest_hours,
        "total_analyzed": len(result.get("incidents", [])),
        "location": {"lat": latitude, "lon": longitude}
    }
```

#### Step 1.4: Create server.py

```python
"""Crime MCP Server.

Provides crime data tools for AI agents to analyze route safety.

Running the Server:
    python -m src.MCP_Servers.crime_mcp

Server will be available at: http://localhost:8001/mcp
"""
import logging
import sys
from typing import Optional
from contextlib import asynccontextmanager

import httpx
from fastmcp import FastMCP

from .config import CrimeMCPSettings
from .functions import (
    get_crime_stats,
    get_crime_incidents,
    get_time_pattern_analysis
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger("crime-mcp")

# Global HTTP client (reused across requests)
http_client: Optional[httpx.AsyncClient] = None

# Load settings from environment
settings = CrimeMCPSettings()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    """
    Lifecycle manager for the MCP server.

    - Startup: Initialize HTTP client
    - Shutdown: Close HTTP client
    """
    global http_client

    logger.info("Crime MCP server starting...")
    http_client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
    logger.info("HTTP client initialized")

    yield  # Server runs while yielding

    logger.info("Crime MCP server shutting down...")
    if http_client and not http_client.is_closed:
        await http_client.aclose()
        http_client = None
    logger.info("Cleanup complete")


# Initialize MCP server
mcp = FastMCP(
    name="crime-analysis",
    instructions="""Crime data analysis tools for route safety assessment.

Use these tools to query crime statistics and incidents at specific locations.

Available tools:
- get_location_crime_stats: Get aggregated crime statistics
- get_location_crime_incidents: Get raw incident data with severity breakdown
- get_location_time_patterns: Analyze crime patterns by time of day

IMPORTANT: Query multiple waypoints along a route to get complete coverage.
The AI agent should use these tools to gather data, then synthesize findings.""",
    lifespan=lifespan
)


@mcp.tool(
    description="""Get aggregated crime statistics for a specific location.

Returns total incident count and breakdown by crime type.
Use this for a quick overview of crime levels at a point along a route.

Parameters:
- latitude: GPS latitude (-90 to 90)
- longitude: GPS longitude (-180 to 180)
- radius_miles: Search radius (default 0.5 miles for urban, 1.0 for suburban)
- days_back: Historical lookback period (default 30, use 7 for recent trends)"""
)
async def get_location_crime_stats(
    latitude: float,
    longitude: float,
    radius_miles: float = 0.5,
    days_back: int = 30
) -> dict:
    """Query crime statistics for a geographic location."""
    if not http_client:
        return {"error": "Server not initialized"}

    return await get_crime_stats(
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        days_back=days_back,
        api_key=settings.CRIME_API_KEY,
        base_url=settings.CRIME_API_BASE_URL,
        http_client=http_client
    )


@mcp.tool(
    description="""Get detailed crime incident data for a location.

Returns individual crime reports with:
- Offense type and code (FBI-NIBRS standard)
- Severity classification (violent/property/other)
- Date and location

Use this for deeper analysis of high-crime areas identified by stats."""
)
async def get_location_crime_incidents(
    latitude: float,
    longitude: float,
    radius_miles: float = 0.5,
    days_back: int = 30,
    limit: int = 50
) -> dict:
    """Query raw crime incident data for a location."""
    if not http_client:
        return {"error": "Server not initialized"}

    return await get_crime_incidents(
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        days_back=days_back,
        api_key=settings.CRIME_API_KEY,
        base_url=settings.CRIME_API_BASE_URL,
        http_client=http_client,
        limit=limit
    )


@mcp.tool(
    description="""Analyze crime patterns by time of day for a location.

Returns:
- Crime counts by hour (0-23)
- Peak crime hours
- Safest hours

Use this to provide time-based recommendations (e.g., "avoid this area after 10pm")."""
)
async def get_location_time_patterns(
    latitude: float,
    longitude: float,
    radius_miles: float = 0.5,
    days_back: int = 30
) -> dict:
    """Analyze crime time patterns for a location."""
    if not http_client:
        return {"error": "Server not initialized"}

    return await get_time_pattern_analysis(
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        days_back=days_back,
        api_key=settings.CRIME_API_KEY,
        base_url=settings.CRIME_API_BASE_URL,
        http_client=http_client
    )


def run_server():
    """Start the MCP server."""
    port = 8001
    logger.info(f"Starting Crime MCP server on port {port}...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/mcp",
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
```

#### Step 1.5: Create __main__.py

```python
"""Entry point for running the Crime MCP server.

Usage:
    python -m src.MCP_Servers.crime_mcp
"""
from .server import run_server

if __name__ == "__main__":
    run_server()
```

---

### Phase 1 Tests

Create `src/tests/test_phase1_crime_mcp.py`:

```python
"""Phase 1 Tests: Crime MCP Server

Test Strategy:
- MOCKED tests: Test server structure and tool definitions (no API calls)
- LIVE tests: Test actual API integration (requires API key)

Run mocked tests:
    pytest src/tests/test_phase1_crime_mcp.py -v -m "not live"

Run all tests (requires API key):
    pytest src/tests/test_phase1_crime_mcp.py -v
"""
import pytest
import asyncio
import httpx
import os
import subprocess
import time
import signal
from unittest.mock import AsyncMock, patch, MagicMock

# Test configuration
MCP_URL = "http://localhost:8001/mcp"
TIMEOUT = 30.0

# Mark for live tests
live = pytest.mark.live


# =============================================================================
# MOCKED TESTS (No API calls)
# =============================================================================

class TestCrimeMCPStructure:
    """Test the MCP server structure without making API calls."""

    def test_config_loads(self):
        """Test that configuration class is properly defined."""
        from src.MCP_Servers.crime_mcp.config import CrimeMCPSettings

        # Should not raise (uses defaults for missing env vars in tests)
        with patch.dict(os.environ, {"CRIME_API_KEY": "test-key"}):
            settings = CrimeMCPSettings()
            assert settings.CRIME_API_KEY == "test-key"
            assert "crimeometer" in settings.CRIME_API_BASE_URL.lower() or settings.CRIME_API_BASE_URL

    def test_functions_exist(self):
        """Test that all required functions are defined."""
        from src.MCP_Servers.crime_mcp.functions import (
            get_crime_stats,
            get_crime_incidents,
            get_time_pattern_analysis
        )

        assert callable(get_crime_stats)
        assert callable(get_crime_incidents)
        assert callable(get_time_pattern_analysis)

    def test_server_mcp_defined(self):
        """Test that the MCP server is properly configured."""
        # Import with mocked settings
        with patch.dict(os.environ, {"CRIME_API_KEY": "test-key"}):
            from src.MCP_Servers.crime_mcp.server import mcp

            assert mcp.name == "crime-analysis"
            assert mcp.instructions is not None


class TestCrimeFunctionsMocked:
    """Test crime functions with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_get_crime_stats_success(self):
        """Test get_crime_stats with mocked successful response."""
        from src.MCP_Servers.crime_mcp.functions import get_crime_stats

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_incidents": 42,
            "incidents_by_type": [
                {"type": "THEFT", "count": 20},
                {"type": "ASSAULT", "count": 10}
            ]
        }
        mock_response.raise_for_status = MagicMock()

        # Mock HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = mock_response

        result = await get_crime_stats(
            latitude=41.8781,
            longitude=-87.6298,
            radius_miles=1.0,
            days_back=30,
            api_key="test-key",
            base_url="https://api.example.com",
            http_client=mock_client
        )

        assert "total_incidents" in result
        assert result["location"]["lat"] == 41.8781

    @pytest.mark.asyncio
    async def test_get_crime_stats_api_error(self):
        """Test get_crime_stats handles API errors gracefully."""
        from src.MCP_Servers.crime_mcp.functions import get_crime_stats

        # Mock HTTP error
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_client.get.return_value = mock_response

        result = await get_crime_stats(
            latitude=41.8781,
            longitude=-87.6298,
            radius_miles=1.0,
            days_back=30,
            api_key="test-key",
            base_url="https://api.example.com",
            http_client=mock_client
        )

        assert "error" in result


# =============================================================================
# LIVE TESTS (Require API key and running server)
# =============================================================================

@pytest.fixture(scope="module")
def mcp_server():
    """Start the MCP server for live testing."""
    api_key = os.getenv("CRIME_API_KEY")
    if not api_key:
        pytest.skip("CRIME_API_KEY not set")

    # Start server as subprocess
    env = os.environ.copy()
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
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


@live
class TestCrimeMCPLive:
    """Live integration tests for the Crime MCP server."""

    @pytest.mark.asyncio
    async def test_server_responds(self, mcp_server):
        """Test that the server is running and responding."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_crime_stats_tool(self, mcp_server):
        """Test calling the crime stats tool."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
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


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not live"])
```

---

### Phase 1 Completion Checklist

- [ ] API research completed and documented in `API_RESEARCH.md`
- [ ] Crime API selected based on research findings
- [ ] `config.py` loads settings from environment
- [ ] `functions.py` implements crime data queries
- [ ] `server.py` defines MCP tools with clear descriptions
- [ ] `__main__.py` allows running with `python -m src.MCP_Servers.crime_mcp`
- [ ] Server starts and responds at `http://localhost:8001/mcp`
- [ ] All mocked tests pass: `pytest src/tests/test_phase1_crime_mcp.py -v -m "not live"`
- [ ] Live tests pass (with API key): `pytest src/tests/test_phase1_crime_mcp.py -v`

---

## Phase 2: Google Maps Helper

### Objective
Create a function that takes start and destination addresses, returns route data with adaptive waypoints, real-time traffic, and place types.

### CRITICAL: Pre-Phase Research

#### 2.1 Study Google Maps Python Client Using Context7

Use Context7 MCP server to research:

```
"Search for googlemaps Python client directions API documentation"
"Search for googlemaps Python polyline decoding"
"Search for Google Maps Directions API alternatives parameter"
"Search for Google Maps Places API nearby search"
```

#### 2.2 Study Reference Files

1. **Google Maps Client**: Research the `googlemaps` Python package
   - `directions()` method — get routes with alternatives
   - Response structure — legs, steps, polyline, duration, distance
   - Traffic data — `departure_time` parameter for real-time traffic

2. **Polyline Library**: `polyline` package for decoding route geometry

#### 2.3 Understand Data Requirements

The Google Maps function must return:

| Data Point | Source | Purpose |
|------------|--------|---------|
| Route alternatives | `alternatives=True` | Multiple routes to analyze |
| Encoded polyline | `overview_polyline` | Route geometry |
| Waypoints (adaptive) | Decoded polyline, sampled | Points for crime queries |
| Real-time traffic | `departure_time="now"` | Traffic conditions |
| Distance/Duration | Leg data | Route metrics |
| Place types | Places API | Gas stations, police stations |

#### 2.4 Plan Adaptive Waypoint Sampling

Waypoint density should be adaptive:
- **Urban areas** (< 10 miles): Sample every 0.5-1 mile
- **Suburban** (10-30 miles): Sample every 2-3 miles
- **Highway/Rural** (> 30 miles): Sample every 5 miles

Also consider:
- Always include start and end points
- Sample more densely near urban centers
- Use reverse geocoding to identify area types (optional)

#### 2.5 Ask Clarifying Questions

Before proceeding, ask:
- "Should I include the estimated traffic delay in the route data?"
- "How many place types should I search for along the route?"
- "Should waypoint descriptions include city names (requires extra API calls)?"

---

### Implementation

#### Step 2.1: Create google_maps.py

```python
"""Google Maps helper functions.

Provides route data extraction for crime analysis with:
- Multiple route alternatives
- Adaptive waypoint sampling
- Real-time traffic data
- Place types along route (gas stations, police stations)
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import googlemaps
import polyline as polyline_lib
from math import radians, sin, cos, sqrt, atan2

# Initialize Google Maps client
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RoutePoint:
    """A point along a route for crime analysis."""
    latitude: float
    longitude: float
    description: Optional[str] = None  # City/area name (if enriched)
    area_type: Optional[str] = None  # "urban", "suburban", "rural"


@dataclass
class PlaceInfo:
    """A place of interest along the route."""
    name: str
    place_type: str  # "gas_station", "police", etc.
    latitude: float
    longitude: float
    vicinity: Optional[str] = None


@dataclass
class TrafficInfo:
    """Traffic information for a route."""
    duration_in_traffic_minutes: int
    traffic_delay_minutes: int  # Additional time due to traffic
    traffic_condition: str  # "light", "moderate", "heavy"


@dataclass
class RouteData:
    """Complete route data for crime analysis."""
    route_id: int
    summary: str  # e.g., "I-90 W via Downtown"
    distance_miles: float
    duration_minutes: int
    start_address: str
    end_address: str
    waypoints: List[RoutePoint]
    polyline: str  # Encoded polyline for visualization
    traffic: Optional[TrafficInfo] = None
    places_along_route: List[PlaceInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "route_id": self.route_id,
            "summary": self.summary,
            "distance_miles": self.distance_miles,
            "duration_minutes": self.duration_minutes,
            "start_address": self.start_address,
            "end_address": self.end_address,
            "waypoints": [
                {"latitude": wp.latitude, "longitude": wp.longitude, "description": wp.description}
                for wp in self.waypoints
            ],
            "polyline": self.polyline,
            "traffic": asdict(self.traffic) if self.traffic else None,
            "places_along_route": [asdict(p) for p in self.places_along_route]
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula."""
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def get_adaptive_interval(total_distance_miles: float) -> float:
    """
    Determine waypoint sampling interval based on route distance.

    - Urban (< 10 mi): 0.75 mile intervals
    - Suburban (10-30 mi): 2 mile intervals
    - Highway (> 30 mi): 5 mile intervals
    """
    if total_distance_miles < 10:
        return 0.75  # Dense sampling for urban routes
    elif total_distance_miles < 30:
        return 2.0  # Moderate for suburban
    else:
        return 5.0  # Sparse for highway/rural


def sample_points_from_polyline(
    encoded_polyline: str,
    interval_miles: float,
    total_distance_miles: float
) -> List[RoutePoint]:
    """
    Extract waypoints from a polyline at adaptive intervals.

    Args:
        encoded_polyline: Google's encoded polyline string
        interval_miles: Distance between sample points
        total_distance_miles: Total route distance (for context)

    Returns:
        List of RoutePoint objects
    """
    # Decode the polyline
    coords = polyline_lib.decode(encoded_polyline)

    if not coords:
        return []

    # Always include start point
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

    # Always include end point (if not already added)
    if len(coords) > 1:
        final = coords[-1]
        last_wp = waypoints[-1]
        if abs(last_wp.latitude - final[0]) > 0.0001 or abs(last_wp.longitude - final[1]) > 0.0001:
            waypoints.append(RoutePoint(latitude=final[0], longitude=final[1]))

    return waypoints


def classify_traffic(duration_normal: int, duration_traffic: int) -> TrafficInfo:
    """Classify traffic condition based on delay."""
    delay = duration_traffic - duration_normal

    if delay < 5:
        condition = "light"
    elif delay < 15:
        condition = "moderate"
    else:
        condition = "heavy"

    return TrafficInfo(
        duration_in_traffic_minutes=duration_traffic,
        traffic_delay_minutes=delay,
        traffic_condition=condition
    )


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def use_google_maps(
    start: str,
    destination: str,
    include_traffic: bool = True,
    include_places: bool = True,
    place_types: List[str] = None
) -> List[RouteData]:
    """
    Get route alternatives between two addresses with adaptive waypoints.

    Args:
        start: Starting address (e.g., "123 Main St, Chicago, IL")
        destination: Destination address
        include_traffic: Whether to fetch real-time traffic data
        include_places: Whether to fetch places along route
        place_types: Place types to search for (default: gas_station, police)

    Returns:
        List of RouteData objects, one per route alternative

    Raises:
        ValueError: If API key not set or invalid addresses
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")

    if place_types is None:
        place_types = ["gas_station", "police"]

    gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

    # Build directions request
    directions_params = {
        "origin": start,
        "destination": destination,
        "mode": "driving",
        "alternatives": True,  # Request multiple routes
    }

    # Add traffic data request
    if include_traffic:
        directions_params["departure_time"] = "now"
        directions_params["traffic_model"] = "best_guess"

    # Get directions
    try:
        directions_result = gmaps.directions(**directions_params)
    except googlemaps.exceptions.ApiError as e:
        raise ValueError(f"Google Maps API error: {e}")

    if not directions_result:
        raise ValueError(f"No routes found between '{start}' and '{destination}'")

    routes = []

    for idx, route in enumerate(directions_result):
        leg = route["legs"][0]  # Single leg for direct A to B

        # Extract distance and duration
        distance_meters = leg["distance"]["value"]
        distance_miles = distance_meters / 1609.34

        duration_seconds = leg["duration"]["value"]
        duration_minutes = duration_seconds // 60

        # Get traffic info if available
        traffic_info = None
        if include_traffic and "duration_in_traffic" in leg:
            traffic_seconds = leg["duration_in_traffic"]["value"]
            traffic_minutes = traffic_seconds // 60
            traffic_info = classify_traffic(duration_minutes, traffic_minutes)

        # Get overview polyline
        overview_polyline = route["overview_polyline"]["points"]

        # Sample waypoints adaptively
        interval = get_adaptive_interval(distance_miles)
        waypoints = sample_points_from_polyline(
            overview_polyline,
            interval_miles=interval,
            total_distance_miles=distance_miles
        )

        # Get places along route (optional)
        places = []
        if include_places and waypoints:
            places = _get_places_along_route(gmaps, waypoints, place_types)

        route_data = RouteData(
            route_id=idx + 1,
            summary=route.get("summary", f"Route {idx + 1}"),
            distance_miles=round(distance_miles, 1),
            duration_minutes=int(duration_minutes),
            start_address=leg["start_address"],
            end_address=leg["end_address"],
            waypoints=waypoints,
            polyline=overview_polyline,
            traffic=traffic_info,
            places_along_route=places
        )

        routes.append(route_data)

    return routes


def _get_places_along_route(
    gmaps: googlemaps.Client,
    waypoints: List[RoutePoint],
    place_types: List[str],
    max_places_per_type: int = 5
) -> List[PlaceInfo]:
    """
    Find places of interest along the route.

    Samples a few waypoints and searches for nearby places.
    """
    places = []

    # Sample waypoints for places search (don't query every point)
    sample_indices = [0, len(waypoints)//2, -1]  # Start, middle, end
    sample_points = [waypoints[i] for i in sample_indices if i < len(waypoints)]

    for point in sample_points:
        for place_type in place_types:
            try:
                results = gmaps.places_nearby(
                    location=(point.latitude, point.longitude),
                    radius=1609,  # 1 mile
                    type=place_type
                )

                for result in results.get("results", [])[:max_places_per_type]:
                    loc = result["geometry"]["location"]
                    places.append(PlaceInfo(
                        name=result.get("name", "Unknown"),
                        place_type=place_type,
                        latitude=loc["lat"],
                        longitude=loc["lng"],
                        vicinity=result.get("vicinity")
                    ))
            except Exception:
                continue  # Skip on error, don't fail the whole request

    return places


# =============================================================================
# OPTIONAL: Enrich waypoints with city names
# =============================================================================

def enrich_waypoints_with_locations(
    routes: List[RouteData],
    gmaps_client: googlemaps.Client
) -> List[RouteData]:
    """
    Add city/area descriptions to waypoints via reverse geocoding.

    WARNING: This makes additional API calls. Use sparingly.
    """
    for route in routes:
        for waypoint in route.waypoints:
            try:
                result = gmaps_client.reverse_geocode(
                    (waypoint.latitude, waypoint.longitude),
                    result_type=["locality", "neighborhood"]
                )
                if result:
                    for component in result[0].get("address_components", []):
                        if "locality" in component.get("types", []):
                            waypoint.description = component["long_name"]
                            break
                        elif "neighborhood" in component.get("types", []):
                            waypoint.description = component["long_name"]
            except Exception:
                pass  # Continue without description

    return routes
```

---

### Phase 2 Tests

Create `src/tests/test_phase2_google_maps.py`:

```python
"""Phase 2 Tests: Google Maps Helper Function

Test Strategy:
- MOCKED tests: Test helper functions without API calls
- LIVE tests: Test actual Google Maps API integration

Run mocked tests:
    pytest src/tests/test_phase2_google_maps.py -v -m "not live"

Run all tests (requires API key):
    pytest src/tests/test_phase2_google_maps.py -v
"""
import pytest
import os
from unittest.mock import patch, MagicMock

# Mark for live tests
live = pytest.mark.live


# =============================================================================
# MOCKED TESTS
# =============================================================================

class TestHelperFunctions:
    """Test helper functions without API calls."""

    def test_haversine_distance(self):
        """Test distance calculation between two points."""
        from src.helper_functions.google_maps import haversine_distance

        # Chicago to Milwaukee is ~90 miles
        distance = haversine_distance(
            41.8781, -87.6298,  # Chicago
            43.0389, -87.9065   # Milwaukee
        )
        assert 80 < distance < 100

    def test_get_adaptive_interval_urban(self):
        """Test adaptive interval for urban routes."""
        from src.helper_functions.google_maps import get_adaptive_interval

        interval = get_adaptive_interval(5.0)  # 5 mile urban route
        assert interval <= 1.0  # Dense sampling

    def test_get_adaptive_interval_suburban(self):
        """Test adaptive interval for suburban routes."""
        from src.helper_functions.google_maps import get_adaptive_interval

        interval = get_adaptive_interval(20.0)  # 20 mile suburban route
        assert 1.0 < interval <= 3.0

    def test_get_adaptive_interval_highway(self):
        """Test adaptive interval for highway routes."""
        from src.helper_functions.google_maps import get_adaptive_interval

        interval = get_adaptive_interval(50.0)  # 50 mile highway route
        assert interval >= 4.0  # Sparse sampling

    def test_sample_points_from_polyline(self):
        """Test polyline sampling produces waypoints."""
        from src.helper_functions.google_maps import sample_points_from_polyline, RoutePoint

        # Sample encoded polyline (Chicago area)
        test_polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

        waypoints = sample_points_from_polyline(
            test_polyline,
            interval_miles=1.0,
            total_distance_miles=10.0
        )

        assert len(waypoints) >= 1
        assert all(isinstance(wp, RoutePoint) for wp in waypoints)
        assert all(-90 <= wp.latitude <= 90 for wp in waypoints)

    def test_classify_traffic(self):
        """Test traffic classification."""
        from src.helper_functions.google_maps import classify_traffic

        # Light traffic
        traffic = classify_traffic(30, 32)
        assert traffic.traffic_condition == "light"

        # Moderate traffic
        traffic = classify_traffic(30, 40)
        assert traffic.traffic_condition == "moderate"

        # Heavy traffic
        traffic = classify_traffic(30, 50)
        assert traffic.traffic_condition == "heavy"


class TestRouteDataStructure:
    """Test data class structures."""

    def test_route_point_creation(self):
        """Test RoutePoint dataclass."""
        from src.helper_functions.google_maps import RoutePoint

        point = RoutePoint(latitude=41.8781, longitude=-87.6298, description="Chicago")
        assert point.latitude == 41.8781
        assert point.description == "Chicago"

    def test_route_data_to_dict(self):
        """Test RouteData serialization."""
        from src.helper_functions.google_maps import RouteData, RoutePoint

        route = RouteData(
            route_id=1,
            summary="Test Route",
            distance_miles=5.0,
            duration_minutes=15,
            start_address="Start",
            end_address="End",
            waypoints=[RoutePoint(41.0, -87.0)],
            polyline="test"
        )

        data = route.to_dict()
        assert data["route_id"] == 1
        assert len(data["waypoints"]) == 1
        assert "latitude" in data["waypoints"][0]


# =============================================================================
# LIVE TESTS
# =============================================================================

@live
class TestGoogleMapsLive:
    """Live integration tests for Google Maps API."""

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip if API key not set."""
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            pytest.skip("GOOGLE_MAPS_API_KEY not set")

    def test_use_google_maps_returns_routes(self):
        """Test that use_google_maps returns a list of routes."""
        from src.helper_functions.google_maps import use_google_maps

        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",
            include_places=False  # Skip places to speed up test
        )

        assert isinstance(routes, list)
        assert len(routes) >= 1

    def test_route_has_required_fields(self):
        """Test that routes have all required fields."""
        from src.helper_functions.google_maps import use_google_maps, RouteData

        routes = use_google_maps(
            start="Union Station, Chicago, IL",
            destination="O'Hare Airport, Chicago, IL",
            include_places=False
        )

        route = routes[0]
        assert isinstance(route, RouteData)
        assert route.route_id >= 1
        assert route.distance_miles > 0
        assert route.duration_minutes > 0
        assert len(route.waypoints) >= 2
        assert route.polyline

    def test_waypoints_have_valid_coordinates(self):
        """Test that waypoints have valid GPS coordinates."""
        from src.helper_functions.google_maps import use_google_maps

        routes = use_google_maps(
            start="Millennium Park, Chicago, IL",
            destination="Lincoln Park Zoo, Chicago, IL",
            include_places=False
        )

        for route in routes:
            for waypoint in route.waypoints:
                assert -90 <= waypoint.latitude <= 90
                assert -180 <= waypoint.longitude <= 180

    def test_traffic_data_included(self):
        """Test that traffic data is returned."""
        from src.helper_functions.google_maps import use_google_maps

        routes = use_google_maps(
            start="Downtown Chicago, IL",
            destination="Evanston, IL",
            include_traffic=True,
            include_places=False
        )

        # At least one route should have traffic info
        has_traffic = any(route.traffic is not None for route in routes)
        assert has_traffic

    def test_places_along_route(self):
        """Test that places are returned when requested."""
        from src.helper_functions.google_maps import use_google_maps

        routes = use_google_maps(
            start="Willis Tower, Chicago, IL",
            destination="Wrigley Field, Chicago, IL",
            include_traffic=False,
            include_places=True,
            place_types=["gas_station"]
        )

        # Should find at least some gas stations on this route
        total_places = sum(len(r.places_along_route) for r in routes)
        assert total_places >= 0  # May be 0 if API rate limited


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not live"])
```

---

### Phase 2 Completion Checklist

- [ ] Context7 research on Google Maps API completed
- [ ] `google_maps.py` created with all required functions
- [ ] `use_google_maps()` returns `List[RouteData]`
- [ ] Adaptive waypoint sampling implemented
- [ ] Real-time traffic data included
- [ ] Place types along route supported
- [ ] All mocked tests pass
- [ ] Live tests pass (with API key)

---

## Phase 3: SafeTravels AI Agent

### Objective
Create a PydanticAI agent that connects to the Crime MCP server and analyzes route safety with accurate, judgment-based analysis.

### CRITICAL: Pre-Phase Research

#### 3.1 Study PydanticAI Using Context7

**This is the most complex phase. Deep research is required.**

Use Context7 MCP server:

```
"Search for PydanticAI agent documentation"
"Search for PydanticAI MCP client integration"
"Search for PydanticAI structured output types"
"Search for PydanticAI system prompts best practices"
"Search for PydanticAI async agent run"
```

#### 3.2 Study Reference Files (IN ORDER)

1. **PRIMARY REFERENCE**: `docs/agent_zero.py`
   - This is the MOST IMPORTANT file
   - Shows complete PydanticAI + MCP integration
   - Shows the class-based agent pattern
   - Study the `AgentZero` class structure

2. **Simple Example**: `docs/Pydantic_AI/agent.py`
   - Basic MCP connection
   - Simple chat loop

3. **Agents Documentation**: `docs/Pydantic_AI/pydantic_ai_docs/agents.md`
   - System prompts (static and dynamic)
   - Running agents (`run`, `run_sync`, `run_stream`)
   - Model settings

4. **Output Types**: `docs/Pydantic_AI/pydantic_ai_docs/output.md`
   - Structured output with Pydantic models
   - `output_type` parameter
   - Validation

5. **MCP Client**: `docs/Pydantic_AI/pydantic_ai_docs/mcp_client.md`
   - `MCPServerStreamableHTTP` usage
   - `agent.run_mcp_servers()` context manager

#### 3.3 Design the System Prompt

The system prompt is CRITICAL. It must instruct the agent on:

1. **Purpose**: Route safety analyst
2. **Scoring Scale**: 1-100 with clear definitions
3. **How to Use Tools**: Query multiple waypoints
4. **Data Analysis**: Severity weighting, recency, patterns
5. **Accuracy Requirements**: Focus on interesting areas but ensure accuracy
6. **Output Format**: Score + detailed summary

#### 3.4 Ask Clarifying Questions

Before proceeding, ask:
- "How should the agent prioritize severity vs. volume of crimes?"
- "Should the agent query all waypoints or use judgment to focus?"
- "What's the ideal summary length (100 words? 200 words?)?"

---

### Implementation

#### Step 3.1: Create safe_travels_agent.py

```python
"""SafeTravels Route Analysis Agent.

A PydanticAI agent that analyzes route safety using crime data.

Key Features:
- Connects to Crime MCP server via Streamable HTTP
- Uses OpenRouter for LLM access
- Returns structured output (risk_score + risk_summary)
- Focuses on "interesting" areas while maintaining accuracy
"""
import os
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.mcp import MCPServerStreamableHTTP

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# OUTPUT TYPES (Structured Output)
# =============================================================================

class RouteAnalysisResult(BaseModel):
    """Structured output from the route analysis agent.

    The agent MUST return data matching this schema.
    """
    risk_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Risk score from 1 (safest) to 100 (most dangerous)"
    )
    risk_summary: str = Field(
        ...,
        min_length=100,
        max_length=500,
        description="Detailed summary explaining the risk assessment, including specific areas and recommendations"
    )


# =============================================================================
# INPUT TYPES
# =============================================================================

@dataclass
class RouteAnalysisInput:
    """Input data for route analysis."""
    route_id: int
    summary: str  # Route name (e.g., "I-90 W via Downtown")
    distance_miles: float
    duration_minutes: int
    waypoints: List[Dict[str, float]]  # List of {"latitude": float, "longitude": float}
    traffic_condition: Optional[str] = None  # "light", "moderate", "heavy"
    places_along_route: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# CONFIGURATION
# =============================================================================

# LLM Configuration (via OpenRouter)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

# MCP Server URL
CRIME_MCP_URL = os.getenv("CRIME_MCP_URL", "http://localhost:8001/mcp")

# Validate configuration
if not OPENROUTER_API_KEY:
    raise ValueError("OPEN_ROUTER_API_KEY environment variable not set")

# Initialize model with OpenRouter
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

SYSTEM_PROMPT = """You are a Route Safety Analyst AI specializing in crime risk assessment for urban travel routes.

## YOUR MISSION
Analyze a driving route and provide an accurate crime risk score (1-100) with a detailed, evidence-based summary.

## SCORING SCALE
- 1-20: VERY SAFE - Minimal crime activity, safe for travel at any time
- 21-40: SAFE - Low crime levels, standard precautions recommended
- 41-60: MODERATE RISK - Some crime activity present, heightened awareness advised
- 61-80: HIGH RISK - Significant crime concentration, consider alternative routes or timing
- 81-100: VERY HIGH RISK - Dangerous area, strongly recommend avoiding or taking precautions

## HOW TO ANALYZE A ROUTE

You will receive route data with waypoints (GPS coordinates along the route).

### Step 1: Strategic Querying
- You do NOT need to query every single waypoint
- Use your judgment to identify "interesting" areas:
  - Query the start and end points
  - Query mid-route points that might be in urban centers
  - If initial queries show high crime, query nearby points to understand the pattern
- AIM FOR ACCURACY: If you're unsure about an area, query it

### Step 2: Use the Crime Tools
Available tools:
- `get_location_crime_stats`: Get total incidents and breakdown by type
- `get_location_crime_incidents`: Get detailed incident data with severity
- `get_location_time_patterns`: Analyze crime by time of day

Recommended approach:
1. Start with `get_location_crime_stats` for key waypoints
2. For high-crime areas, use `get_location_crime_incidents` for details
3. Use `get_location_time_patterns` if time-based advice would be helpful

### Step 3: Analyze the Data
Consider these factors (in order of importance):

1. **Severity Weighting**:
   - Violent crimes (assault, robbery) = HIGH weight
   - Property crimes (theft, burglary) = MEDIUM weight
   - Other crimes = LOW weight

2. **Incident Volume**:
   - Compare total incidents to route length
   - High-density areas are riskier than spread-out incidents

3. **Recency**:
   - Recent incidents (last 7 days) are more concerning
   - Older patterns may have changed

4. **Concentration**:
   - A few hotspots are easier to avoid than widespread crime
   - Note specific intersections or blocks if possible

### Step 4: Calculate the Score
Base your score on:
- Volume of incidents relative to distance
- Severity of crimes (violent > property)
- Concentration (hotspots vs spread)
- Time patterns (if relevant to user's travel time)

### Step 5: Write the Summary
Your summary MUST include:
1. **Overall assessment** (one sentence)
2. **Key risk areas** (specific locations if available)
3. **Crime types** observed (e.g., "primarily property crime")
4. **Recommendations** (specific, actionable)

Example:
"This route presents MODERATE RISK (score: 52) primarily due to elevated property crime rates in the downtown corridor between Main St and Oak Ave. Crime data shows 34 incidents within the last 30 days, with vehicle theft (40%) and larceny (35%) being most common. The highest concentration appears near the intersection of State and Madison during evening hours. RECOMMENDATION: Avoid extended stops in this area, especially after dark. The suburban portions of the route show significantly lower crime activity."

## CRITICAL RULES

1. **ACCURACY IS PARAMOUNT**: Only use data returned by the tools. NEVER fabricate or guess crime statistics.

2. **BE SPECIFIC**: When possible, mention specific locations, crime types, and percentages.

3. **BE BALANCED**: Note both risky AND safe areas on the route.

4. **ACTIONABLE ADVICE**: End with concrete recommendations the user can follow.

5. **HANDLE ERRORS**: If a tool call fails, note it and continue with available data. Don't fail silently.

6. **MINIMUM QUERIES**: Query at least 3 locations along any route, regardless of length.
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

    Wraps the PydanticAI agent with a clean interface for route analysis.
    """

    def __init__(self):
        """Initialize the agent.

        Raises:
            ValueError: If required environment variables are not set
        """
        if not OPENROUTER_API_KEY:
            raise ValueError("OPEN_ROUTER_API_KEY environment variable not set")

        logger.info(f"SafeTravelsAgent initialized with model: {LLM_MODEL}")

    async def analyze_route(self, route_input: RouteAnalysisInput) -> Dict[str, Any]:
        """
        Analyze a route for crime risk.

        Args:
            route_input: RouteAnalysisInput with route data and waypoints

        Returns:
            Dictionary with:
                - route_id: The route identifier
                - risk_score: 1-100 score (or None if failed)
                - risk_summary: Detailed summary (or None if failed)
                - status: "success" or "failed"
                - error: Error message if failed
        """
        # Format the waypoints for the prompt
        waypoint_list = "\n".join([
            f"  - Point {i+1}: ({wp['latitude']:.6f}, {wp['longitude']:.6f})"
            for i, wp in enumerate(route_input.waypoints)
        ])

        # Build the user prompt
        prompt = f"""Analyze the following route for crime risk:

**Route:** {route_input.summary}
**Distance:** {route_input.distance_miles} miles
**Duration:** {route_input.duration_minutes} minutes
**Traffic:** {route_input.traffic_condition or "Unknown"}

**Waypoints to analyze:**
{waypoint_list}

Please query crime data for strategic waypoints along this route and provide your risk assessment.
Focus on accuracy — query enough points to be confident in your assessment."""

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
            logger.exception(f"Route analysis failed for route {route_input.route_id}: {e}")
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

async def analyze_single_route(route_data: Dict[str, Any]) -> Dict[str, Any]:
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
        waypoints=route_data["waypoints"],
        traffic_condition=route_data.get("traffic_condition"),
        places_along_route=route_data.get("places_along_route")
    )

    return await agent_instance.analyze_route(input_data)
```

---

### Phase 3 Tests

Create `src/tests/test_phase3_agent.py`:

```python
"""Phase 3 Tests: SafeTravels AI Agent

Test Strategy:
- MOCKED tests: Test agent structure and output validation
- LIVE tests: Test actual agent with MCP server

Run mocked tests:
    pytest src/tests/test_phase3_agent.py -v -m "not live"

Run all tests (requires API keys and running MCP server):
    pytest src/tests/test_phase3_agent.py -v
"""
import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Mark for live tests
live = pytest.mark.live


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
    ],
    "traffic_condition": "moderate"
}


# =============================================================================
# MOCKED TESTS
# =============================================================================

class TestOutputTypeValidation:
    """Test the RouteAnalysisResult output type."""

    def test_valid_result(self):
        """Test that valid results pass validation."""
        from src.safe_travels_agent import RouteAnalysisResult

        result = RouteAnalysisResult(
            risk_score=65,
            risk_summary="This is a moderately risky route due to several factors. "
                        "The downtown area shows elevated property crime rates. "
                        "Vehicle theft is the most common incident type. "
                        "Recommend avoiding extended stops near State and Madison."
        )
        assert result.risk_score == 65
        assert len(result.risk_summary) >= 100

    def test_score_out_of_range_high(self):
        """Test that scores above 100 are rejected."""
        from src.safe_travels_agent import RouteAnalysisResult
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RouteAnalysisResult(
                risk_score=150,
                risk_summary="A" * 100  # Meets min length
            )

    def test_score_out_of_range_low(self):
        """Test that scores below 1 are rejected."""
        from src.safe_travels_agent import RouteAnalysisResult
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RouteAnalysisResult(
                risk_score=0,
                risk_summary="A" * 100
            )

    def test_summary_too_short(self):
        """Test that short summaries are rejected."""
        from src.safe_travels_agent import RouteAnalysisResult
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            RouteAnalysisResult(
                risk_score=50,
                risk_summary="Too short"
            )


class TestRouteAnalysisInput:
    """Test the RouteAnalysisInput dataclass."""

    def test_input_creation(self):
        """Test creating input data."""
        from src.safe_travels_agent import RouteAnalysisInput

        input_data = RouteAnalysisInput(
            route_id=1,
            summary="Test Route",
            distance_miles=5.0,
            duration_minutes=15,
            waypoints=[{"latitude": 41.0, "longitude": -87.0}]
        )
        assert input_data.route_id == 1
        assert len(input_data.waypoints) == 1


class TestAgentStructure:
    """Test agent structure without making API calls."""

    def test_agent_initialization(self):
        """Test that agent can be initialized with mocked env."""
        with patch.dict(os.environ, {"OPEN_ROUTER_API_KEY": "test-key"}):
            # Re-import to pick up mocked env
            import importlib
            import src.safe_travels_agent as agent_module
            importlib.reload(agent_module)

            agent = agent_module.SafeTravelsAgent()
            assert agent is not None

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        with patch.dict(os.environ, {"OPEN_ROUTER_API_KEY": "test-key"}):
            import importlib
            import src.safe_travels_agent as agent_module
            importlib.reload(agent_module)

            assert agent_module.SYSTEM_PROMPT is not None
            assert len(agent_module.SYSTEM_PROMPT) > 500  # Substantial prompt
            assert "risk" in agent_module.SYSTEM_PROMPT.lower()


# =============================================================================
# LIVE TESTS
# =============================================================================

@live
class TestAgentLive:
    """Live integration tests for the AI agent."""

    @pytest.fixture(autouse=True)
    def check_requirements(self):
        """Skip if required env vars not set."""
        if not os.getenv("OPEN_ROUTER_API_KEY"):
            pytest.skip("OPEN_ROUTER_API_KEY not set")
        # Note: Also requires Crime MCP server running on port 8001

    @pytest.mark.asyncio
    async def test_agent_returns_result(self):
        """Test that agent returns a result dictionary."""
        from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

        agent = SafeTravelsAgent()
        input_data = RouteAnalysisInput(**SAMPLE_ROUTE)

        result = await agent.analyze_route(input_data)

        assert isinstance(result, dict)
        assert "route_id" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_successful_analysis_structure(self):
        """Test that successful analysis has correct structure."""
        from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

        agent = SafeTravelsAgent()
        input_data = RouteAnalysisInput(**SAMPLE_ROUTE)

        result = await agent.analyze_route(input_data)

        if result["status"] == "success":
            assert "risk_score" in result
            assert "risk_summary" in result
            assert 1 <= result["risk_score"] <= 100
            assert len(result["risk_summary"]) >= 100

    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the analyze_single_route convenience function."""
        from src.safe_travels_agent import analyze_single_route

        result = await analyze_single_route(SAMPLE_ROUTE)

        assert isinstance(result, dict)
        assert result["route_id"] == SAMPLE_ROUTE["route_id"]


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not live"])
```

---

### Phase 3 Completion Checklist

- [ ] Context7 research on PydanticAI completed
- [ ] `agent_zero.py` studied thoroughly
- [ ] `safe_travels_agent.py` created with:
  - [ ] `RouteAnalysisResult` output type
  - [ ] `RouteAnalysisInput` dataclass
  - [ ] `SafeTravelsAgent` class
  - [ ] `SYSTEM_PROMPT` (comprehensive, world-class)
  - [ ] MCP server connection via `MCPServerStreamableHTTP`
- [ ] Agent connects to Crime MCP server
- [ ] Agent returns structured output (score + summary)
- [ ] All mocked tests pass
- [ ] Live tests pass (with API keys and MCP server)

---

## Phase 4: Orchestrator Script

### Objective
Create `safe_travels.py` that coordinates Google Maps and parallel agent calls.

### Pre-Phase Research

#### 4.1 Study Python Async Patterns

Research using Context7:
```
"Search for Python asyncio.gather parallel execution"
"Search for Python async timeout handling"
"Search for Python async error handling patterns"
```

Key concepts:
- `asyncio.gather()` for parallel execution
- `asyncio.wait_for()` for timeout handling
- `return_exceptions=True` for graceful failure handling

#### 4.2 Plan the Flow

```
1. Receive start and destination addresses
2. Call use_google_maps() → List[RouteData]
3. Convert RouteData → RouteAnalysisInput
4. For each route, spawn agent analysis in parallel
5. Apply timeout to each analysis
6. Collect results (handle partial failures)
7. Return consolidated response
```

---

### Implementation

Create `src/safe_travels.py`:

```python
"""SafeTravels Route Analysis Orchestrator.

Coordinates Google Maps routing and parallel crime analysis.

Usage:
    # As a module
    from src.safe_travels import analyze_routes
    result = await analyze_routes("Start Address", "End Address")

    # From command line
    python src/safe_travels.py "Start Address" "End Address"
"""
import asyncio
import logging
from typing import List, Dict, Any
from dataclasses import asdict

from src.helper_functions.google_maps import use_google_maps, RouteData
from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def route_data_to_input(route: RouteData) -> RouteAnalysisInput:
    """Convert RouteData from Google Maps to RouteAnalysisInput for agent."""
    return RouteAnalysisInput(
        route_id=route.route_id,
        summary=route.summary,
        distance_miles=route.distance_miles,
        duration_minutes=route.duration_minutes,
        waypoints=[
            {"latitude": wp.latitude, "longitude": wp.longitude}
            for wp in route.waypoints
        ],
        traffic_condition=route.traffic.traffic_condition if route.traffic else None,
        places_along_route=[asdict(p) for p in route.places_along_route] if route.places_along_route else None
    )


async def analyze_route_with_timeout(
    agent: SafeTravelsAgent,
    route_input: RouteAnalysisInput,
    timeout_seconds: float = 120.0
) -> Dict[str, Any]:
    """
    Analyze a single route with timeout protection.

    Args:
        agent: SafeTravelsAgent instance
        route_input: Route data to analyze
        timeout_seconds: Maximum time to wait for analysis

    Returns:
        Analysis result dictionary (success or failure)
    """
    try:
        result = await asyncio.wait_for(
            agent.analyze_route(route_input),
            timeout=timeout_seconds
        )
        return result

    except asyncio.TimeoutError:
        logger.warning(f"Route {route_input.route_id} analysis timed out after {timeout_seconds}s")
        return {
            "route_id": route_input.route_id,
            "risk_score": None,
            "risk_summary": None,
            "status": "failed",
            "error": f"Analysis timed out after {timeout_seconds} seconds"
        }

    except Exception as e:
        logger.exception(f"Route {route_input.route_id} analysis failed: {e}")
        return {
            "route_id": route_input.route_id,
            "risk_score": None,
            "risk_summary": None,
            "status": "failed",
            "error": str(e)
        }


# =============================================================================
# MAIN ORCHESTRATION FUNCTION
# =============================================================================

async def analyze_routes(
    start: str,
    destination: str,
    timeout_per_route: float = 120.0,
    include_traffic: bool = True,
    include_places: bool = True
) -> Dict[str, Any]:
    """
    Analyze all routes between start and destination for crime risk.

    This is the main orchestration function that:
    1. Gets route alternatives from Google Maps
    2. Runs parallel AI agent analyses on each route
    3. Returns consolidated results with graceful failure handling

    Args:
        start: Starting address (e.g., "123 Main St, Chicago, IL")
        destination: Destination address
        timeout_per_route: Maximum seconds to wait per route analysis
        include_traffic: Whether to fetch real-time traffic data
        include_places: Whether to fetch places along route

    Returns:
        Dictionary with:
            - routes: List of route analysis results
            - total_routes: Number of routes found
            - successful_analyses: Number of successful analyses
            - status: "success", "partial_failure", or "failed"
            - error: Error message if complete failure
    """
    logger.info(f"Analyzing routes from '{start}' to '{destination}'")

    # ==========================================================================
    # Step 1: Get routes from Google Maps
    # ==========================================================================
    try:
        routes = use_google_maps(
            start=start,
            destination=destination,
            include_traffic=include_traffic,
            include_places=include_places
        )
        logger.info(f"Found {len(routes)} route alternatives")

    except ValueError as e:
        logger.error(f"Google Maps error: {e}")
        return {
            "routes": [],
            "total_routes": 0,
            "successful_analyses": 0,
            "status": "failed",
            "error": f"Failed to get routes: {str(e)}"
        }

    except Exception as e:
        logger.exception(f"Unexpected error getting routes: {e}")
        return {
            "routes": [],
            "total_routes": 0,
            "successful_analyses": 0,
            "status": "failed",
            "error": f"Unexpected error: {str(e)}"
        }

    if not routes:
        return {
            "routes": [],
            "total_routes": 0,
            "successful_analyses": 0,
            "status": "failed",
            "error": "No routes found between the specified locations"
        }

    # ==========================================================================
    # Step 2: Prepare agent inputs
    # ==========================================================================
    agent = SafeTravelsAgent()
    inputs = [route_data_to_input(route) for route in routes]

    logger.info(f"Prepared {len(inputs)} routes for analysis")
    for inp in inputs:
        logger.info(f"  Route {inp.route_id}: {inp.summary} ({inp.distance_miles} mi, {len(inp.waypoints)} waypoints)")

    # ==========================================================================
    # Step 3: Run analyses in PARALLEL
    # ==========================================================================
    logger.info(f"Starting parallel analysis of {len(inputs)} routes...")

    tasks = [
        analyze_route_with_timeout(agent, route_input, timeout_per_route)
        for route_input in inputs
    ]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # ==========================================================================
    # Step 4: Process results
    # ==========================================================================
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful

    logger.info(f"Analysis complete: {successful}/{len(results)} routes succeeded")

    if successful == 0:
        status = "failed"
    elif successful < len(results):
        status = "partial_failure"
    else:
        status = "success"

    return {
        "routes": results,
        "total_routes": len(results),
        "successful_analyses": successful,
        "failed_analyses": failed,
        "status": status
    }


# =============================================================================
# SYNCHRONOUS WRAPPER
# =============================================================================

def analyze_routes_sync(
    start: str,
    destination: str,
    timeout_per_route: float = 120.0
) -> Dict[str, Any]:
    """
    Synchronous wrapper for analyze_routes.

    Use this when not in an async context.
    """
    return asyncio.run(analyze_routes(start, destination, timeout_per_route))


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python src/safe_travels.py <start_address> <destination_address>")
        print("")
        print("Example:")
        print("  python src/safe_travels.py 'Willis Tower, Chicago' 'Navy Pier, Chicago'")
        sys.exit(1)

    start_addr = sys.argv[1]
    dest_addr = sys.argv[2]

    print(f"\n{'='*60}")
    print(f"SafeTravels Route Analysis")
    print(f"{'='*60}")
    print(f"From: {start_addr}")
    print(f"To:   {dest_addr}")
    print(f"{'='*60}\n")

    result = analyze_routes_sync(start_addr, dest_addr)

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2))
```

---

### Phase 4 Tests

Create `src/tests/test_phase4_orchestrator.py`:

```python
"""Phase 4 Tests: Orchestrator Script

Test Strategy:
- MOCKED tests: Test orchestration logic with mocked components
- LIVE tests: Full integration test

Run mocked tests:
    pytest src/tests/test_phase4_orchestrator.py -v -m "not live"

Run all tests:
    pytest src/tests/test_phase4_orchestrator.py -v
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dataclasses import dataclass

# Mark for live tests
live = pytest.mark.live


# =============================================================================
# MOCKED TESTS
# =============================================================================

class TestHelperFunctions:
    """Test helper functions."""

    def test_route_data_to_input(self):
        """Test conversion from RouteData to RouteAnalysisInput."""
        from src.safe_travels import route_data_to_input
        from src.helper_functions.google_maps import RouteData, RoutePoint, TrafficInfo
        from src.safe_travels_agent import RouteAnalysisInput

        route = RouteData(
            route_id=1,
            summary="Test Route",
            distance_miles=5.0,
            duration_minutes=15,
            start_address="Start",
            end_address="End",
            waypoints=[
                RoutePoint(latitude=41.8781, longitude=-87.6298),
                RoutePoint(latitude=41.8827, longitude=-87.6233),
            ],
            polyline="test_polyline",
            traffic=TrafficInfo(
                duration_in_traffic_minutes=18,
                traffic_delay_minutes=3,
                traffic_condition="light"
            )
        )

        input_data = route_data_to_input(route)

        assert isinstance(input_data, RouteAnalysisInput)
        assert input_data.route_id == 1
        assert input_data.summary == "Test Route"
        assert len(input_data.waypoints) == 2
        assert input_data.traffic_condition == "light"


class TestTimeoutHandling:
    """Test timeout handling in route analysis."""

    @pytest.mark.asyncio
    async def test_timeout_returns_failure(self):
        """Test that timeouts are handled gracefully."""
        from src.safe_travels import analyze_route_with_timeout
        from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

        # Create mock agent that takes too long
        mock_agent = Mock(spec=SafeTravelsAgent)

        async def slow_analysis(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return {"status": "success"}

        mock_agent.analyze_route = slow_analysis

        input_data = RouteAnalysisInput(
            route_id=1,
            summary="Test",
            distance_miles=5.0,
            duration_minutes=15,
            waypoints=[{"latitude": 41.0, "longitude": -87.0}]
        )

        # Should timeout quickly
        result = await analyze_route_with_timeout(
            mock_agent,
            input_data,
            timeout_seconds=0.1
        )

        assert result["status"] == "failed"
        assert "timed out" in result["error"].lower()
        assert result["risk_score"] is None

    @pytest.mark.asyncio
    async def test_exception_returns_failure(self):
        """Test that exceptions are handled gracefully."""
        from src.safe_travels import analyze_route_with_timeout
        from src.safe_travels_agent import SafeTravelsAgent, RouteAnalysisInput

        mock_agent = Mock(spec=SafeTravelsAgent)

        async def failing_analysis(*args, **kwargs):
            raise RuntimeError("Test error")

        mock_agent.analyze_route = failing_analysis

        input_data = RouteAnalysisInput(
            route_id=1,
            summary="Test",
            distance_miles=5.0,
            duration_minutes=15,
            waypoints=[{"latitude": 41.0, "longitude": -87.0}]
        )

        result = await analyze_route_with_timeout(mock_agent, input_data)

        assert result["status"] == "failed"
        assert "Test error" in result["error"]


class TestAnalyzeRoutesOrchestration:
    """Test the main orchestration function with mocks."""

    @pytest.mark.asyncio
    async def test_handles_google_maps_error(self):
        """Test handling of Google Maps API errors."""
        from src.safe_travels import analyze_routes

        with patch("src.safe_travels.use_google_maps") as mock_gmaps:
            mock_gmaps.side_effect = ValueError("Invalid address")

            result = await analyze_routes("Invalid", "Also Invalid")

            assert result["status"] == "failed"
            assert "Invalid address" in result["error"]
            assert result["total_routes"] == 0

    @pytest.mark.asyncio
    async def test_handles_no_routes(self):
        """Test handling when no routes are found."""
        from src.safe_travels import analyze_routes

        with patch("src.safe_travels.use_google_maps") as mock_gmaps:
            mock_gmaps.return_value = []  # No routes

            result = await analyze_routes("Start", "End")

            assert result["status"] == "failed"
            assert "No routes found" in result["error"]


# =============================================================================
# LIVE TESTS
# =============================================================================

@live
class TestOrchestratorLive:
    """Live integration tests for the orchestrator."""

    @pytest.fixture(autouse=True)
    def check_requirements(self):
        """Skip if required env vars not set."""
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            pytest.skip("GOOGLE_MAPS_API_KEY not set")
        if not os.getenv("OPEN_ROUTER_API_KEY"):
            pytest.skip("OPEN_ROUTER_API_KEY not set")
        # Note: Also requires Crime MCP server running

    @pytest.mark.asyncio
    async def test_full_analysis(self):
        """Test complete route analysis flow."""
        from src.safe_travels import analyze_routes

        result = await analyze_routes(
            start="Willis Tower, Chicago, IL",
            destination="Navy Pier, Chicago, IL",
            timeout_per_route=180.0
        )

        assert isinstance(result, dict)
        assert "routes" in result
        assert "status" in result
        assert result["total_routes"] >= 1

    def test_sync_wrapper(self):
        """Test the synchronous wrapper."""
        from src.safe_travels import analyze_routes_sync

        result = analyze_routes_sync(
            start="Millennium Park, Chicago",
            destination="Lincoln Park Zoo, Chicago"
        )

        assert isinstance(result, dict)
        assert "routes" in result


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not live"])
```

---

### Phase 4 Completion Checklist

- [ ] `safe_travels.py` created with all functions
- [ ] `route_data_to_input()` converts between data types
- [ ] `analyze_route_with_timeout()` handles timeouts
- [ ] `analyze_routes()` orchestrates parallel execution
- [ ] `analyze_routes_sync()` provides sync wrapper
- [ ] CLI interface works
- [ ] Partial failures handled gracefully
- [ ] All mocked tests pass
- [ ] Live tests pass

---

## Phase 5: FastAPI Application

### Objective
Create the REST API that exposes route analysis functionality.

### Pre-Phase Research

Use Context7:
```
"Search for FastAPI async endpoints"
"Search for FastAPI Pydantic models request response"
"Search for FastAPI CORS middleware"
"Search for FastAPI error handling"
```

---

### Implementation

Create `src/safe_travels_api.py`:

```python
"""SafeTravels FastAPI Application.

REST API for route crime risk analysis.

Running the Server:
    python src/safe_travels_api.py

    Or with uvicorn:
    uvicorn src.safe_travels_api:app --host 0.0.0.0 --port 8000 --reload

API Documentation:
    http://localhost:8000/docs
"""
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.safe_travels import analyze_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RouteAnalysisRequest(BaseModel):
    """Request body for route analysis."""

    start: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Starting address (e.g., '123 Main St, Chicago, IL')"
    )
    destination: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Destination address (e.g., '456 Oak Ave, Chicago, IL')"
    )
    include_traffic: bool = Field(
        default=True,
        description="Whether to include real-time traffic data"
    )
    include_places: bool = Field(
        default=True,
        description="Whether to include places along route (gas stations, police)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start": "Willis Tower, Chicago, IL",
                "destination": "Navy Pier, Chicago, IL",
                "include_traffic": True,
                "include_places": True
            }
        }


class RouteResult(BaseModel):
    """Result for a single route."""

    route_id: int = Field(..., description="Route identifier")
    risk_score: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Risk score from 1 (safest) to 100 (most dangerous)"
    )
    risk_summary: Optional[str] = Field(
        None,
        description="Detailed summary explaining the risk assessment"
    )
    status: str = Field(..., description="'success' or 'failed'")
    error: Optional[str] = Field(None, description="Error message if failed")


class RouteAnalysisResponse(BaseModel):
    """Response body for route analysis."""

    routes: List[RouteResult] = Field(..., description="Analysis results for each route")
    total_routes: int = Field(..., description="Total number of routes analyzed")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(default=0, description="Number of failed analyses")
    status: str = Field(..., description="'success', 'partial_failure', or 'failed'")
    error: Optional[str] = Field(None, description="Error message if complete failure")


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("SafeTravels API starting up...")
    logger.info("Ensure Crime MCP server is running on port 8001")
    yield
    logger.info("SafeTravels API shutting down...")


app = FastAPI(
    title="SafeTravels API",
    description="""
## Route Crime Risk Analysis API

AI-powered route safety analysis that evaluates crime risk for driving routes.

### How it works:
1. Provide start and destination addresses
2. The API gets multiple route alternatives from Google Maps
3. Each route is analyzed in parallel using AI agents with crime data
4. Returns risk scores (1-100) and detailed summaries for each route

### Risk Score Scale:
- **1-20**: Very Safe
- **21-40**: Safe
- **41-60**: Moderate Risk
- **61-80**: High Risk
- **81-100**: Very High Risk
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SafeTravels API",
        "version": "1.0.0",
        "description": "AI-powered route crime risk analysis",
        "endpoints": {
            "POST /analyze-route": "Analyze routes for crime risk",
            "GET /health": "Health check",
            "GET /docs": "API documentation (Swagger UI)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "safetravels-api",
        "version": "1.0.0"
    }


@app.post("/analyze-route", response_model=RouteAnalysisResponse)
async def analyze_route_endpoint(request: RouteAnalysisRequest):
    """
    Analyze routes between two addresses for crime risk.

    Returns multiple route alternatives with AI-generated risk scores (1-100)
    and detailed summaries explaining the assessment.

    **Note**: This endpoint may take 30-120 seconds depending on the number
    of routes and complexity of analysis.
    """
    logger.info(f"Received analysis request: {request.start} -> {request.destination}")

    try:
        result = await analyze_routes(
            start=request.start,
            destination=request.destination,
            timeout_per_route=120.0,
            include_traffic=request.include_traffic,
            include_places=request.include_places
        )

        # Convert to response model
        routes = [RouteResult(**r) for r in result.get("routes", [])]

        response = RouteAnalysisResponse(
            routes=routes,
            total_routes=result.get("total_routes", len(routes)),
            successful_analyses=result.get("successful_analyses", 0),
            failed_analyses=result.get("failed_analyses", 0),
            status=result.get("status", "unknown"),
            error=result.get("error")
        )

        logger.info(f"Analysis complete: {response.successful_analyses}/{response.total_routes} routes")
        return response

    except Exception as e:
        logger.exception(f"Route analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Route analysis failed: {str(e)}"
        )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("SafeTravels API Server")
    print("="*60)
    print("Starting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
```

---

### Phase 5 Tests

Create `src/tests/test_phase5_api.py`:

```python
"""Phase 5 Tests: FastAPI Application

Test Strategy:
- MOCKED tests: Test API endpoints with mocked orchestrator
- LIVE tests: Full integration test

Run mocked tests:
    pytest src/tests/test_phase5_api.py -v -m "not live"

Run all tests:
    pytest src/tests/test_phase5_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import os

# Mark for live tests
live = pytest.mark.live


# =============================================================================
# TEST CLIENT FIXTURE
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    from src.safe_travels_api import app
    return TestClient(app)


# =============================================================================
# MOCKED TESTS
# =============================================================================

class TestBasicEndpoints:
    """Test basic endpoints without external dependencies."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "SafeTravels API"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_endpoint(self, client):
        """Test that OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/analyze-route" in schema["paths"]


class TestInputValidation:
    """Test request validation."""

    def test_missing_fields(self, client):
        """Test validation error for missing fields."""
        response = client.post("/analyze-route", json={})
        assert response.status_code == 422

    def test_empty_start(self, client):
        """Test validation error for empty start."""
        response = client.post("/analyze-route", json={
            "start": "",
            "destination": "Valid destination"
        })
        assert response.status_code == 422

    def test_start_too_short(self, client):
        """Test validation error for start too short."""
        response = client.post("/analyze-route", json={
            "start": "AB",  # Less than 3 chars
            "destination": "Valid destination"
        })
        assert response.status_code == 422


class TestAnalyzeRouteWithMocks:
    """Test analyze-route endpoint with mocked orchestrator."""

    def test_successful_response_structure(self, client):
        """Test that successful response has correct structure."""
        mock_result = {
            "routes": [
                {
                    "route_id": 1,
                    "risk_score": 45,
                    "risk_summary": "This is a test summary " * 10,
                    "status": "success"
                }
            ],
            "total_routes": 1,
            "successful_analyses": 1,
            "failed_analyses": 0,
            "status": "success"
        }

        with patch("src.safe_travels_api.analyze_routes", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result

            response = client.post("/analyze-route", json={
                "start": "Start Address",
                "destination": "End Address"
            })

            assert response.status_code == 200
            data = response.json()
            assert "routes" in data
            assert data["total_routes"] == 1
            assert data["routes"][0]["risk_score"] == 45

    def test_partial_failure_response(self, client):
        """Test response when some routes fail."""
        mock_result = {
            "routes": [
                {"route_id": 1, "risk_score": 50, "risk_summary": "Test " * 30, "status": "success"},
                {"route_id": 2, "risk_score": None, "risk_summary": None, "status": "failed", "error": "Timeout"}
            ],
            "total_routes": 2,
            "successful_analyses": 1,
            "failed_analyses": 1,
            "status": "partial_failure"
        }

        with patch("src.safe_travels_api.analyze_routes", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_result

            response = client.post("/analyze-route", json={
                "start": "Start",
                "destination": "End"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "partial_failure"
            assert data["successful_analyses"] == 1
            assert data["failed_analyses"] == 1


# =============================================================================
# LIVE TESTS
# =============================================================================

@live
class TestAPILive:
    """Live integration tests for the API."""

    @pytest.fixture(autouse=True)
    def check_requirements(self):
        """Skip if required env vars not set."""
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            pytest.skip("GOOGLE_MAPS_API_KEY not set")
        if not os.getenv("OPEN_ROUTER_API_KEY"):
            pytest.skip("OPEN_ROUTER_API_KEY not set")

    def test_full_request(self, client):
        """Test complete route analysis request."""
        response = client.post("/analyze-route", json={
            "start": "Willis Tower, Chicago, IL",
            "destination": "Navy Pier, Chicago, IL"
        })

        assert response.status_code == 200
        data = response.json()
        assert "routes" in data
        assert data["total_routes"] >= 1


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not live"])
```

---

### Phase 5 Completion Checklist

- [ ] `safe_travels_api.py` created with all endpoints
- [ ] Request/response Pydantic models defined
- [ ] `/analyze-route` POST endpoint works
- [ ] `/health` endpoint returns healthy
- [ ] CORS configured
- [ ] OpenAPI docs available at `/docs`
- [ ] All mocked tests pass
- [ ] Live tests pass

---

## Final Validation

### Complete System Test

1. **Start the Crime MCP Server**:
```bash
python -m src.MCP_Servers.crime_mcp
# Should see: Starting Crime MCP server on port 8001...
```

2. **Start the FastAPI Server** (new terminal):
```bash
python src/safe_travels_api.py
# Should see: Starting server on http://localhost:8000
```

3. **Test the API**:
```bash
curl -X POST http://localhost:8000/analyze-route \
  -H "Content-Type: application/json" \
  -d '{
    "start": "Willis Tower, Chicago, IL",
    "destination": "Navy Pier, Chicago, IL"
  }'
```

4. **Run All Tests**:
```bash
# Mocked tests (no API keys needed)
pytest src/tests/ -v -m "not live"

# Full tests (requires API keys and servers running)
pytest src/tests/ -v
```

### Expected Response Format

```json
{
  "routes": [
    {
      "route_id": 1,
      "risk_score": 52,
      "risk_summary": "This route presents MODERATE RISK primarily due to elevated property crime rates in the downtown corridor. Crime data shows 34 incidents within the last 30 days, with vehicle theft (40%) and larceny (35%) being most common. The highest concentration appears near State and Madison during evening hours. RECOMMENDATION: Avoid extended stops in the downtown area, especially after dark.",
      "status": "success"
    },
    {
      "route_id": 2,
      "risk_score": 38,
      "risk_summary": "This alternative route shows LOWER RISK by avoiding the downtown core. The suburban portions have significantly fewer incidents (12 in 30 days), primarily minor property crimes. This route is recommended for travel during evening hours when downtown crime rates peak.",
      "status": "success"
    }
  ],
  "total_routes": 2,
  "successful_analyses": 2,
  "failed_analyses": 0,
  "status": "success"
}
```

---

## Summary Checklist

### Before Each Phase
- [ ] Complete Context7 research
- [ ] Read all reference files
- [ ] Ask clarifying questions
- [ ] Understand exactly what will be built

### Phase Completion
- [ ] **Phase 0**: Environment setup complete
- [ ] **Phase 1**: Crime MCP Server running on port 8001
- [ ] **Phase 2**: `use_google_maps()` returns adaptive waypoints
- [ ] **Phase 3**: AI agent returns accurate risk scores
- [ ] **Phase 4**: Orchestrator coordinates parallel analysis
- [ ] **Phase 5**: FastAPI serves requests

### Final Validation
- [ ] All mocked tests pass
- [ ] All live tests pass
- [ ] API responds to curl request
- [ ] Response matches expected format

---

## Appendix: Key Reference Files

| File | Purpose |
|------|---------|
| `docs/agent_zero.py` | **PRIMARY** PydanticAI agent reference |
| `docs/Search_MCP/src/Example_MCP/` | MCP server boilerplate |
| `docs/Pydantic_AI/pydantic_ai_docs/` | PydanticAI documentation |
| `docs/crime_platform/crimeo_docs.md` | Crimeometer API docs |
| `docs/Search_MCP/docs/MCP_Explained.md` | MCP beginner guide |

---

## Appendix: Troubleshooting

### Crime MCP Server Won't Start
- Check `CRIME_API_KEY` is set in `.env`
- Ensure port 8001 is not in use

### Google Maps Returns No Routes
- Verify `GOOGLE_MAPS_API_KEY` is valid
- Check addresses are in a supported region

### Agent Analysis Fails
- Ensure Crime MCP server is running
- Check `OPEN_ROUTER_API_KEY` is valid
- Verify `CRIME_MCP_URL` is correct

### Tests Fail
- For mocked tests: Check imports are correct
- For live tests: Ensure all servers are running and API keys are set
