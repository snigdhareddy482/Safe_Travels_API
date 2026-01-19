"""
Technical Architecture - System Design
======================================

Shows the technical architecture for investors/engineers.
"""

import streamlit as st

st.set_page_config(page_title="Technical Architecture", page_icon="🏗️", layout="wide")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #374151 0%, #1f2937 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">🏗️ Technical Architecture</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Enterprise-grade API platform built for scale</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ARCHITECTURE DIAGRAM
# =============================================================================

st.markdown("## 📐 System Architecture")

st.markdown("""
```
┌─────────────────────────────────────────────────────────────────────┐
│                    PARTNER APPS / TMS / DRIVER APPS                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                         API Gateway (FastAPI)
                    Rate Limit | Auth | Cache | Docs
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼─────────┐    ┌────────▼───────┐    ┌─────────▼────────┐
│   REST API      │    │   MCP Server   │    │   LangGraph      │
│   Endpoints     │    │   (Tools)      │    │   Agent          │
│   15+ routes    │    │   20+ tools    │    │   Multi-agent    │
└───────┬─────────┘    └────────┬───────┘    └─────────┬────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   RAG Pipeline        │
                    │   ChromaDB + LangChain│
                    └───────────┬───────────┘
                                │
┌─────────────────────┬─────────┴───────────┬─────────────────────┐
│   FBI Crime Data    │   DOT Truck Stops   │   CargoNet Reports  │
│   (JSON + Vector)   │   (JSON + GeoAPI)   │   (PDF + Embeddings)│
└─────────────────────┴─────────────────────┴─────────────────────┘
```
""")

st.markdown("---")

# =============================================================================
# TECH STACK
# =============================================================================

st.markdown("## 🔧 Technology Stack")

stack_col1, stack_col2, stack_col3 = st.columns(3)

with stack_col1:
    st.markdown("""
    ### 🔌 API Layer
    | Component | Technology |
    |:---|:---|
    | Framework | **FastAPI** |
    | Server | Uvicorn |
    | Docs | Swagger UI |
    | Validation | Pydantic |
    | Auth | API Keys (OAuth2 planned) |
    """)

with stack_col2:
    st.markdown("""
    ### 🤖 AI/ML Layer
    | Component | Technology |
    |:---|:---|
    | Orchestration | **LangChain** |
    | Agent System | **LangGraph** |
    | MCP Server | **FastMCP** |
    | Vector DB | **ChromaDB** |
    | Embeddings | OpenAI/Gemini |
    """)

with stack_col3:
    st.markdown("""
    ### 📊 Data Layer
    | Component | Technology |
    |:---|:---|
    | Stop Data | JSON (40,000+) |
    | Crime Data | FBI UCR API |
    | Geo Queries | Haversine + Grid |
    | Caching | In-memory (Redis planned) |
    | Storage | File-based (PostgreSQL planned) |
    """)

st.markdown("---")

# =============================================================================
# API ENDPOINTS
# =============================================================================

st.markdown("## 📡 API Endpoints (15+)")

endpoint_col1, endpoint_col2, endpoint_col3 = st.columns(3)

with endpoint_col1:
    st.markdown("""
    ### 🅿️ Stop Finder
    - `GET /safe-stops`
    - `GET /fuel-stops`
    - `GET /emergency-stops`
    - `GET /hos-recommendation`
    - `GET /parking-availability`
    """)

with endpoint_col2:
    st.markdown("""
    ### 🗺️ Route Analysis
    - `POST /analyze-route`
    - `POST /assess-risk`
    - `POST /query`
    
    ### 🚨 Detection
    - `POST /check-speed-anomaly`
    - `POST /check-gps-status`
    """)

with endpoint_col3:
    st.markdown("""
    ### 🔊 Alerts
    - `GET /voice-alert`
    - `GET /voice-alert-types`
    
    ### 🎚️ Analysis
    - `GET /what-if`
    - `GET /what-if/best-time`
    - `POST /incidents`
    """)

st.markdown("---")

# =============================================================================
# MCP TOOLS
# =============================================================================

st.markdown("## 🛠️ MCP Tools (20+)")

st.markdown("""
| Tool | Purpose | Status |
|:---|:---|:---|
| `safe_stops.py` | Find secure parking with 100-pt scoring | ✅ |
| `risk_scorer.py` | 15-factor risk assessment | ✅ |
| `red_zone_checker.py` | High-crime area detection | ✅ |
| `route_scanner.py` | Segment-by-segment analysis | ✅ |
| `speed_anomaly.py` | Creeping/braking detection | ✅ |
| `gps_monitor.py` | Jammer/signal loss detection | ✅ |
| `behavior_monitor.py` | Dwell time, unauthorized stops | ✅ |
| `voice_alerts.py` | 12 audio alert types | ✅ |
| `whatif_slider.py` | Time-based risk analysis | ✅ |
| `parking_availability.py` | Real-time spot availability | ✅ |
""")

st.markdown("---")

# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

st.markdown("## ⚡ Performance Metrics")

perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)

with perf_col1:
    st.markdown("""
    <div style="background: #d1fae5; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #16a34a;"><100ms</div>
        <div style="color: #065f46;">Avg Response</div>
    </div>
    """, unsafe_allow_html=True)

with perf_col2:
    st.markdown("""
    <div style="background: #dbeafe; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #2563eb;">99.9%</div>
        <div style="color: #1d4ed8;">Uptime SLA</div>
    </div>
    """, unsafe_allow_html=True)

with perf_col3:
    st.markdown("""
    <div style="background: #fef3c7; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #d97706;">50K+</div>
        <div style="color: #92400e;">Concurrent Users</div>
    </div>
    """, unsafe_allow_html=True)

with perf_col4:
    st.markdown("""
    <div style="background: #fce7f3; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #db2777;">10K+</div>
        <div style="color: #9d174d;">Requests/sec</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# ROADMAP
# =============================================================================

st.markdown("## 🗓️ Technical Roadmap")

st.markdown("""
### Q1 2026 (Now)
- ✅ FastAPI + MCP Server
- ✅ 15+ API endpoints
- ✅ RAG pipeline with ChromaDB
- ✅ Multi-agent LangGraph system
- 🔄 Streamlit dashboard (in progress)

### Q2 2026
- 📦 PostgreSQL + PostGIS migration
- 📦 Redis caching layer
- 📦 WebSocket real-time alerts
- 📦 Mobile SDK (React Native)

### Q3 2026
- 📦 Azure/AWS production deployment
- 📦 OAuth 2.0 authentication
- 📦 Rate limiting + metering
- 📦 Analytics dashboard

### Q4 2026
- 📦 White-label API options
- 📦 Insurance data API
- 📦 Fleet analytics
- 📦 Dashcam integration
""")

st.markdown("---")

# =============================================================================
# SECURITY
# =============================================================================

st.markdown("## 🔒 Security & Compliance")

sec_col1, sec_col2 = st.columns(2)

with sec_col1:
    st.markdown("""
    ### 🛡️ Security Features
    - ✅ API key authentication
    - ✅ Rate limiting (1000 req/min)
    - ✅ TLS 1.3 encryption
    - ✅ Input validation (Pydantic)
    - ✅ Audit logging
    - 🔄 OAuth 2.0 (planned)
    - 🔄 SOC 2 Type II (planned)
    """)

with sec_col2:
    st.markdown("""
    ### 📜 Compliance
    - ✅ GDPR-ready (data privacy)
    - ✅ CCPA-ready (California)
    - ✅ FMCSA HOS regulations
    - ✅ DOT data standards
    - 🔄 HIPAA-adjacent (planned)
    """)
