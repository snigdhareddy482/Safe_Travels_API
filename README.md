# SafeTravels API

**RAG-Powered Cargo Theft Prevention API & MCP Server**

Real-time risk intelligence using Retrieval-Augmented Generation (RAG) and Autonomous Agents to protect trucking fleets from cargo theft. Now supports the Model Context Protocol (MCP).

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn safetravels.api.main:app --reload

# Run the MCP Server (for Claude Desktop/Cursor)
python -m safetravels.mcp.server

# Open docs at http://localhost:8000/docs
```

## 🏗️ Architecture

```mermaid
graph TD
    User[User / Claude] -->|HTTP or MCP| Gateway
    Gateway --> API[FastAPI]
    Gateway --> MCP[MCP Server]
    
    subgraph "SafeTravels Core"
        API --> Agents
        MCP --> Agents
        
        subgraph "Agent Swarm"
            Planner[Planner Agent] -->|Route Options| Analyst[Analyst Agent]
            Analyst -->|Risk Analysis| Critic[Critic Agent]
            Critic -->|Review/Approve| Analyst
        end
        
        Agents --> RAG[RAG Pipeline]
        RAG --> ChromaDB[(ChromaDB)]
        RAG --> LLM[LLM (Groq/GPT-4o)]
    end
```

| Component | Technology |
|-----------|------------|
| **Agents** | LangGraph (Planner, Analyst, Critic) |
| **Interface** | FastAPI & Model Context Protocol (MCP) |
| **Embeddings** | SBERT / OpenAI |
| **Vector DB** | ChromaDB |
| **LLM** | GPT-4o-mini / Groq |
| **Framework** | LangChain |

## 📡 Key Features

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/assess-risk` | POST | Get risk assessment for location |
| `/api/v1/analyze-route` | POST | Analyze route for theft risks |
| `/api/v1/safe-stops` | GET | Find safe parking nearby |
| `/api/v1/query` | POST | Natural language query |

### MCP Tools
| Tool | Description |
|------|-------------|
| `assess_location_risk` | Comprehensive 15-factor risk scoring |
| `find_safe_stops_nearby` | Locate nearby secure parking using real data |
| `analyze_route` | Full route risk analysis with Red/Yellow zones |
| `get_hos_stop_recommendation` | Find stops matching Hours of Service limits |

## 📁 Project Structure

```
safetravels/
├── agents/              # Autonomous Agents (Planner, Analyst, Critic)
├── api/                 # FastAPI routes and schemas
├── data/                # Data ingestion pipelines
├── mcp/                 # Model Context Protocol server tools
├── rag/                 # RAG Pipeline (ChromaDB, Chains)
├── realtime/            # Real-time event processing
└── frontend/            # Streamlit Dashboard
```

## 🔑 Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
DATABASE_URL=postgresql://...
```

## 📊 Status

- [x] API skeleton
- [x] Pydantic schemas
- [x] ChromaDB setup
- [x] RAG pipeline
- [x] **New:** Multi-Agent System (LangGraph)
- [x] **New:** MCP Server
- [x] **New:** Real-time Risk Analysis
- [ ] Dashboard (In Progress)
