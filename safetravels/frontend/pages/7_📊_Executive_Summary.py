"""
Executive Summary - Investor Overview
=====================================

Business case, KPIs, and market opportunity.
"""

import streamlit as st

st.set_page_config(page_title="Executive Summary", page_icon="📊", layout="wide")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 1.5rem;">
    <h1 style="margin:0; font-size: 2.5rem;">📊 Executive Summary</h1>
    <p style="margin:0.5rem 0 0 0; font-size: 1.2rem;">SafeTravels API - Investor Presentation</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# KEY METRICS
# =============================================================================

st.markdown("## 🎯 Impact at a Glance")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">$50B+</div>
        <div style="font-size: 1rem; opacity: 0.9;">Annual Cargo Theft</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem;">↑ Growing 15% YoY</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">94%</div>
        <div style="font-size: 1rem; opacity: 0.9;">Our Accuracy</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem;">vs 60% random</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;"><100ms</div>
        <div style="font-size: 1rem; opacity: 0.9;">API Response</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem;">Enterprise-grade</div>
    </div>
    """, unsafe_allow_html=True)

with metric_col4:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%); padding: 1.5rem; border-radius: 15px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">40K+</div>
        <div style="font-size: 1rem; opacity: 0.9;">Truck Stops</div>
        <div style="font-size: 0.85rem; margin-top: 0.5rem;">Scored & ranked</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# PROBLEM / SOLUTION
# =============================================================================

st.markdown("## 💡 The Problem We Solve")

prob_col1, prob_col2 = st.columns(2)

with prob_col1:
    st.markdown("""
    <div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 15px; padding: 1.5rem;">
        <h3 style="color: #b91c1c; margin-top: 0;">🔴 The Problem</h3>
        <ul style="color: #7f1d1d; margin: 0; padding-left: 1.25rem;">
            <li><strong>$50 billion</strong> annual cargo theft in US</li>
            <li><strong>3.5 million</strong> truck drivers at risk daily</li>
            <li><strong>70%</strong> of thefts happen at truck stops</li>
            <li><strong>No solution</strong> provides proactive warnings</li>
            <li><strong>Drivers stop blindly</strong> without safety data</li>
        </ul>
        <div style="margin-top: 1rem; padding: 0.75rem; background: #fecaca; border-radius: 8px; color: #991b1b; font-style: italic;">
            "Drivers don't know which stops are safe until it's too late"
        </div>
    </div>
    """, unsafe_allow_html=True)

with prob_col2:
    st.markdown("""
    <div style="background: #d1fae5; border: 2px solid #10b981; border-radius: 15px; padding: 1.5rem;">
        <h3 style="color: #065f46; margin-top: 0;">🟢 Our Solution</h3>
        <ul style="color: #047857; margin: 0; padding-left: 1.25rem;">
            <li><strong>100-point security scoring</strong> for every stop</li>
            <li><strong>Proactive Red Zone alerts</strong> before danger</li>
            <li><strong>HOS-aware recommendations</strong> (legal + safe)</li>
            <li><strong>API-first platform</strong> for any fleet system</li>
            <li><strong>15-factor risk model</strong> with ML</li>
        </ul>
        <div style="margin-top: 1rem; padding: 0.75rem; background: #a7f3d0; border-radius: 8px; color: #065f46; font-style: italic;">
            "We tell drivers exactly where to stop, and where NOT to"
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# ROI IMPACT
# =============================================================================

st.markdown("## 💰 ROI Per 1,000 Trucks (Annual)")

roi_col1, roi_col2, roi_col3, roi_col4 = st.columns(4)

with roi_col1:
    st.markdown("""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #16a34a;">$2.3M</div>
        <div style="color: #166534;">Theft Prevention</div>
        <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">Avg $2,300/theft × prevented</div>
    </div>
    """, unsafe_allow_html=True)

with roi_col2:
    st.markdown("""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #16a34a;">$1.8M</div>
        <div style="color: #166534;">Liability Reduction</div>
        <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">Fewer incidents = lower premiums</div>
    </div>
    """, unsafe_allow_html=True)

with roi_col3:
    st.markdown("""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #16a34a;">$1.2M</div>
        <div style="color: #166534;">Driver Retention</div>
        <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">Less trauma = less turnover</div>
    </div>
    """, unsafe_allow_html=True)

