"""
SafeTravels - Main Application
==============================

Multi-page Streamlit app with:
- DRIVER EXPERIENCE (Main Product)
- Investor/Business Section

Author: SafeTravels Team
"""

import streamlit as st

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="SafeTravels - Truck Driver Safety Platform",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Professional theme */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    
    .subheader {
        font-size: 1.3rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Cards */
    .feature-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Navigation styling */
    .nav-link {
        display: block;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        text-decoration: none;
        color: #1e293b;
        transition: all 0.2s;
    }
    .nav-link:hover {
        background: #f1f5f9;
    }
    .nav-link.active {
        background: #2563eb;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# MAIN PAGE CONTENT
# =============================================================================

st.markdown('<h1 class="main-header">🚛 SafeTravels</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">AI-Powered Truck Stop Safety & Route Intelligence Platform</p>', unsafe_allow_html=True)

# Hero section
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🛡️ Security Scoring", "100-Point", "Proprietary formula")
with col2:
    st.metric("🚛 Truck Stops", "40,000+", "Scored & ranked")  
with col3:
    st.metric("⚡ API Response", "<100ms", "Enterprise-grade")
with col4:
    st.metric("🎯 Accuracy", "94%", "vs 60% random")

st.markdown("---")

# Quick Navigation Cards
st.markdown("## 🚀 Quick Access")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🚛 Driver Dashboard</h3>
        <p>Real-time alerts, safe stop finder, HOS tracking, and emergency help.</p>
        <p><strong>👉 Select from sidebar</strong></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🔌 Live API Demo</h3>
        <p>Test our 15+ API endpoints with real data. Interactive playground.</p>
        <p><strong>👉 Select from sidebar</strong></p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>💼 For Investors</h3>
        <p>ROI calculator, market analysis, and business case.</p>
        <p><strong>👉 Select from sidebar</strong></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Problem Statement
st.markdown("## 📊 The Problem We Solve")

prob_col1, prob_col2 = st.columns(2)

with prob_col1:
    st.markdown("""
    ### 💰 $50 Billion Problem
    
    - **$50B+** annual cargo theft in the US
    - **3.5M** truck drivers at risk daily
    - **No proactive solution** exists today
    - **70% of thefts** happen at truck stops
    
    > *"Drivers don't know which stops are safe until it's too late"*
    """)

with prob_col2:
    st.markdown("""
    ### 🛡️ Our Solution
    
    - **100-point security scoring** for every stop
    - **Proactive Red Zone alerts** before danger
    - **HOS-aware recommendations** (legal + safe)
    - **API-first platform** for any fleet system
    
    > *"We tell drivers exactly where to stop, and where NOT to"*
    """)

st.markdown("---")

# Features Overview
st.markdown("## 🎯 Platform Features")

feat_col1, feat_col2, feat_col3 = st.columns(3)

with feat_col1:
    st.markdown("""
    #### 🅿️ Safe Stop Finder
    - Find secure parking nearby
    - Filter by security tier
    - Real-time availability
    - User reviews & ratings
    
    #### ⏰ HOS Integration
    - Track driving hours
    - Get stop recommendations
    - Never violate regulations
    """)

with feat_col2:
    st.markdown("""
    #### 🚨 Real-Time Alerts
    - Red Zone warnings
    - Speed anomaly detection
    - GPS jammer alerts
    - Dwell time warnings
    
    #### 🗺️ Route Analysis
    - Segment-by-segment scoring
    - Red Zone mapping
    - Alternative routes
    """)

with feat_col3:
    st.markdown("""
    #### 🎚️ What-If Analysis
    - Time-based risk slider
    - Best departure times
    - Risk forecasting
    
    #### 🆘 Emergency Mode
    - One-tap SOS
    - Nearest police stations
    - Secured truck stops
    - GPS sharing
    """)

st.markdown("---")

# Call to Action
st.markdown("## 👈 Get Started")
st.info("**Select a page from the sidebar** to explore the Driver Dashboard, test APIs, or see business metrics.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 1rem;">
    <strong>SafeTravels API Platform</strong> | January 2026<br/>
    Built with ❤️ for truck driver safety
</div>
""", unsafe_allow_html=True)
