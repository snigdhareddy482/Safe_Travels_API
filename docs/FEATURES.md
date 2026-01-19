# SafeTravels API — Features

> RAG-Powered Cargo Theft Prevention

**Author:** Snigdha

---

## 🎯 Core Features

### 1. Location Risk Assessment

**What it does:**  
Takes any latitude/longitude and returns a comprehensive risk assessment with natural language explanation.

**Example Query:**
```
POST /api/v1/assess-risk
{
  "latitude": 32.7767,
  "longitude": -96.7970,
  "commodity": "electronics"
}
```

**Example Response:**
```json
{
  "risk_level": "high",
  "assessment": "This location in Dallas County has elevated theft risk. The area has seen 5 cargo theft incidents in the past 6 months, primarily targeting electronics. Most incidents occurred between 2-5 AM in unsecured parking areas.",
  "sources": [
    {"title": "FBI Crime Data - Dallas County 2025", "relevance": 0.92},
    {"title": "CargoNet Alert - Texas Electronics Theft", "relevance": 0.87},
    {"title": "FreightWaves Report - I-35 Corridor", "relevance": 0.71}
  ],
  "recommendations": [
    "Park in secured lots with 24/7 security",
    "Avoid stops between 2-5 AM",
    "Consider Pilot Travel Center #4521 (8 miles east) - lower risk"
  ]
}
```

**Key capabilities:**
- Natural language explanation (not just a number)
- Source citations for transparency
- Actionable recommendations
- Commodity-aware risk adjustment

---

### 2. Route Analysis

**What it does:**  
Analyzes an entire route from origin to destination, breaking it into segments and identifying high-risk areas.

**Example Query:**
```
POST /api/v1/analyze-route
{
  "origin": {"latitude": 32.7767, "longitude": -96.7970},
  "destination": {"latitude": 41.8781, "longitude": -87.6298},
  "departure_time": "2026-01-15T22:00:00Z",
  "commodity": "electronics"
}
```

**Example Response:**
```json
{
  "overall_risk": "moderate",
  "total_distance_miles": 920,
  "summary": "This Dallas to Chicago route passes through 3 risk zones. The highest risk is the I-44 corridor near Tulsa (miles 280-350) which has seen increased theft activity. Recommend avoiding stops in this segment.",
  "segments": [
    {
      "segment_id": 1,
      "name": "Dallas to Oklahoma City",
      "risk_level": "low",
      "distance_miles": 200,
      "explanation": "Well-patrolled corridor, low incident history"
    },
    {
      "segment_id": 2,
      "name": "Oklahoma City to Tulsa",
      "risk_level": "high",
      "distance_miles": 100,
      "explanation": "I-44 corridor has seen 8 thefts in past 3 months"
    },
    {
      "segment_id": 3,
      "name": "Tulsa to Springfield",
      "risk_level": "moderate",
      "distance_miles": 180,
      "explanation": "Some truck stop incidents reported"
    }
  ],
  "safe_stops": [
    {
      "name": "Pilot Travel Center - Joplin",
      "location": {"latitude": 37.08, "longitude": -94.51},
      "risk_level": "low",
      "distance_from_start_miles": 380,
      "features": ["24/7 security", "gated parking", "CCTV"]
    }
  ],
  "sources": [
    {"title": "FBI Crime Data - Route Counties", "relevance": 0.88},
    {"title": "CargoNet Alert - I-44 Corridor", "relevance": 0.94}
  ]
}
```

**Key capabilities:**
- Segment-by-segment risk breakdown
- Identifies highest risk portions
- Safe stop recommendations along the route
- Time-of-day awareness

---

### 3. Natural Language Queries

**What it does:**  
Ask any question about cargo theft risk in plain English. The RAG system retrieves relevant documents and synthesizes an answer.

**Example Queries:**
| Question | What You Get |
|----------|--------------|
| "Is this truck stop safe at night?" | Risk assessment + recent incidents + recommendations |
| "What are the most dangerous highways in Texas?" | Ranked list with incident counts + sources |
| "Should I avoid I-10 near Los Angeles?" | Yes/no with explanation + alternative routes |
| "What time is safest to drive through Oklahoma?" | Time window analysis + supporting data |
| "Compare Pilot vs Love's for overnight parking" | Side-by-side comparison with incident data |

**Example Query:**
```
POST /api/v1/query
{
  "query": "What are the top 3 most dangerous truck stops in California?",
  "include_sources": true
}
```

**Example Response:**
```json
{
  "query": "What are the top 3 most dangerous truck stops in California?",
  "answer": "Based on incident reports from the past 12 months, the highest-risk truck stops in California are:\n\n1. **Rest Area I-10 Mile 45** (near Coachella) - 8 thefts reported, primarily targeting electronics\n2. **Truck Stop at I-5/CA-99 Junction** (Bakersfield) - 6 thefts, mixed commodities\n3. **Rest Area I-15 near Barstow** - 5 thefts, targeting pharmaceuticals\n\nAll incidents occurred between midnight and 5 AM. Recommend using secured truck stops instead.",
  "sources": [
    {"title": "CargoNet California Report 2025", "relevance": 0.95},
    {"title": "FBI UCR - California Counties", "relevance": 0.82}
  ],
  "follow_up_questions": [
    "What are safe alternatives near each of these?",
    "What commodities are most targeted in California?"
  ]
}
```

