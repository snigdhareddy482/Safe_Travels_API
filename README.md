# SafeTravels API

**AI-Powered Route Safety Analysis**

Analyze routes between two addresses and get AI-generated crime risk scores (1-100) with explanatory summaries for each route option.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the Crime MCP Server
python -m src.MCP_Servers.crime_mcp

# Run the API
uvicorn src.safe_travels_api:app --reload

# Open docs at http://localhost:8000/docs
```

## 🏗️ Architecture

```
User Request → FastAPI → Orchestrator → PydanticAI Agent + Crime MCP → Response
```

| Component | Technology |
|-----------|------------|
| **API** | FastAPI |
| **Route Data** | Google Maps Directions API |
| **Crime Data** | Crimeometer via MCP Server |
| **AI Agent** | PydanticAI |
| **MCP Transport** | Streamable HTTP |

## 📡 API Usage

### POST /analyze-route

**Request:**
```json
{
  "start": "123 Main St, Chicago, IL",
  "destination": "456 Oak Ave, Chicago, IL"
}
```

**Response:**
```json
{
  "routes": [
    {
      "route_id": 1,
      "risk_score": 75,
      "risk_summary": "High crime corridor through downtown...",
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

## 📁 Project Structure

```
src/
├── safe_travels.py              # Main orchestrator
├── safe_travels_api.py          # FastAPI application
├── safe_travels_agent.py        # PydanticAI agent
├── helper_functions/
│   └── google_maps.py           # Google Maps wrapper
├── MCP_Servers/
│   └── crime_mcp/               # Crime MCP Server
│       ├── config.py
│       ├── functions.py
│       └── server.py
└── tests/                       # Phase tests
```

## 🔑 Environment Variables

Create a `.env` file:

```env
GOOGLE_MAPS_API_KEY=AIzaSy...
CRIME_API_KEY=your_crimeometer_key
OPENAI_API_KEY=sk-...
```

## 📊 Implementation Status

- [ ] Phase 1: Crime MCP Server
- [ ] Phase 2: Google Maps Helper
- [ ] Phase 3: PydanticAI Agent
- [ ] Phase 4: Orchestrator
- [ ] Phase 5: FastAPI Endpoint

See `docs/refactor_plan.md` for detailed implementation guide.
