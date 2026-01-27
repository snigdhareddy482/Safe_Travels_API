# SafeTravels API - AI Assistant Rules

## Project Overview
SafeTravels is a **Route Safety API** that analyzes routes between two addresses and provides AI-generated crime risk scores (1-100) with explanatory summaries for each route option.

## Core Architecture

```
User Request → FastAPI → Orchestrator → PydanticAI Agent + Crime MCP Server → Response
```

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Route Data | Google Maps Directions API |
| Crime Data | Crimeometer via MCP Server |
| AI Agent | PydanticAI |
| Transport | Streamable HTTP (MCP) |

## Core Development Philosophy

### 1. KISS (Keep It Simple, Stupid)
- **No excess code** - Clean, readable, elegant
- **Research first** - Understand before implementing
- **Test to verify** - Each phase has tests that must pass

### 2. Collaborative Principles
- **COLLABORATE**: Work with the user, don't go rogue
- **ASK FIRST**: If unclear about requirements, ask
- **NO ASSUMPTIONS**: Verify before implementing
- **SMALL STEPS**: Minimal, focused changes

### 3. Quality Standards
- **Follow Patterns**: Match existing code style
- **Type Safety**: Use Pydantic models, type hints
- **Document Intent**: Clear docstrings for non-obvious logic

### 4. Important Constraints
- **No Random Docs**: Don't create .md files unless requested
- **Prefer Editing**: Edit existing files over creating new ones
- **Respect Scope**: Only change what's explicitly requested

## File Structure
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

## Key Decisions
| Decision | Choice | Why |
|----------|--------|-----|
| Route Data | Google Maps API | Multiple route alternatives |
| Crime Data | Crimeometer | Real-time, good coverage |
| AI Agent | PydanticAI | Type-safe, structured output |
| MCP Transport | Streamable HTTP | Standard, reliable |
| API | FastAPI | Fast, async, auto-docs |
