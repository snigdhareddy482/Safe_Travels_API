"""
ROI Calculator - Fleet Savings Calculator
==========================================

Interactive calculator for fleet ROI.
"""

import streamlit as st

st.set_page_config(page_title="ROI Calculator", page_icon="💰", layout="wide")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">💰 ROI Calculator</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Calculate your fleet's potential savings with SafeTravels</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# INPUT SECTION
# =============================================================================

st.markdown("## 📊 Your Fleet Profile")

input_col1, input_col2, input_col3 = st.columns(3)

with input_col1:
    st.markdown("### 🚛 Fleet Size")
    fleet_size = st.slider("Number of Trucks", 10, 5000, 500, 10)
    
with input_col2:
    st.markdown("### 💵 Cargo Value")
    avg_cargo = st.slider("Avg Cargo Value ($)", 10000, 500000, 75000, 5000)

with input_col3:
    st.markdown("### 📈 Current Incidents")
    incidents = st.slider("Annual Theft Incidents", 0, 50, 5)

st.markdown("---")

# =============================================================================
# CALCULATIONS
# =============================================================================

# Constants
REDUCTION_RATE = 0.40  # 40% theft reduction
LIABILITY_PER_TRUCK = 1800
RETENTION_PER_TRUCK = 1200
HOS_SAVINGS_PER_TRUCK = 450

# Calculate savings
prevented_thefts = int(incidents * REDUCTION_RATE)
theft_savings = prevented_thefts * avg_cargo
liability_savings = fleet_size * LIABILITY_PER_TRUCK
retention_savings = fleet_size * RETENTION_PER_TRUCK
hos_savings = fleet_size * HOS_SAVINGS_PER_TRUCK
total_savings = theft_savings + liability_savings + retention_savings + hos_savings

# Pricing tier
if fleet_size <= 100:
    price = 499
    tier = "Starter"
elif fleet_size <= 500:
    price = 1999
    tier = "Professional"
else:
    price = 4999 + (fleet_size - 500) * 5  # Custom pricing
    tier = "Enterprise"

annual_cost = price * 12
roi_multiple = total_savings / annual_cost if annual_cost > 0 else 0
payback_months = (annual_cost / (total_savings / 12)) if total_savings > 0 else 0

# =============================================================================
# RESULTS
# =============================================================================

st.markdown("## 💰 Your Projected Savings")

# Summary card
st.markdown(f"""
<div style="background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem;">
    <div style="font-size: 1.25rem; opacity: 0.9;">Annual Savings for {fleet_size} Trucks</div>
    <div style="font-size: 4rem; font-weight: bold;">${total_savings:,.0f}</div>
    <div style="font-size: 1.25rem; margin-top: 0.5rem;">ROI: {roi_multiple:.0f}x | Payback: {payback_months:.1f} months</div>
</div>
""", unsafe_allow_html=True)

# Breakdown
result_col1, result_col2, result_col3, result_col4 = st.columns(4)

with result_col1:
    st.markdown(f"""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">🛡️ Theft Prevention</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: #16a34a;">${theft_savings:,.0f}</div>
        <div style="font-size: 0.85rem; color: #666;">{prevented_thefts} thefts prevented</div>
    </div>
    """, unsafe_allow_html=True)

with result_col2:
    st.markdown(f"""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">⚖️ Liability Reduction</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: #16a34a;">${liability_savings:,.0f}</div>
        <div style="font-size: 0.85rem; color: #666;">${LIABILITY_PER_TRUCK}/truck</div>
    </div>
    """, unsafe_allow_html=True)

with result_col3:
    st.markdown(f"""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">👥 Driver Retention</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: #16a34a;">${retention_savings:,.0f}</div>
        <div style="font-size: 0.85rem; color: #666;">${RETENTION_PER_TRUCK}/truck</div>
    </div>
    """, unsafe_allow_html=True)

