# SafeTravels API — Master Plan

> **AI-Powered Route Safety Analysis**

**Author:** Snigdha  
**Version:** 2.0 | January 2026

---

## 🎯 Project Vision

Build a **clean, elegant API** that takes a start address and destination address, returns multiple routes with AI-generated crime risk scores (1-100) and summaries for each route.

---

## 🏗️ Architecture Overview

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
                                │  - Uses Crimeometer API               │
                                └───────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API** | FastAPI | REST endpoint |
| **Route Data** | Google Maps Directions API | Get multiple route alternatives |
| **Crime Data** | Crimeometer API | Real-time crime statistics |
| **AI Agent** | PydanticAI | Analyze routes, generate scores |
| **MCP Server** | FastMCP | Expose crime tools to agent |
| **Transport** | Streamable HTTP | MCP communication |

---

## 📡 API Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /analyze-route` | POST | Analyze routes between two addresses |

### Request
```json
{
  "start": "123 Main St, Chicago, IL",
  "destination": "456 Oak Ave, Chicago, IL"
}
```

### Response
```json
{
  "routes": [
    {
      "route_id": 1,
      "risk_score": 75,
      "risk_summary": "High crime corridor through downtown Chicago...",
      "status": "success"
    },
    {
      "route_id": 2,
      "risk_score": 42,
      "risk_summary": "Lower risk suburban route...",
      "status": "success"
    }
  ]
}
```

---

## 📁 Project Structure

```
src/
├── safe_travels.py              # Main orchestrator
├── safe_travels_api.py          # FastAPI application
├── safe_travels_agent.py        # PydanticAI agent
├── helper_functions/
│   ├── __init__.py
│   └── google_maps.py           # Google Maps API wrapper
├── MCP_Servers/
│   ├── __init__.py
│   └── crime_mcp/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── config.py            # Settings
│       ├── functions.py         # Crime API implementation
│       └── server.py            # FastMCP server
└── tests/
    ├── test_phase1_crime_mcp.py
    ├── test_phase2_google_maps.py
    ├── test_phase3_agent.py
    ├── test_phase4_orchestrator.py
    └── test_phase5_api.py
```

---

## 📅 Implementation Phases

| Phase | Component | Description |
|-------|-----------|-------------|
| **Phase 1** | Crime MCP Server | MCP server with Crimeometer tools |
| **Phase 2** | Google Maps Helper | Route extraction with waypoints |
| **Phase 3** | PydanticAI Agent | Risk scoring agent |
| **Phase 4** | Orchestrator | Parallel route analysis |
| **Phase 5** | FastAPI | Final API endpoint |

---

## ✅ Success Metrics

| Metric | Target |
|--------|--------|
| Query latency | < 5 seconds |
| Risk score accuracy | Consistent 1-100 scale |
| API uptime | 99% |
| Code quality | Clean, readable, testable |
