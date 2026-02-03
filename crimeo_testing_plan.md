# Crimeo API Testing Plan

> **Goal**: Call the Crimeo Raw Data endpoint for downtown Chicago, save the response as JSON, and analyze what we're working with before building the MCP server.

---

## Background

Crimeo is a crime data API. You give it a GPS coordinate, a radius, and a date range. It returns individual crime incidents from official police records. Chicago is one of 30+ supported US cities.

For full API reference, see `docs/crime_platform/crimeo_explained.md`.

---

## What the Test Does

One Python script (`src/tests/test_crimeo_api.py`) that:

1. Calls the **Raw Data** endpoint for downtown Chicago
2. Saves the full response to `src/tests/crimeo_raw_data_chicago.json`
3. Prints a summary to the console (total incidents, crime type breakdown)

No pytest. No assertions. Just a simple script that hits the API and saves what comes back.

---

## Test Parameters

| Parameter | Value | Why |
|-----------|-------|-----|
| `lat` | `41.8781` | Downtown Chicago (The Loop, near Willis Tower) |
| `lon` | `-87.6298` | Downtown Chicago |
| `distance` | `2mi` | 2-mile radius. Production will use 1mi, but we want more data for analysis. |
| `datetime_ini` | 6 months before today | Calculated at runtime. Format: `yyyy-MM-ddT00:00:00.000Z` |
| `datetime_end` | Today | Calculated at runtime. Same format. |
| `page` | `1` | First 100 results only |

---

## API Call Details

### Endpoint

```
GET https://api.crimeometer.com/v1/incidents/raw-data
```

### Headers

```
Content-Type: application/json
x-api-key: <value of CRIMEO_API from .env file>
```

### Full URL Example

```
https://api.crimeometer.com/v1/incidents/raw-data?lat=41.8781&lon=-87.6298&distance=2mi&datetime_ini=2025-07-26T00:00:00.000Z&datetime_end=2026-01-26T00:00:00.000Z&page=1
```

---

## How to Run

### Prerequisites

1. Python 3.10+
2. `requests` and `python-dotenv` installed (`pip install requests python-dotenv`)
3. `.env` file in project root with: `CRIMEO_API=<your-key>`

### Run

From the project root:

```bash
python src/tests/test_crimeo_api.py
```

### Expected Console Output

```
=== Crimeo Raw Data API Test ===
Location: lat=41.8781, lon=-87.6298 (Downtown Chicago)
Radius: 2mi
Date range: 2025-07-26 to 2026-01-26

Status: 200 OK
Total incidents: 247
Total pages: 3

Crime Type Breakdown:
  Theft/Larceny: 45
  Motor Vehicle Theft: 32
  Assault: 28
  ...

Saved to: src/tests/crimeo_raw_data_chicago.json
```

### File Created

```
src/tests/crimeo_raw_data_chicago.json
```

---

## What to Look for in the JSON

After running, open `crimeo_raw_data_chicago.json` and check:

1. **Volume**: How many `total_incidents`? Is 100 per page enough or do we need pagination?
2. **Crime types**: What `incident_offense` values appear? Are the ones we care about present (Motor Vehicle Theft, Robbery, Theft, Assault)?
3. **Data quality**: Are `incident_offense_detail_description` values useful? Are addresses present?
4. **Recency**: Are the dates actually recent, or is the data stale?
5. **Geography**: Are `incident_latitude`/`incident_longitude` values actually within Chicago?

---

## After Testing

1. **Update** `docs/crime_platform/crimeo_explained.md` -- fill in the "Test Results Analysis" section
2. **Proceed** to building the Crime MCP Server (Phase 1 of `refactor_plan.md`)

---

## Script Location

```
src/tests/test_crimeo_api.py
```