---

### 4. Safe Stop Finder

**What it does:**  
Finds secure parking locations near a given point, ranked by safety level.

**Example Query:**
```
GET /api/v1/safe-stops?latitude=35.5&longitude=-97.5&radius_miles=50
```

**Example Response:**
```json
{
  "location": {"latitude": 35.5, "longitude": -97.5},
  "radius_miles": 50,
  "total_found": 8,
  "stops": [
    {
      "name": "Pilot Travel Center #421",
      "distance_miles": 12.3,
      "risk_level": "low",
      "safety_features": ["24/7 security", "gated parking", "CCTV", "well-lit"],
      "explanation": "No incidents in past 24 months. Security guards on site."
    },
    {
      "name": "Love's Travel Stop",
      "distance_miles": 18.7,
      "risk_level": "low",
      "safety_features": ["CCTV", "well-lit", "truck parking separated"],
      "explanation": "1 minor incident 14 months ago. Generally safe."
    },
    {
      "name": "Independent Truck Stop",
      "distance_miles": 8.1,
      "risk_level": "moderate",
      "safety_features": ["well-lit"],
      "explanation": "2 incidents in past year. No on-site security."
    }
  ]
}
```

---

### 5. Incident Reporting (Feedback Loop)

**What it does:**  
Allows drivers to report thefts or suspicious activity. Reports are ingested into the RAG knowledge base to improve future assessments.

**Example Query:**
```
POST /api/v1/incidents
{
  "latitude": 35.2271,
  "longitude": -97.4395,
  "event_type": "theft",
  "description": "Trailer seal broken, 10 pallets of electronics stolen",
  "commodity": "electronics",
  "estimated_loss": 150000,
  "timestamp": "2026-01-06T03:30:00Z"
}
```

**Why this matters:**
- Data flywheel: More reports → Better predictions
- Real-time updates: New incidents immediately affect risk assessments
- Community-driven: Drivers helping drivers

---

## 🚀 Advanced RAG Features

### 6. Theft Pattern Analysis

**Example Queries:**
| Query | Response |
|-------|----------|
| "What are common theft patterns in Texas?" | Strategic theft (85%), trailer burglary (12%), hijacking (3%) |
| "Are thefts increasing near Dallas?" | Yes, up 23% from last year, mostly electronics |
| "Which commodities are targeted in Q4?" | Electronics, pharmaceuticals, copper (holiday season) |

---

### 7. Commodity-Specific Intelligence

**Example Queries:**
| Query | Response |
|-------|----------|
| "Safest route for $2M pharmaceuticals?" | Lower-risk route with secured stops only |
| "What electronics thefts happened this week?" | List with locations, dates, values |
| "Are food shipments at risk in this area?" | Low risk - food not a high-value target here |

---

### 8. Time-Based Analysis

**Example Queries:**
| Query | Response |
|-------|----------|
| "When is safest to drive through Oklahoma?" | 10 AM - 4 PM weekdays, 70% lower risk |
| "Are weekends safer than weekdays?" | Depends on route - data shows weekday nights highest risk |
| "How does theft change during holidays?" | December: +40% in electronics, -20% in produce |

---

### 9. Comparative Analysis

**Example Query:**
```
POST /api/v1/compare
{
  "type": "routes",
  "items": [
    {"name": "Route A", "path": "I-10 through Phoenix"},
    {"name": "Route B", "path": "I-40 through Albuquerque"}
  ]
}
```

**Example Response:**
```json
{
  "comparison": {
    "Route A (I-10)": {
      "risk_level": "high",
      "incidents_last_year": 34,
      "most_targeted": "electronics"
    },
    "Route B (I-40)": {
      "risk_level": "moderate",
      "incidents_last_year": 12,
      "most_targeted": "general freight"
    }
  },
  "recommendation": "Route B is 65% safer. +45 minutes travel time but significantly lower risk for electronics cargo.",
  "sources": [...]
}
```

---

### 10. Pre-Trip Briefings

**What it does:**  
Generates a comprehensive AI safety briefing before departure.

**Example Response:**
```
🛡️ PRE-TRIP SAFETY BRIEFING
Route: Dallas, TX → Chicago, IL
Departure: Tonight 10:00 PM
Cargo: Electronics ($450,000)

⚠️ TOP 3 WARNINGS:
1. I-44 corridor (Miles 280-350) - HIGH RISK - 8 thefts in past 3 months
2. Night departure increases risk by 40%
3. Electronics are #1 targeted commodity on this route

✅ RECOMMENDED STOPS:
• Mile 380: Pilot Travel Center, Joplin - SECURE
• Mile 600: Love's, Springfield - SECURE

🚫 STOPS TO AVOID:
• Mile 145: Rest Area - 3 recent incidents
• Mile 290: Independent truck stop - no security

📊 OVERALL ASSESSMENT: ELEVATED RISK
Take extra precautions for first 200 miles from pickup.
```

