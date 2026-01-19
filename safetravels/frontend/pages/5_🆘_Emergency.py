"""
Emergency Mode - SOS & Quick Help
=================================

One-tap emergency assistance with GPS sharing.
"""

import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Emergency Mode", page_icon="🆘", layout="wide")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 1.5rem;">
    <h1 style="margin:0; font-size: 2.5rem;">🆘 EMERGENCY MODE</h1>
    <p style="margin:0.5rem 0 0 0; font-size: 1.2rem;">Quick access to emergency services and help</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SOS BUTTON
# =============================================================================

st.markdown("")

col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="
            width: 200px; 
            height: 200px; 
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 30px rgba(220, 38, 38, 0.5);
            cursor: pointer;
            transition: transform 0.2s;
        ">
            <div style="color: white; text-align: center;">
                <div style="font-size: 3rem;">🆘</div>
                <div style="font-size: 1.5rem; font-weight: bold;">SOS</div>
            </div>
        </div>
        <p style="margin-top: 1rem; color: #666;">Press and hold for 3 seconds to activate</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚨 ACTIVATE EMERGENCY SOS", type="primary", use_container_width=True):
        st.error("⚠️ SOS ACTIVATED - Location shared with emergency contacts and dispatch")

st.markdown("---")

# =============================================================================
# QUICK ACTIONS
# =============================================================================

st.markdown("## ⚡ Quick Emergency Actions")

action_col1, action_col2, action_col3 = st.columns(3)

with action_col1:
    st.markdown("""
    <div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">📞</div>
        <h3 style="margin: 0.5rem 0; color: #b91c1c;">Call 911</h3>
        <p style="color: #7f1d1d; font-size: 0.9rem; margin: 0;">Direct line to emergency services</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("📞 CALL 911", key="btn_911", use_container_width=True)

with action_col2:
    st.markdown("""
    <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">📍</div>
        <h3 style="margin: 0.5rem 0; color: #92400e;">Share Location</h3>
        <p style="color: #78350f; font-size: 0.9rem; margin: 0;">Send GPS to trusted contacts</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("📍 SHARE MY LOCATION", key="btn_share", use_container_width=True)

with action_col3:
    st.markdown("""
    <div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">🏢</div>
        <h3 style="margin: 0.5rem 0; color: #1e40af;">Call Dispatch</h3>
        <p style="color: #1e3a8a; font-size: 0.9rem; margin: 0;">Contact your fleet dispatcher</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🏢 CALL DISPATCH", key="btn_dispatch", use_container_width=True)

st.markdown("")

action_col4, action_col5, action_col6 = st.columns(3)

with action_col4:
    st.markdown("""
    <div style="background: #d1fae5; border: 2px solid #10b981; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">🏥</div>
        <h3 style="margin: 0.5rem 0; color: #065f46;">Nearest Hospital</h3>
        <p style="color: #047857; font-size: 0.9rem; margin: 0;">Find closest medical facility</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🏥 FIND HOSPITAL", key="btn_hospital", use_container_width=True)

with action_col5:
    st.markdown("""
    <div style="background: #e0e7ff; border: 2px solid #6366f1; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">👮</div>
        <h3 style="margin: 0.5rem 0; color: #4338ca;">Nearest Police</h3>
        <p style="color: #4f46e5; font-size: 0.9rem; margin: 0;">Find closest police station</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("👮 FIND POLICE", key="btn_police", use_container_width=True)

with action_col6:
    st.markdown("""
    <div style="background: #fce7f3; border: 2px solid #ec4899; border-radius: 12px; padding: 1.5rem; text-align: center; height: 180px;">
        <div style="font-size: 3rem;">🎭</div>
        <h3 style="margin: 0.5rem 0; color: #be185d;">Fake Call</h3>
        <p style="color: #9d174d; font-size: 0.9rem; margin: 0;">Screen harassment attempt</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🎭 START FAKE CALL", key="btn_fake", use_container_width=True)

st.markdown("---")

# =============================================================================
# CURRENT LOCATION
# =============================================================================

st.markdown("## 📍 Your Current Location")

loc_col1, loc_col2 = st.columns([2, 1])

with loc_col1:
    st.markdown("""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0;">📍 I-40 Westbound, Mile Marker 234</h3>
                <p style="color: #666; margin: 0.5rem 0;">Williamson County, Tennessee</p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.85rem; color: #666;">GPS Coordinates</div>
                <div style="font-family: monospace;">35.9606° N, 86.8268° W</div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
            <div style="display: flex; gap: 2rem;">
                <div>🚔 <strong>Nearest Police:</strong> 4.2 miles (Williamson County Sheriff)</div>
                <div>🏥 <strong>Nearest Hospital:</strong> 8.5 miles (Williamson Medical)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with loc_col2:
    st.markdown(f"""
    <div style="background: #1e293b; color: white; border-radius: 12px; padding: 1.5rem; text-align: center;">
        <div style="font-size: 0.85rem; opacity: 0.8;">Last Updated</div>
        <div style="font-size: 1.5rem; font-weight: bold;">{datetime.now().strftime("%I:%M:%S %p")}</div>
        <div style="margin-top: 0.5rem;">
            <span style="background: #22c55e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem;">● GPS Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# EMERGENCY CONTACTS
# =============================================================================

st.markdown("## 📱 Emergency Contacts")

contact_col1, contact_col2, contact_col3 = st.columns(3)

with contact_col1:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 50px; height: 50px; background: #dbeafe; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.5rem;">🏢</span>
            </div>
            <div>
                <div style="font-weight: bold;">Fleet Dispatch</div>
                <div style="color: #3b82f6; font-size: 1.1rem;">(555) 123-4567</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with contact_col2:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 50px; height: 50px; background: #fce7f3; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.5rem;">👨‍👩‍👧</span>
            </div>
            <div>
                <div style="font-weight: bold;">Family (Wife)</div>
                <div style="color: #ec4899; font-size: 1.1rem;">(555) 987-6543</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with contact_col3:
    st.markdown("""
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 50px; height: 50px; background: #dcfce7; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.5rem;">🛡️</span>
            </div>
            <div>
                <div style="font-weight: bold;">Safety Team</div>
                <div style="color: #22c55e; font-size: 1.1rem;">(555) 456-7890</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# INCIDENT REPORTING
# =============================================================================

st.markdown("## 📝 Report Incident")

with st.expander("📝 Click to report an incident", expanded=False):
    st.markdown("### What type of incident?")
    
    incident_type = st.selectbox(
        "Incident Type",
        ["Select...", "Theft from vehicle", "Personal assault/harassment", "Vehicle damage", "Scam/fraud", "Poor stop conditions", "Other"]
    )
    
    incident_desc = st.text_area("Description", placeholder="Describe what happened...")
    
    st.markdown("### 📍 Location")
    st.text_input("Stop Name or Location", placeholder="e.g., Pilot #587 or I-40 Mile 234")
    
    st.checkbox("📷 Add photos/video", value=False)
    st.checkbox("🔒 Report anonymously", value=True)
    
    st.button("📤 Submit Report", type="primary")
    
    st.info("ℹ️ Your report helps other drivers stay safe. All incidents are reviewed before publishing.")
