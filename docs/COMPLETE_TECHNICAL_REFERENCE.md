# SafeTravels: Complete Technical Reference

> **The "Bible" of SafeTravels**  
> This document serves as the single source of truth for the entire SafeTravels project. It details every component, algorithm, agent persona, and configuration parameter in minute detail.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Autonomous Agents (The Swarm)](#3-autonomous-agents-the-swarm)
4. [RAG Pipeline Deep Dive](#4-rag-pipeline-deep-dive)
5. [Risk Model Algorithms](#5-risk-model-algorithms-minute-details)
6. [Safe Stop Security Logic](#6-safe-stop-security-logic)
7. [MCP Server & Tools](#7-mcp-server--tools)
8. [Data Ecosystem](#8-data-ecosystem)

---

## 1. Project Overview

**SafeTravels** is an AI-powered API designed to prevent cargo theft—a $68B annual problem in the logistics industry. Unlike static databases or simple crime maps, SafeTravels uses **Retrieval-Augmented Generation (RAG)** and **Autonomous Agents** to provide dynamic, context-aware risk intelligence.

### Core Mission
To move beyond "dots on a map" by providing:
- **Predictive Risk Scoring:** Using a 15-factor model.
- **Explainable AI:** "Why is this risky?" (e.g., "High theft rate for electronics at night").
- **Agentic Workflows:** Autonomous planning, analysis, and critique of routes.

---

## 2. System Architecture

The system is built on a modular microservices architecture, orchestrated by LangGraph and exposed via FastMCP.

```mermaid
graph TD
    User[User / Client] -->|MCP Protocol| MCPServer
    MCPServer -->|Orchestrate| AgentGraph[LangGraph Agents]
    
    subgraph "The Swarm (Agents)"
        Planner -->|Options| Analyst
        Analyst -->|Draft| Critic
        Critic -->|Feedback| Analyst
    end
    
    subgraph "Core Engines"
        RiskEngine[Risk Scorer (15-Factor)]
        RouteScanner[Route Scanner]
        SafeStop[Safe Stop Finder]
    end
    
    subgraph "RAG Pipeline"
        ChromaDB[(ChromaDB Vector Store)]
        Embed[Embedding Model]
        LLM[GPT-4o / Groq]
    end
    
    AgentGraph --> RiskEngine
    AgentGraph --> RAG Pipeline
    MCPServer --> SafeStop
```

### Technology Stack
- **Orchestration:** LangGraph (Stateful multi-agent workflows)
- **Interface:** Model Context Protocol (MCP) by Anthropic
- **Vector Database:** ChromaDB (Local persistence)
- **LLM:** OpenAI GPT-4o-mini / Groq Llama 3
- **Language:** Python 3.10+

---

## 3. Autonomous Agents (The Swarm)

SafeTravels employs a "human-in-the-loop" style workflow simulated by three specialized agents.

### 3.1 The Planner
*Role: Logistics Coordinator*
- **Responsibility:** Generates multiple route options and calculates raw metrics.
- **Minute Details:**
    - **Logic:**
        - Generates **3 distinct routes**: Direct (I-35), Northern (I-40), Southern (I-20).
    - **Scoring Weights:**
        - **Safety (Risk):** 60% (Most critical factor).
        - **Time:** 25% (Efficiency matters).
        - **Distance:** 15% (Impacts fuel/cost).
    - **Hotspot Logic:**
        - **Bounding Boxes:** Checks overlapping coordinates against known hotspots (I-10, Chicago South Side).
        - **Penalty:** Applies a **1.5x risk multiplier** if a route intersects a hotspot.
    - **Output:** List of `RouteOption` objects ranking from safest to riskiest.

### 3.2 The Analyst
*Role: Risk Intelligence Specialist*
- **Responsibility:** Deep-dives into the Planner's options to find the "why".
- **Minute Details:**
    - **Selection:** Picks the route with the lowest weighted risk score.
    - **Confidence Calculation:**
        - **Base:** 0.70 (70%)
        - **Source Boost:** +5% per cited document.
        - **Claim Boost:** +2% per verifiable claim.
        - **Red Zone Penalty:** -10% per Red Zone.
        - *Clamped: 50% - 95%.*
    - **Recommendation System:**
        - **Risk ≥ 7:** Triggers "Plan daylight transit only" & "Additional security required".
        - **Red Zone > 0:** Triggers "Do NOT stop in Red Zones".
        - **High Value:** Triggers "Secured stops only (Tier 1)".

### 3.3 The Critic
*Role: Senior Auditor*
- **Responsibility:** Validates the Analyst's work before it reaches the user.
- **Minute Details:**
    - **Revision Loop:** Allows up to **3 revisions**. If it fails a 4th time, it force-approves with a "Best Effort" flag.
    - **Validation Checks:**
        - **Citation Check:** Rejects if sources are "Unknown" or "N/A" (needs >2 claims).
        - **Logic Check:** Verifies the math and ensuring the safest route is actually chosen.
    - **Internal Scoring (Critic's Confidence):**
        - **Base:** 0.80
        - **Penalties:** -15% if Citation ID fails, -15% if Logic fails.
        - *Used to determine if human intervention is needed.*

### 3.4 The Memory Agent (System Service)
*Role: Personalization Engine*
- **Responsibility:** Manages driver history and learns from feedback without being a direct node in the planning graph.
- **Minute Details:**
    - **Trip Recording:** Persists every trip's details (Origin, Dest, Cargo, RouteID).
    - **Feedback Loop:** Records driver ratings for stops (1-5 stars).
        - **Unsafe Flag:** Stops rated **1 or 2 stars** are marked as "unsafe" for that specific driver.
    - **Personalization:**
        - **Exclusion:** Automatically filters out "unsafe" stops from future recommendations.
        - **Preference Matching:** Prioritizes stop types (e.g., "Love's" vs "Pilot") based on stored preferences.
    - **Storage:** JSON-based persistence in `./trip_memory/{driver_id}_memory.json`.
### 3.5 The Shared Brain (`state.py`)
*Role: State Management Infrastructure*
- **Responsibility:** Defines the schema for data passing between agents.
- **Minute Details:**
    - **Schema:** Uses a `TypedDict` named `AgentState` to enforce type safety.
    - **Keys:**
        - `trip_request`: Raw user input.
        - `reasoning_chain`: A chronological list of timestamped "thoughts".
        - `revision_count`: Integer tracker to prevent infinite critic loops.
    - **Immutability:** Designed for functional updates (agents receive state → return new state).

### 3.6 The Orchestrator (`multi_agent_graph.py`)
*Role: Workflow Conductor*
- **Responsibility:** Manages the Planner → Analyst → Critic loop using LangGraph.
- **Minute Details:**
    - **Conditional Routing (`_route_after_critic`):**
        - If Critic says "approved" → Move to `finalize`.
        - If Critic says "needs_revision" → Loop back to `analyst`.
    - **Hard Stop:** Enforces a **Max Revision Limit of 3**. If the loop hits 3, it forces an "approved" verdict to prevent infinite cycles.
    - **Final Confidence:** Calculates the geometric mean of the Analyst's confidence and the Critic's confidence.

### 3.7 The RAG Researcher (`graph.py`)
*Role: Question Answering Sub-System*
- **Responsibility:** A specialized, separate graph for answering general questions (e.g., "Is stops in Dallas safe?") without running the full route planner.
- **Minute Details:**
    - **Self-Correction Loop:**
        1.  **Retrieve:** Fetches docs from ChromaDB.
        2.  **Grade:** Checks if docs are relevant.
        3.  **Decide:**
            -   If relevant → Generate Answer.
            -   If irrelevant → **Transform Query**.
### 3.8 Utility Scripts
The final 2 files serve operational purposes:

**9. `safetravels/testing/agent_demo.py` (CLI Demo)**
- **Role:** Standalone demonstration script.
- **Minute Details:**
    - Imports `build_graph` from `safetravels.agents.graph`.
    - Runs a hardcoded query: *"Is Dallas a high risk area for electronics?"*.
    - Uses `agent.stream()` to print node execution steps (`➜ Node Completed: retrieve`, etc.) to the console.
    - *Moved from `agents/example.py` to `testing/` to keep source clean.*

**10. `safetravels/agents/__init__.py` (Package Marker)**
- **Role:** Python Module Definition.
- **Minute Details:**
    - Currently **empty** (0 bytes).
    - Its presence tells Python that the `agents/` folder is a package, allowing imports like `from safetravels.agents import planner`.
    - *Required for the application to function.*

### 3.9 Swarm Workflow & Efficiency
How do these 7 components (4 Personas + 3 Infrastructure) actually work together to solve the problem and save resources?

#### A. The "Linear-Cyclic" Architecture
The system follows a specific flow orchestrated by `multi_agent_graph.py`:

1.  **Input:** User sends a request (e.g., "Safe route Dallas to Chicago").
2.  **Planner (Fast Computation):**
    -   *Action:* Instantly generates 3 mathematical routes using `planner.py`.
    -   *Resource Saving:* Uses **geometric math** (bounding boxes) instead of expensive LLM calls for the initial filtering. It filters out thousands of bad routes in milliseconds.
3.  **Analyst (Deep Thinking):**
    -   *Action:* Takes the mathematical output and applies "reasoning". It selects the single best route.
    -   *Action:* Calls the `RAG Researcher` (`graph.py`) only if it needs external context (e.g., "Is there a riot in St. Louis?").
    -   *Resource Saving:* Only invokes the expensive RAG loop when necessary, not for every mile of the trip.
4.  **Critic (Quality Control):**
    -   *Action:* mathematically verifies the Analyst's work (e.g., "Did you actually pick the route with the lowest score?").
    -   *Loop:* If it finds a mistake, it sends it back.
    -   *Resource Saving:* Prevents **Hallucinations**. Instead of sending a bad route to the user (which costs time and money to fix later), it catches the error in-memory.

#### B. How They Solve The Problem (Efficiency)
| Metric | Without Swarm | With SafeTravels Swarm |
|---|---|---|
| **Time to Plan** | Human Dispatcher: **45-60 mins** (checking multiple apps, news sites) | Swarm: **15-30 seconds** (Automated parallel processing) |
| **Compute Cost** | High (LLM generating entire coordinates) | **Low** (Planner uses Python math for coords, LLM only for reasoning) |
| **Accuracy** | Variable (Human fatigue/bias) | **High** (Critic enforces 15-factor checklist every time) |
| **Memory** | None (Dispatcher forgets driver prefs) | **Perfect** (Memory Agent persists "Unsafe" flags forever) |

#### C. "Life of a Request" (Concrete Visualization)
Instead of abstract boxes, here is exactly what happens when a User asks: *"Plan a safe route from Dallas to Chicago for Electronics."*

**1. THE HANDOFF (User → Memory → Planner)**
> **User:** "I need to move $500k of TVs to Chicago."
> **Memory:** "Recognized Driver #42. Injecting preference: *Avoids unlit rest areas*."
> **Planner:** "Received. Calculating geometry..."

**2. THE MATH PHASE (Planner)**
> **Planner:** *Runs geometric bounding box checks.*
> - Option A (Direct via I-35): **REJECTED** (Hits 'Chicago South Side' Hotspot).
> - Option B (East via I-57): **PASS**.
> - Option C (West via I-55): **PASS**.
> **Output:** "Option C is mathematically safest (Risk 4.2)."

**3. THE REASONING PHASE (Analyst)**
> **Analyst:** "Math says Option C, but why?"
> *Invokes RAG Researcher...*
> **RAG:** "Retrieved 3 recent reports: 'I-55 St. Louis bypass has high cargo theft alerts this week'."
> **Analyst:** "Aha! Adjusting score. Option C is actually risky now. Switching to Option B."
> **Draft:** "Recommend Option B. Avoid St. Louis due to active alerts."

**4. THE AUDIT PHASE (Critic)**
> **Critic:** "Reviewing Analyst's draft..."
> - *Check 1:* Are citations real? **YES** (Source: FBI UCR 2024).
> - *Check 2:* Is logic sound? **YES** (Option B avoids the St. Louis alert).
> **Verdict:** "APPROVED."

**5. FINAL OUTPUT (To Dashboard)**
> **System:** Displays Map with Option B highlighted. "Recommended: Northern Bypass (Avoids St. Louis theft ring)."

---

## 4. RAG Pipeline Deep Dive

### 4.1 Ingestion (`vector_store.py`)
- **Store:** ChromaDB (local persistence).
- **Collections:**
    - `crime_data`: FBI/Police statistics.
    - `theft_reports`: News and incident reports.
    - `truck_stops`: Facility amenities and reviews.
- **Similarity:** Cosine Similarity.

### 4.2 Retrieval & Generation (`chain.py`)
- **Top-K:** Retrieves top 5 most relevant documents per query.
- **Temperature:** Set to **0.1** (very low) to ensure factual, consistent scoring.
- **Scoring Rubric (1-10):**
    - **1-2 (Low):** No recent incidents, Low crime rate.
    - **3-4 (Mod-Low):** 0-1 incidents, Average crime.
    - **5-6 (Moderate):** 1-2 incidents, Above average crime.
    - **7-8 (High):** 3-5 incidents, High crime.
    - **9-10 (Critical):** 6+ incidents, Active theft ring.

---

## 5. Risk Model Algorithms (Minute Details)

The heart of SafeTravels is the deterministic **15-Factor Risk Model** defined in `config.py`.

### 5.1 The Formula
$$ \text{Risk} = \text{Base} \times \prod (\text{Weights}) $$
*Result is clamped between 1.0 and 10.0.*

### 5.2 Factor Weights (Exact Values)

#### A. Temporal Factors (Time is critical)
| Factor | Value | Weight |
|--------|-------|--------|
| **Time of Day** | **Night (10pm-5am)** | **1.50x** |
| | Evening (5pm-10pm) | 1.25x |
| | Day (5am-5pm) | 1.00x |
| **Day of Week** | **Saturday** | **1.20x** |
| | Friday | 1.15x |
| | Sunday | 1.10x |
| | Mon-Wed | 1.00x |
| **Season** | **Black Friday Week** | **1.50x** |
| | Holiday Peak (Dec) | 1.40x |

#### B. Cargo Targets (What's inside matters)
| Feature | Value | Weight |
|---------|-------|--------|
| **Commodity** | **Electronics** | **1.50x** |
| | Pharmaceuticals | 1.45x |
| | Alcohol/Tobacco | 1.30x |
| | Auto Parts | 1.25x |
| | Food/Beverage | 1.00x |
| **Value** | **$1M+** | **1.60x** |
| | $500k-$1M | 1.40x |

#### C. Location & Environment
| Feature | Value | Weight |
|---------|-------|--------|
| **Location** | **Roadside/Unsecured** | **1.60x** |
| | Rest Area | 1.30x |
| | **Secured Truck Stop** | **0.80x** |
| **Weather** | **Severe Storm** | **1.35x** |
| | Fog/Ice | 1.20x |
| **Events** | **Civil Unrest / Riot** | **2.00x** |
| | Major Protest | 1.60x |
| **Traffic** | **Standstill** | **1.50x** |

### 5.3 Route Zone Logic (`route_scanner.py`)
- **Segment Size:** Every **20 miles**.
- **Red Zone:** Any segment with **Risk Score ≥ 7.0**.
- **Yellow Zone:** Any segment with **Risk Score ≥ 5.0**.
- **Route Multipliers:**
    - **> 1500 miles:** **1.4x** (Exposure penalty)
    - **1000-1500 miles:** **1.25x**

---

## 6. Safe Stop Security Logic

Safety is quantified on a **0-100 point scale** in `safe_stops.py`.

### 6.1 Scoring Breakdown

**Tier 1: Physical Security (+45 max)**
- **Gated Parking:** +18 pts (Most critical)
- **24/7 Guards:** +15 pts
- **CCTV:** +8 pts
- **Well Lit:** +4 pts

**Tier 2: Location History (+35 max)**
- **No Recent Thefts:** +18 pts
- **Low Risk State:** +8 pts
- **Highway Access:** +6 pts

**Tier 3: Operational (+20 max)**
- **Major Brand:** +8 pts (Pilot, Love's, etc.)
- **Staffed 24/7:** +7 pts

**Penalties (Deductions)**
- **Poor Lighting:** -6 pts
- **Isolated Area:** -5 pts
- **High Crime State:** -5 pts

### 6.2 Security Tiers
- **Tier 1 (Premium):** 85-100 points
- **Tier 2 (Secure):** 65-84 points
- **Tier 3 (Basic):** 45-64 points
- **Avoid:** < 45 points

---

## 7. MCP Server & Tools

The Model Context Protocol (MCP) server exposes **8 specialized tools** for AI agents.

### Tool Reference

#### 1. `assess_location_risk`
*Calculates granular risk score (1-10) using the 15-factor model.*
- **Arguments:**
    - `latitude` (float): GPS Latitude.
    - `longitude` (float): GPS Longitude.
    - `commodity` (str): Cargo type (e.g., "electronics").
    - `cargo_value` (float): Declared value in USD.
    - `time_of_day` (str): "day", "evening", "night".
    - `day_of_week` (str): "monday", "friday", etc.
    - `month` (str): "january", "december", etc.
    - `season` (str): "normal", "holiday_peak".
    - `location_type` (str): "truck_stop_secured", "rest_area", etc.
    - `state` (str): Two-letter code (e.g., "TX").
    - `weather` (str): "clear", "storm", "fog".
    - `event` (str): "none", "civil_unrest", "protest".
    - `traffic` (str): "free_flow", "standstill".
    - `accident_history` (str): "low", "high".
- **Returns:** JSON with score, risk level, factor breakdown, and warnings.

#### 2. `quick_risk_check`
*Fast risk check that auto-detects current time factors.*
- **Arguments:**
    - `latitude` (float)
    - `longitude` (float)
    - `commodity` (str, default "general")
    - `cargo_value` (float, default 50000)
- **Returns:** Simplified risk score and top 3 warnings.

#### 3. `find_safe_stops_nearby`
*Locates secure parking ranked by security tier.*
- **Arguments:**
    - `latitude` (float)
    - `longitude` (float)
    - `radius_miles` (int, default 50)
    - `min_security_tier` (str): "level_1" (Premium), "level_2", "level_3".
    - `require_fuel` (bool): Filter for fuel availability.
    - `limit` (int): Max results.
- **Returns:** List of stops with Security Score (0-100) and Tier.

#### 4. `find_fuel_stops_nearby`
*Finds diesel locations prioritized by safety.*
- **Arguments:**
    - `latitude` (float)
    - `longitude` (float)
    - `radius_miles` (int)
- **Returns:** List of fuel stops sorted by distance.

#### 5. `find_emergency_stops`
*Locates immediate help (Police stations + Secured stops).*
- **Arguments:**
    - `latitude` (float)
    - `longitude` (float)
- **Returns:** List of highest-security options within 100 miles.

#### 6. `get_hos_stop_recommendation`
*Recommends stops based on Hours of Service (HOS) limits.*
- **Arguments:**
    - `latitude` (float)
    - `longitude` (float)
    - `hours_driven` (float): Current shift driving hours (max 11).
    - `break_type` (str): "quick" (30min) or "overnight" (10hr).
- **Safety Guarantee:** Never recommends unsafe locations for overnight breaks.

#### 7. `analyze_route`
*Full multi-agent workflow to scan an entire trip.*
- **Arguments:**
    - `origin_lat`, `origin_lon`
    - `destination_lat`, `destination_lon`
    - `commodity` (str)
    - `cargo_value` (float)
    - `time_of_day`, `month`
- **Output:** Complete analysis with Red Zones, Yellow Zones, and Recommendations.

#### 8. `check_recent_incidents`
*Queries driver reports and theft intelligence in the area.*
- **Arguments:**
    - `latitude`, `longitude`
    - `radius_miles` (int)
    - `hours_ago` (int, default 24)
- **Returns:** List of recent "theft", "suspicious_activity", or "police_activity" events.

---

## 8. Data Ecosystem

Data is the fuel for RAG and Risk Models.

### Primary Sources
- **FBI UCR Data:** Uniform Crime Reporting statistics (State/County level).
- **DOT Truck Stop Inventory:** Jason's Law dataset (location, amenities).
- **OpenStreetMap:** Highway exits and POI data.

### 8.2 Static Data Files (The Pantry)
These JSON files in `safetravels/data/` provide the "Static Facts" the app needs.

#### A. The Rules of the Road
1.  **`high_risk_corridors.json`** (The Red Zones)
    - **What:** List of dangerous highway segments (e.g., "I-10 El Paso").
    - **Use:** If a route intersects these coordinates, Risk Score +50%.
2.  **`hos_regulations.json`** (The Law)
    - **What:** Government driving limits (11 hours max).
    - **Use:** Ensures the app recommends *legal* stops.
3.  **`us_holidays.json`** (The Calendar)
    - **What:** Dates like Black Friday or Thanksgiving.
    - **Use:** Adds a risk penalty during peak theft holidays.

#### B. The Maps & Stats
4.  **`dot_truck_stops.json`** & **`osm_truck_stops.json`** (The Map)
    - **What:** 170+ locations with amenity details (Showers, Guards).
    - **Use:** The pool of candidates for "Safe Stop" recommendations.
5.  **`fbi_crime_data.json`** (The Crime Blotter)
    - **What:** Theft stats for 3000+ US counties.
    - **Use:** Calculates the base "Location Risk" (1-10) before AI analysis.
6.  **`cargo_theft_stats.json`** (The Hit List)
    - **What:** Relative risk by cargo type.
    - **Use:** "Electronics (5x risk)" vs "Food (1x risk)". Adjusts score based on manifest.

### Internal Intelligence
- **Hotspot Database:** Hardcoded bounding boxes for high-theft corridors (e.g., I-10).
- **Holiday Calendar:** Dates for "Black Friday" and holiday peaks.
- **HOS Rules:** Hours of Service regulations for stop recommendations.

---
**Document Status:** Final  
**Last Updated:** January 2026  
## 9. API Reference (Minute Details)
The SafeTravels API is built on **FastAPI** and exposes 12 specialized endpoints.

### 9.1 Core Risk Endpoints

#### `POST /assess-risk`
*Calculates static risk for a single point.*
- **Request (`RiskAssessmentRequest`):**
  - `latitude` (float): -90 to 90.
  - `longitude` (float): -180 to 180.
  - `commodity` (str, optional): e.g., "electronics".
  - `time` (datetime, optional): Defaults to now.
- **Response (`RiskAssessmentResponse`):**
  - `risk_score` (1-10): The calculated risk.
  - `risk_level` (str): low/moderate/high/critical.
  - `confidence` (0.0-1.0): Model certainty.
  - `sources`: List of RAG citations.

#### `POST /analyze-route`
*Scans a full path for risk.*
- **Request (`RouteAnalysisRequest`):**
  - `origin` (Coordinates).
  - `destination` (Coordinates).
  - `departure_time` (datetime).
- **Logic:**
  - Calculates risk at Origin, Destination, and Midpoint.
  - Interpolates **20-mile segments**.
  - Flags any segment with Risk >= 7 as "High Risk".
- **Response:** List of `SegmentRisk` objects + `SafeStop` recommendations.

#### `POST /query`
*Natural Language Q&A.*
- **Request:** `{"query": "Is I-40 safe tonight?"}`.
- **Engine:** Triggers the **RAG Graph Agent** (See 3.7).
- **Process:** Retrieve -> Grade -> Generate -> Critic -> Answer.

### 9.2 Safety & Stops Endpoints

#### `GET /safe-stops`
*Finds secure parking.*
- **Parameters:**
  - `radius_miles` (default 50).
  - `min_tier` (default "level_3").
  - `require_fuel` (bool).
- **Scoring:** Retuns stops with 0-100 security score (mapped to Tiers 1-3).

#### `GET /hos-recommendation`
- **Inputs:** `hours_driven` (float), `break_type` ("quick"/"overnight").
- **Constraint:** NEVER recommends < Level 2 security for overnight breaks.

### 9.3 Real-Time Signal Endpoints

| Endpoint | Method | Inputs | Minute Logic |
|---|---|---|---|
| **/check-speed-anomaly** | POST | `speed_mph`, `traffic_level` | Detects "creeping" (5-15mph on highway) = Tailing Suspect. |
| **/check-gps-status** | POST | `last_ping_time` | **Jammer Logic:** >60s gap = Suspected, >120s = Emergency. |
| **/voice-alert** | GET | `alert_type` | Generates TTS audio for "Entering Red Zone". |
| **/incidents** | POST | `event_type`, `desc` | Ingests user report into ChromaDB (`theft_reports` collection). |

### 9.4 Common Data Models
- **Coordinates:** Pydantic model enforcing Lat/Lon limits.
- **StopTier:** Enum (`Level 1`=Premium, `Level 2`=Secure, `Avoid`).

## 10. System Integration & Data Flow (The "Wiring")
This section explains exactly how the components interact with each other and the outside world.

### 10.1 API ↔ Agent Integration
How does a web request actually trigger the Swarm?
1.  **Trigger:** `routes.py` receives `POST /query`.
2.  **Handoff:** It imports `build_graph()` from `safetravels.agents.graph`.
3.  **Execution:** It runs `agent.stream(inputs)` which spins up the LangGraph state machine.
4.  **Wait:** The API holds the connection open while the Planner/Analyst/Critic loop runs (approx 5-15s).
5.  **Return:** The final `AgentState` is converted into a Pydantic `QueryResponse`.

### 10.2 Agent ↔ External Component Map
The Agents don't just talk to each other; they rely on specific subsystems:

| Agent | Component | Interaction Type | Purpose |
|---|---|---|---|
| **Planner** | `config.py` | Import | Reads `HOTSPOT_PENALTY` constant (1.5x) |
| **Planner** | `fbi_crime_data.json` | File Read | Checks coordinate bounding boxes |
| **Analyst** | `vector_store.py` | Function Call | Queries ChromaDB for recent theft reports |
| **Analyst** | `risk_scorer.py` | Function Call | Runs the 15-factor math model |
| **Memory** | `./trip_memory/*.json` | File I/O | Reads/Writes driver preference files |

### 10.3 The Data Pipeline (End-to-End Flow)
How data moves from raw internet sources to the final user alert.

1.  **Ingestion (Offline):**
    - `load_data.py` scrapes FBI/CargoNet reports.
    - `embeddings.py` converts text → Vectors (High-dimensional math).
    - `vector_store.py` saves Vectors → **ChromaDB**.

2.  **Retrieval (Runtime):**
    - User asks: "Is this parking lot safe?"
    - **Analyst** calls `retriever`.
    - `retriever` finds the top 5 most similar vectors in **ChromaDB**.

3.  **Synthesis (The Think):**
    - **Analyst** sends Protocol + Retrieved Docs + User Query to **OpenAI (GPT-4o)**.
    - **LLM** generates the explanation: *"Rated High Risk due to 3 recent thefts within 1 mile."*

### 10.3 The Data Pipeline (End-to-End Flow)
How data moves from raw internet sources to the final user alert.

1.  **Ingestion (Offline):**
    - `load_data.py` scrapes FBI/CargoNet reports.
    - `embeddings.py` converts text → Vectors (High-dimensional math).
    - `vector_store.py` saves Vectors → **ChromaDB**.

2.  **Retrieval (Runtime):**
    - User asks: "Is this parking lot safe?"
    - **Analyst** calls `retriever`.
    - `retriever` finds the top 5 most similar vectors in **ChromaDB**.

3.  **Synthesis (The Think):**
    - **Analyst** sends Protocol + Retrieved Docs + User Query to **OpenAI (GPT-4o)**.
    - **LLM** generates the explanation: *"Rated High Risk due to 3 recent thefts within 1 mile."*

4.  **Delivery (API):**
    - **API Endpoint** returns JSON response to the Dashboard.

## 11. Deep Dive: ChromaDB (The Long-Term Memory)
This section explains the "Why", "What", and "How" of our Vector Database.

### 11.1 WHAT is it?
ChromaDB is an **AI-native embedding database**.
- Unlike SQL (which stores rows/columns), Chroma stores **Vectors** (lists of numbers).
- It lives locally in the `safetravels/chroma_db/` folder (SQLite + Parquet files).

### 11.2 WHY do we need it?
Standard databases fail at "Context".
- **Problem:** If you search SQL for "Robbery", it won't find reports labeled "Hijacking" or "Theft".
- **Solution (Semantic Search):** Chroma understands that "Robbery" and "Hijacking" are mathematically similar concepts.
- **Memory extension:** It allows the Agents to "remember" millions of crime reports, far exceeding the LLM's context window limit.

### 11.3 HOW does it work? (The Math)
It uses a process called **Vector Embedding**.

1.  **Translation:** We use a model called `all-MiniLM-L6-v2`.
    - Text: *"Cargo theft at Pilot Travel Center"*
    - Vector: `[0.041, -0.992, 0.113, ...]` (384 dimensions).
2.  **Storage:** This list of numbers is saved in a highly optimized index (`HNSW`).
3.  ** retrieval:** When a user asks a question, we convert their question into numbers and measure the **Cosine Similarity** (the angle) between the question vector and the document vectors.
    - *Zero Angle* = Exact Match.
    - *Wide Angle* = Unrelated.

### 11.4 Collections Architecture
We organize data into specific "drawers" (Collections) to keep searches fast:

| Collection Name | Content | Update Frequency |
|---|---|---|
| `crime_data` | FBI Uniform Crime Reports (Stats) | Yearly |
| `theft_reports` | CargoNet / User-submitted Incidents | Real-time |

## 12. Configuration & Security Architecture
How we manage secrets, rules, and external connections securely.

### 12.1 The "Restaurant" Strategy
We divide configuration into 3 layers to ensure security and flexibility.

| Layer | File Source | Role | Analogy | Public? |
|---|---|---|---|---|
| **Security Layer** | `.env` | **The Safe** | Holds secrets (API Keys, Passwords) that unlock the app. | 🔒 **PRIVATE** (GitIgnored) |
| **Logic Layer** | `core/app_settings.py` | **The Rulebook** | Defines internal rules (`DEBUG=True`, `Risk=1.5x`). Reads keys from The Safe. | 🌍 **PUBLIC** |
| **Vendor Layer** | `config/external_services.py` | **The Suppliers** | Contact list for external services (Google URL, Azure Endpoint). | 🌍 **PUBLIC** |


### 12.2 Why this separation?
1.  **Safety:** If you accidentally upload code to GitHub, your `.env` (The Safe) stays behind on your laptop. Hackers see the Rulebook, but they can't "open the restaurant" without the keys.
2.  **Modularity:** If Google changes their URL, we update the **Vendor Layer** (`api_config.py`) without risking bugs in the **Logic Layer** (`core/config.py`).

## 13. Application Core (The Engine Room)
This folder `safetravels/core/` contains the code that powers everything else.

### 13.1 `app_settings.py` (The Rulebook)
- **Role:** Central Laws of Physics.

- **What it does:**
    - Defines the **Risk Model Constants** (e.g., Nighttime = 1.5x risk).
    - Sets the **Application State** (Debug Mode, App Name).
    - Loads **Secrets** from the `.env` safe.

### 13.2 `data_loader.py` (The Supply Line)
- **Role:** Raw Material Injection.
- **What it does:**
    - It is the **ONLY** way the application gets external static data.
    - **Loads:**
        - `dot_truck_stops.json` (Parking spots).
        - `fbi_crime_data.json` (Crime stats).
        - `high_risk_corridors.json` (Red Zones).
    - **Process:** Converts silly JSON text into smart Python objects (Classes) that agents can understand.