---

### 11. Historical Lookups

**Example Query:**
```
GET /api/v1/history?latitude=33.45&longitude=-112.07&radius_miles=10
```

**Response:**
```json
{
  "location": "Phoenix, AZ area",
  "incidents_found": 15,
  "timeline": [
    {"date": "2026-01-02", "type": "theft", "commodity": "electronics", "value": 280000},
    {"date": "2025-12-18", "type": "theft", "commodity": "copper", "value": 95000},
    {"date": "2025-12-05", "type": "near_miss", "description": "Suspicious vehicle following truck"}
  ],
  "trends": "Incidents increasing - up 30% from previous quarter"
}
```

---

### 12. Insurance Reports

**What it does:**  
Generates formal risk reports for insurance underwriting or compliance.

**Output:**
- PDF download with official risk assessment
- Route-level risk analysis
- Mitigation measures taken
- Source citations for auditing

---

### 13. Conversational Assistant

**What it does:**  
Multi-turn chat interface that remembers context.

**Example Conversation:**
```
User: "Analyze my route from Houston to Atlanta"
AI: [Provides full route analysis]

User: "What about that segment near Jackson?"
AI: [Zooms in on Jackson, MS segment with detailed info]

User: "Are there safer alternatives?"
AI: [Suggests alternative through Memphis with comparison]
```

---

### 14. Alert Subscriptions

**What it does:**  
Set up notifications for routes or areas you care about.

**Types:**
| Alert Type | Trigger |
|------------|---------|
| **Route Alert** | Risk level changes on your saved route |
| **Area Alert** | New incident reported in watched area |
| **Threshold Alert** | Risk exceeds your set level (e.g., > 7/10) |

---

### 15. Multi-Language Support

**What it does:**  
Query and receive responses in multiple languages.

**Example:**
```
Query: "¿Es seguro este estacionamiento para camiones?"
Response: "Este estacionamiento tiene riesgo moderado. Ha habido 2 incidentes en los últimos 6 meses..."
```

---

---

### 16. Model Context Protocol (MCP) Server

**What it does:**  
Exposes SafeTravels tools directly to AI assistants like Claude Desktop, Cursor, or other LLMs. This allows users to use generic AI interfaces to perform specific cargo safety tasks.

**Available Tools:**
- `assess_location_risk`: Comprehensive scoring
- `find_safe_stops_nearby`: Real-time parking search
- `analyze_route`: Complete route scanning
- `check_recent_incidents`: Direct query of incident database

**Example Usage in Claude:**
> "I'm driving a truck with electronics to Dallas. Is it safe to park at the Pilot on I-20?"
> 
> *Claude uses `assess_location_risk` tool behind the scenes and answers using SafeTravels data.*

---

## 📡 API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/assess-risk` | POST | Single location risk assessment |
| `/api/v1/analyze-route` | POST | Full route analysis with segments |
| `/api/v1/query` | POST | Natural language question |
| `/api/v1/safe-stops` | GET | Find safe parking nearby |
| `/api/v1/incidents` | POST | Report theft/incident |
| `/api/v1/compare` | POST | Compare routes or stops |
| `/api/v1/briefing` | POST | Generate pre-trip briefing |
| `/api/v1/history` | GET | Location incident history |
| `/api/v1/report` | POST | Generate insurance report |
| `/api/v1/chat` | POST | Conversational assistant |

---

## 📅 Implementation Roadmap

### Phase 1 (Weeks 1-4) — Core MVP
- [ ] ChromaDB setup and data ingestion
- [ ] Risk assessment endpoint
- [ ] Route analysis endpoint
- [ ] Basic LangChain RAG chain

### Phase 2 (Weeks 5-6) — Enhanced Features
- [ ] Natural language query endpoint
- [ ] Safe stop finder
- [ ] Comparative analysis
- [ ] Streamlit dashboard

### Phase 3 (Weeks 7-8) — Advanced Features
- [ ] Pre-trip briefings
- [ ] Incident reporting
- [ ] Historical lookups
- [ ] Chat interface

### Future Enhancements
- [ ] Alert subscriptions
- [ ] Insurance report generation
- [ ] Multi-language support
- [ ] Voice query support
- [ ] Mobile app integration

---

## 💡 Why RAG Powers All These Features

| Capability | How RAG Enables It |
|------------|-------------------|
| **Any Question** | LLM understands natural language |
| **Source Citations** | Retrieved docs become the sources |
| **Up-to-date Data** | Just add new docs to ChromaDB |
| **Explanations** | LLM synthesizes human-readable answers |
| **Comparisons** | Retrieve docs for both, let LLM compare |
| **Patterns** | Aggregate across many documents |
| **Multi-language** | LLM translates naturally |
| **Chat** | Context window enables follow-ups |
