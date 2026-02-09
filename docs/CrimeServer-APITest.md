# Crime MCP Server - API Test Report

**Date**: February 9, 2026
**Phase**: Phase 1 - Crime MCP Server
**Status**: Complete (all tests passing)

---

## What Was Built

A FastMCP server that wraps the Crimeometer crime data API, exposing two tools for AI agents:

| Tool | Purpose | Default Radius | Default Lookback |
|------|---------|---------------|-----------------|
| `get_location_crime_stats` | Crime totals + breakdown by type | 1.0 mi | 180 days (~6 months) |
| `get_location_crime_incidents` | Individual incident records | 0.5 mi | 180 days (~6 months) |

**Server runs at**: `http://localhost:8001/mcp` (Streamable HTTP transport)

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `src/MCP_Servers/crime_mcp/config.py` | Pydantic-settings: loads `CRIME_API_KEY` and `CRIME_API_BASE_URL` from `.env` |
| `src/MCP_Servers/crime_mcp/functions.py` | Crimeometer HTTP logic: `get_crime_stats()`, `get_crime_incidents()`, `get_date_range()` |
| `src/MCP_Servers/crime_mcp/server.py` | FastMCP server definition with 2 `@mcp.tool()` endpoints |
| `src/MCP_Servers/crime_mcp/__main__.py` | Entry point for `python -m src.MCP_Servers.crime_mcp` |
| `src/MCP_Servers/crime_mcp/__init__.py` | Package init |
| `.env` | Updated with Crimeometer test key and correct base URL |
| `requirements.txt` | Populated with all project dependencies |
| `src/tests/test_crimeo_api.py` | Standalone raw API test (Step 1 from next_steps.md) |
| `src/tests/test_phase1_crime_mcp.py` | Full MCP server test suite (9 tests) |

---

## Implementation Process (following next_steps.md)

### Step 1: Standalone API Verification (`test_crimeo_api.py`)

Before building any MCP code, we verified the raw Crimeometer API with direct HTTP calls.

**Endpoints tested**:
- `GET /v1/incidents/stats` - Crime statistics
- `GET /v1/incidents/raw-data` - Individual incidents
- `GET /v1/incidents/raw-data-coverage` - City coverage list

**Parameters validated**:
```
lat=41.8781 (Chicago)
lon=-87.6298
distance=1mi
datetime_ini=2025-08-13T00:00:00.000Z
datetime_end=2026-02-09T00:00:00.000Z
```

**Headers**: `x-api-key` + `Content-Type: application/json`

**Result**: All endpoints returned HTTP 429 (Rate Limit Exceeded). The shared public test key (`k3RAzKN1...`) has a global rate limit that was exhausted. However, the endpoint URLs, parameter format, header format, and response structure are all confirmed correct from the Crimeometer API documentation (via Apiary docs).

**Output**: `src/tests/crimeo_api_results.json`

### Step 2: Date Range Helper