with result_col4:
    st.markdown(f"""
    <div style="background: #f0fdf4; border: 1px solid #22c55e; border-radius: 12px; padding: 1.25rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">⏰ HOS Compliance</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: #16a34a;">${hos_savings:,.0f}</div>
        <div style="font-size: 0.85rem; color: #666;">${HOS_SAVINGS_PER_TRUCK}/truck</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# PRICING COMPARISON
# =============================================================================

st.markdown("## 💳 Pricing vs. Savings")

price_col1, price_col2, price_col3 = st.columns(3)

with price_col1:
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #666;">Your Plan: {tier}</div>
        <div style="font-size: 2rem; font-weight: bold; color: #1e3a5f;">${annual_cost:,.0f}/year</div>
        <div style="font-size: 0.85rem; color: #666;">${price}/month</div>
    </div>
    """, unsafe_allow_html=True)

with price_col2:
    st.markdown(f"""
    <div style="background: #d1fae5; border: 1px solid #10b981; border-radius: 12px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #065f46;">Annual Savings</div>
        <div style="font-size: 2rem; font-weight: bold; color: #16a34a;">${total_savings:,.0f}</div>
        <div style="font-size: 0.85rem; color: #065f46;">Projected value</div>
    </div>
    """, unsafe_allow_html=True)

with price_col3:
    st.markdown(f"""
    <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 0.9rem; color: #92400e;">Return on Investment</div>
        <div style="font-size: 2rem; font-weight: bold; color: #d97706;">{roi_multiple:.0f}x</div>
        <div style="font-size: 0.85rem; color: #92400e;">Payback: {payback_months:.1f} months</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# PRICING TIERS
# =============================================================================

st.markdown("## 📋 Pricing Plans")

tier_col1, tier_col2, tier_col3 = st.columns(3)

with tier_col1:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 15px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 1.25rem; font-weight: bold; color: #1e3a5f;">📱 Starter</div>
        <div style="font-size: 2.5rem; font-weight: bold; color: #3b82f6; margin: 1rem 0;">$499<span style="font-size: 1rem; color: #666;">/mo</span></div>
        <ul style="text-align: left; padding-left: 1.25rem; color: #666;">
            <li>Up to 100 trucks</li>
            <li>10,000 API calls/month</li>
            <li>Email support</li>
            <li>Basic analytics</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with tier_col2:
    st.markdown("""
    <div style="background: white; border: 2px solid #3b82f6; border-radius: 15px; padding: 1.5rem; text-align: center; position: relative;">
        <div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #3b82f6; color: white; padding: 4px 16px; border-radius: 20px; font-size: 0.8rem;">POPULAR</div>
        <div style="font-size: 1.25rem; font-weight: bold; color: #1e3a5f;">🚀 Professional</div>
        <div style="font-size: 2.5rem; font-weight: bold; color: #3b82f6; margin: 1rem 0;">$1,999<span style="font-size: 1rem; color: #666;">/mo</span></div>
        <ul style="text-align: left; padding-left: 1.25rem; color: #666;">
            <li>Up to 500 trucks</li>
            <li>100,000 API calls/month</li>
            <li>Priority support + Slack</li>
            <li>Advanced analytics</li>
            <li>Custom integrations</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with tier_col3:
    st.markdown("""
    <div style="background: #1e3a5f; color: white; border-radius: 15px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 1.25rem; font-weight: bold;">🏢 Enterprise</div>
        <div style="font-size: 2.5rem; font-weight: bold; margin: 1rem 0;">Custom</div>
        <ul style="text-align: left; padding-left: 1.25rem; opacity: 0.9;">
            <li>Unlimited trucks & API</li>
            <li>24/7 phone support</li>
            <li>Dedicated account manager</li>
            <li>Custom SLA</li>
            <li>White-label options</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# CTA
# =============================================================================

st.markdown("""
<div style="text-align: center; padding: 1.5rem; background: #f0fdf4; border: 2px solid #22c55e; border-radius: 15px;">
    <h3 style="color: #166534; margin: 0;">Ready to save ${0:,.0f} annually?</h3>
    <p style="color: #047857; margin: 0.5rem 0;">Start your 30-day free trial today</p>
</div>
""".format(total_savings), unsafe_allow_html=True)
