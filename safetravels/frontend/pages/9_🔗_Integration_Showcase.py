"""
Integration Showcase - Partner Integration Examples
===================================================

Shows how partners integrate SafeTravels API.
"""

import streamlit as st

st.set_page_config(page_title="Integration Showcase", page_icon="🔗", layout="wide")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">🔗 Integration Showcase</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">See how partners use SafeTravels API in their systems</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# INTEGRATION EXAMPLES
# =============================================================================

st.markdown("## 📱 Integration Examples")

# TMS Integration
st.markdown("### 1️⃣ Fleet Management System (TMS)")

st.markdown("""
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
            <h4 style="margin: 0; color: #1e3a5f;">🏢 Dispatch Dashboard</h4>
            <p style="color: #64748b; margin: 0.5rem 0;">How fleet managers use SafeTravels in their dispatch system</p>
        </div>
        <span style="background: #22c55e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">LIVE INTEGRATION</span>
    </div>
    
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
        <div style="border-bottom: 1px solid #e5e7eb; padding-bottom: 1rem; margin-bottom: 1rem;">
            <strong>Driver: John Smith - Truck #4892</strong><br/>
            Route: Dallas, TX → Memphis, TN<br/>
            Status: 6/11 hours driven, approaching Red Zone
        </div>
        
        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 8px;">
            <strong>🤖 AI RECOMMENDATION (via SafeTravels API):</strong><br/>
            "Stop at Pilot #892 in 12 miles (LEVEL 1, Score: 87/100)"<br/>
            <em>Safe stop before Memphis Red Zone</em>
        </div>
        
        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
            <span style="background: #22c55e; color: white; padding: 8px 16px; border-radius: 8px; cursor: pointer;">✓ Approve</span>
            <span style="background: #e5e7eb; color: #374151; padding: 8px 16px; border-radius: 8px; cursor: pointer;">Suggest Alternative</span>
            <span style="background: #fee2e2; color: #b91c1c; padding: 8px 16px; border-radius: 8px; cursor: pointer;">Override</span>
        </div>
        
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.85rem; color: #64748b;">
            <strong>POWERED BY SAFETRAVELS API</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Driver App Integration
st.markdown("### 2️⃣ Driver Mobile App")

st.markdown("""
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
            <h4 style="margin: 0; color: #1e3a5f;">📱 In-Cab Driver App</h4>
            <p style="color: #64748b; margin: 0.5rem 0;">How drivers receive SafeTravels alerts in their app</p>
        </div>
        <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">MOBILE SDK</span>
    </div>
    
    <div style="background: #1e293b; border-radius: 20px; padding: 1.5rem; margin-top: 1rem; max-width: 350px;">
        <div style="background: #fee2e2; border-radius: 12px; padding: 1rem; color: #7f1d1d; margin-bottom: 1rem;">
            <strong>🚨 ALERT: Red Zone in 45 miles</strong><br/>
            Memphis High-Crime District
        </div>
        
        <div style="color: white; margin-bottom: 1rem;">
            <strong>✅ Top Recommended Stops:</strong>
        </div>
        
        <div style="background: #374151; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem;">
            <div style="color: white; display: flex; justify-content: space-between;">
                <span>1. Pilot #892</span>
                <span style="color: #22c55e;">⭐ 4.8</span>
            </div>
            <div style="color: #9ca3af; font-size: 0.85rem;">12 miles • 🟢 Level 1</div>
        </div>
        
        <div style="background: #374151; border-radius: 8px; padding: 0.75rem;">
            <div style="color: white; display: flex; justify-content: space-between;">
                <span>2. Love's #445</span>
                <span style="color: #22c55e;">⭐ 4.5</span>
            </div>
            <div style="color: #9ca3af; font-size: 0.85rem;">28 miles • 🟡 Level 2</div>
        </div>
        
        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
            <span style="background: #3b82f6; color: white; padding: 8px 16px; border-radius: 8px; flex: 1; text-align: center;">Navigate</span>
            <span style="background: #374151; color: white; padding: 8px 16px; border-radius: 8px; flex: 1; text-align: center;">Call</span>
        </div>
        
        <div style="margin-top: 1rem; text-align: center; font-size: 0.75rem; color: #64748b;">
            POWERED BY SAFETRAVELS API
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Insurance Platform
st.markdown("### 3️⃣ Insurance Risk Platform")

st.markdown("""
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
            <h4 style="margin: 0; color: #1e3a5f;">🛡️ Insurance Risk Assessment</h4>
            <p style="color: #64748b; margin: 0.5rem 0;">How insurers use SafeTravels data for underwriting</p>
        </div>
        <span style="background: #8b5cf6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">DATA API</span>
    </div>
    
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div>
                <strong>Fleet Safety Score</strong><br/>
                <span style="color: #64748b;">Acme Trucking Co. (500 trucks)</span>
            </div>
            <div style="font-size: 3rem; font-weight: bold; color: #16a34a;">8.7<span style="font-size: 1rem; color: #64748b;">/10</span></div>
        </div>
        
        <div style="background: #d1fae5; border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
            <strong style="color: #065f46;">✅ 92% of drivers stopping at Level 1-2 locations</strong><br/>
            <span style="color: #047857;">Premium Discount: 12% ($45,000 annual savings)</span>
        </div>
        
        <div style="display: flex; gap: 1rem;">
            <div style="flex: 1; background: #f8fafc; padding: 1rem; border-radius: 8px; text-align: center;">
                <div style="color: #64748b; font-size: 0.85rem;">Theft Incidents (YTD)</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #16a34a;">2</div>
                <div style="color: #22c55e; font-size: 0.85rem;">↓ 60% from last year</div>
            </div>
            <div style="flex: 1; background: #f8fafc; padding: 1rem; border-radius: 8px; text-align: center;">
                <div style="color: #64748b; font-size: 0.85rem;">Red Zone Stops</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #16a34a;">3%</div>
                <div style="color: #22c55e; font-size: 0.85rem;">Industry avg: 18%</div>
            </div>
        </div>
        
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.85rem; color: #64748b;">
            <strong>POWERED BY SAFETRAVELS API</strong>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SUCCESS STORIES
# =============================================================================

st.markdown("## 🏆 Partner Success Stories")

story_col1, story_col2, story_col3 = st.columns(3)

with story_col1:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 15px; padding: 1.5rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⭐⭐⭐⭐⭐</div>
        <p style="font-style: italic; color: #374151; margin-bottom: 1rem;">
            "SafeTravels API reduced our cargo theft by <strong>40%</strong> in the first month. 
            We're now recommending it to all fleet customers."
        </p>
        <div style="border-top: 1px solid #e5e7eb; padding-top: 1rem;">
            <strong>John Smith</strong><br/>
            <span style="color: #64748b;">VP Operations, Schneider National</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with story_col2:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 15px; padding: 1.5rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⭐⭐⭐⭐⭐</div>
        <p style="font-style: italic; color: #374151; margin-bottom: 1rem;">
            "Saved us <strong>$1.2M</strong> in the first year. ROI paid for itself in Q1. 
            This is the single best safety investment we've made."
        </p>
        <div style="border-top: 1px solid #e5e7eb; padding-top: 1rem;">
            <strong>Sarah Lee</strong><br/>
            <span style="color: #64748b;">CEO, JB Hunt Express</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with story_col3:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 15px; padding: 1.5rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⭐⭐⭐⭐⭐</div>
        <p style="font-style: italic; color: #374151; margin-bottom: 1rem;">
            "Our drivers feel SO much safer. Driver retention improved <strong>15%</strong>. 
            Integration was seamless - live in 2 weeks."
        </p>
        <div style="border-top: 1px solid #e5e7eb; padding-top: 1rem;">
            <strong>Mike Johnson</strong><br/>
            <span style="color: #64748b;">Safety Director, Werner Enterprises</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# INTEGRATION PROCESS
# =============================================================================

st.markdown("## 🚀 Integration Process")

process_col1, process_col2, process_col3, process_col4 = st.columns(4)

with process_col1:
    st.markdown("""
    <div style="text-align: center;">
        <div style="width: 60px; height: 60px; background: #dbeafe; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.5rem;">1</div>
        <h4 style="margin: 1rem 0 0.5rem 0;">Sign Up</h4>
        <p style="color: #64748b; font-size: 0.9rem;">Get API keys in minutes</p>
    </div>
    """, unsafe_allow_html=True)

with process_col2:
    st.markdown("""
    <div style="text-align: center;">
        <div style="width: 60px; height: 60px; background: #dbeafe; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.5rem;">2</div>
        <h4 style="margin: 1rem 0 0.5rem 0;">Integrate</h4>
        <p style="color: #64748b; font-size: 0.9rem;">Simple REST API + SDKs</p>
    </div>
    """, unsafe_allow_html=True)

with process_col3:
    st.markdown("""
    <div style="text-align: center;">
        <div style="width: 60px; height: 60px; background: #dbeafe; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.5rem;">3</div>
        <h4 style="margin: 1rem 0 0.5rem 0;">Test</h4>
        <p style="color: #64748b; font-size: 0.9rem;">Sandbox environment</p>
    </div>
    """, unsafe_allow_html=True)

with process_col4:
    st.markdown("""
    <div style="text-align: center;">
        <div style="width: 60px; height: 60px; background: #22c55e; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.5rem; color: white;">✓</div>
        <h4 style="margin: 1rem 0 0.5rem 0;">Go Live</h4>
        <p style="color: #64748b; font-size: 0.9rem;">Deploy in 2 weeks</p>
    </div>
    """, unsafe_allow_html=True)