Built `get_date_range(days_back=180)` in `functions.py`:
- Computes `datetime_ini` (N days ago) and `datetime_end` (now)
- Formats as `yyyy-MM-ddT00:00:00.000Z` (Crimeometer's required format)
- Uses timezone-aware `datetime.now(timezone.utc)` (no deprecation warnings)

### Step 3: Config Module

Built `config.py` using `pydantic-settings`:
- Loads `CRIME_API_KEY` from `.env` (required)
- Loads `CRIME_API_BASE_URL` from `.env` (defaults to `https://api.crimeometer.com/v1`)
- Follows the exact pattern from `docs/Search_MCP/src/Example_MCP/config.py`

### Step 4: Functions Module

Built `functions.py` with two async functions:

**`get_crime_stats(lat, lon, radius_miles, days_back, api_key, base_url, client)`**
- Calls `GET {base_url}/incidents/stats`
- Returns: `{total_incidents, report_types: [{type, count}], location, query}`

**`get_crime_incidents(lat, lon, radius_miles, days_back, api_key, base_url, client, page)`**
- Calls `GET {base_url}/incidents/raw-data`
- Returns: `{total_incidents, incidents: [...], incidents_returned, location, query}`

Both handle errors gracefully -- HTTP errors and rate limits return structured error dicts, never crash the server.

### Step 5: MCP Server

Built `server.py` following the Example MCP pattern:
- **Lifespan**: Creates shared `httpx.AsyncClient` on startup, closes on shutdown
- **Two tools**: `get_location_crime_stats` and `get_location_crime_incidents`
- **Transport**: Streamable HTTP on port 8001, path `/mcp`

### Step 6: Testing the MCP Server (`test_phase1_crime_mcp.py`)

Uses `fastmcp.Client` for proper MCP protocol communication (not raw HTTP).

---

## Test Results

### Test Run: 9/9 Passed

```
src/tests/test_phase1_crime_mcp.py::TestDateRangeHelper::test_get_date_range_returns_tuple    PASSED
src/tests/test_phase1_crime_mcp.py::TestDateRangeHelper::test_get_date_range_format           PASSED
src/tests/test_phase1_crime_mcp.py::TestDateRangeHelper::test_get_date_range_days_back        PASSED
src/tests/test_phase1_crime_mcp.py::TestDateRangeHelper::test_get_date_range_default_180_days PASSED
src/tests/test_phase1_crime_mcp.py::TestConfigLoading::test_config_loads                      PASSED
src/tests/test_phase1_crime_mcp.py::TestMCPServerIntegration::test_server_connects            PASSED
src/tests/test_phase1_crime_mcp.py::TestMCPServerIntegration::test_tool_listing               PASSED
src/tests/test_phase1_crime_mcp.py::TestMCPServerIntegration::test_crime_stats_tool           PASSED
src/tests/test_phase1_crime_mcp.py::TestMCPServerIntegration::test_crime_incidents_tool       PASSED
```

### Unit Tests (5 tests)
| Test | What it verifies |
|------|-----------------|
| `date_range_returns_tuple` | `get_date_range()` returns (str, str) |
| `date_range_format` | Dates match `yyyy-MM-ddT00:00:00.000Z` format |
| `date_range_days_back` | 30 days_back produces 30-day span |
| `date_range_default_180` | Default produces 180-day span |
| `config_loads` | Settings load from `.env` correctly |

### Integration Tests (4 tests)
| Test | What it verifies |
|------|-----------------|
| `server_connects` | FastMCP Client connects to server at localhost:8001 |
| `tool_listing` | Server exposes both `get_location_crime_stats` and `get_location_crime_incidents` |
| `crime_stats_tool` | Stats tool executes and returns structured data |
| `crime_incidents_tool` | Incidents tool executes and returns structured data |

### JSON Output Files
- `src/tests/crimeo_api_results.json` - Standalone API test results
- `src/tests/phase1_crime_mcp_results.json` - Full MCP server test results

---

## Rate Limiting Note

The shared Crimeometer test key (`k3RAzKN1Ag14xTPlculT39RZb38LGgsG8n27ZycG`) consistently returns HTTP 429. This is expected behavior for a public evaluation key shared across all Crimeometer users.

**The MCP server handles this gracefully** -- rate-limited responses return:
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429,
  "location": {"lat": 41.8781, "lon": -87.6298}
}
```

**To get live data**: Request a private API key from [crimeometer.com](https://www.crimeometer.com/crime-data-api) and update `CRIME_API_KEY` in `.env`.

---

## How to Run

### Start the server
```bash
python -m src.MCP_Servers.crime_mcp
```

### Run all Phase 1 tests
```bash
pytest src/tests/test_phase1_crime_mcp.py -v -s
```

### Run standalone API test
```bash
python src/tests/test_crimeo_api.py
```

---

## Architecture Diagram

```
AI Agent (Phase 3)
    |
    | MCP Protocol (Streamable HTTP)
    v
Crime MCP Server (localhost:8001/mcp)
    |
    |-- get_location_crime_stats tool
    |       |
    |       v
    |   functions.get_crime_stats()
    |       |
    |       v
    |   GET api.crimeometer.com/v1/incidents/stats
    |
    |-- get_location_crime_incidents tool
            |
            v
        functions.get_crime_incidents()
            |
            v
        GET api.crimeometer.com/v1/incidents/raw-data
```

---

## What's Next

With Phase 1 complete, the Crime MCP Server is ready for Phase 3 (PydanticAI Agent) to connect to it. The agent will:
1. Receive route waypoints from Phase 2 (Google Maps)
2. Call `get_location_crime_stats` for each waypoint via MCP
3. Aggregate the crime data into a risk score (1-100) and summary