with roi_col4:
    st.markdown("""
    <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 2rem; font-weight: bold; color: #d97706;">$5.75M</div>
        <div style="color: #92400e; font-weight: bold;">TOTAL ROI</div>
        <div style="font-size: 0.85rem; color: #78350f; margin-top: 0.5rem;">Per 1,000 trucks annually</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# MARKET OPPORTUNITY
# =============================================================================

st.markdown("## 📈 Market Opportunity")

market_col1, market_col2 = st.columns(2)

with market_col1:
    st.markdown("""
    ### 🎯 Target Market
    
    | Segment | Size | Opportunity |
    |:---|:---|:---|
    | Truck Drivers | 3.5M | Direct users |
    | Fleet Companies | 500K+ | API integration |
    | Logistics Platforms | 1,000+ | White-label |
    | Insurance Companies | 200+ | Risk data |
    
    ### 💵 Revenue Model
    
    | Tier | Price/Month | Target |
    |:---|:---|:---|
    | Starter (<100 trucks) | $499 | Small fleets |
    | Professional (<500) | $1,999 | Mid-size |
    | Enterprise (unlimited) | $15K-50K | Large fleets |
    """)

with market_col2:
    st.markdown("""
    ### 📊 TAM / SAM / SOM
    
    - **TAM:** $175M (annual API subscription market)
    - **SAM:** $2.3B (with fleet management integration)
    - **SOM:** $50M (Year 1-3 achievable)
    
    ### 🚀 Competitive Advantage
    
    - ✅ Only API with predictive Red Zone warnings
    - ✅ Proprietary 100-point security scoring
    - ✅ 15-factor ML risk model
    - ✅ HOS-integrated recommendations
    - ✅ Sub-100ms API response
    - ✅ Enterprise SLA with 99.9% uptime
    """)

st.markdown("---")

# =============================================================================
# COMPETITIVE COMPARISON
# =============================================================================

st.markdown("## 🏆 Competitive Advantage")

st.markdown("""
| Feature | SafeTravels | TruckPark | Trucker Path | Google Maps |
|:---|:---|:---|:---|:---|
| 100-point security scoring | ✅ | ❌ | ⚠️ 5-star | ❌ |
| Proactive Red Zone alerts | ✅ | ❌ | ❌ | ❌ |
| HOS integration | ✅ | ⚠️ | ⚠️ | ❌ |
| GPS jammer detection | ✅ | ❌ | ❌ | ❌ |
| What-If time analysis | ✅ | ❌ | ❌ | ❌ |
| 15-factor risk model | ✅ | ❌ | ❌ | ❌ |
| API-first platform | ✅ | ⚠️ | ❌ | ⚠️ |
| Sub-100ms response | ✅ | ❌ | ❌ | ✅ |
| Real-time incident data | ✅ | ⚠️ | ⚠️ | ❌ |
""")

st.markdown("---")

# =============================================================================
# INVESTMENT ASK
# =============================================================================

st.markdown("## 💼 Investment Opportunity")

invest_col1, invest_col2 = st.columns(2)

with invest_col1:
    st.markdown("""
    <div style="background: #1e3a5f; color: white; border-radius: 15px; padding: 1.5rem;">
        <h3 style="margin-top: 0;">🔵 Funding Round</h3>
        <div style="font-size: 2rem; font-weight: bold;">$2M Seed</div>
        <div style="margin-top: 1rem;">
            <div>📅 Close: June 2026</div>
            <div>💰 Valuation: $12M post-money</div>
            <div>📊 Expected: 10x in 5 years</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with invest_col2:
    st.markdown("""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 15px; padding: 1.5rem;">
        <h3 style="margin-top: 0;">📊 Use of Funds</h3>
        <ul style="margin: 0; padding-left: 1.25rem;">
            <li><strong>40%</strong> - Engineering (2 backend engineers)</li>
            <li><strong>20%</strong> - Data & Operations</li>
            <li><strong>20%</strong> - Sales & Marketing</li>
            <li><strong>10%</strong> - Infrastructure</li>
            <li><strong>10%</strong> - Operations & Legal</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# CTA
# =============================================================================

st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); border-radius: 15px; color: white;">
    <h2 style="margin: 0;">Ready to Eliminate Truck Stop Crime?</h2>
    <p style="margin: 1rem 0; opacity: 0.9;">Schedule a demo or request our full investment deck</p>
    <div style="margin-top: 1rem;">
        📧 invest@safetravels.io | 🌐 safetravels.io
    </div>
</div>
""", unsafe_allow_html=True)
