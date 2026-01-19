"""
Real-Time Alerts - Alert Center
===============================

View and manage all safety alerts.
"""

import streamlit as st
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Real-Time Alerts", page_icon="🚨", layout="wide")

API_URL = "http://127.0.0.1:8000/api/v1"

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">🚨 Real-Time Alerts</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Stay protected with proactive safety warnings</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ACTIVE ALERTS SECTION
# =============================================================================

st.markdown("## 🔴 Active Alerts")

# Critical Alert
st.markdown("""
<div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
            <span style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">🔴 CRITICAL</span>
            <h3 style="margin: 0.75rem 0 0.5rem 0; color: #b91c1c;">⚠️ RED ZONE APPROACHING</h3>
            <p style="margin: 0; color: #7f1d1d;">Memphis High-Crime District - 45 miles ahead</p>
            <div style="margin-top: 0.75rem; color: #991b1b; font-size: 0.9rem;">
                ⏰ Triggered: 2 minutes ago | 📍 ETA: 52 minutes
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 2rem; font-weight: bold; color: #dc2626;">45 mi</div>
            <div style="color: #991b1b;">until Red Zone</div>
        </div>
    </div>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #fca5a5;">
        <strong>Recommended Action:</strong> Stop at Pilot #587 (12 miles) or Love's #892 (28 miles) BEFORE entering zone
    </div>
</div>
""", unsafe_allow_html=True)

col_a1, col_a2 = st.columns(2)
with col_a1:
    st.button("🅿️ Show Safe Stops Before Zone", type="primary", use_container_width=True)
with col_a2:
    st.button("❌ Dismiss Alert", use_container_width=True)

st.markdown("")

# Warning Alert
st.markdown("""
<div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
            <span style="background: #f59e0b; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">🟡 WARNING</span>
            <h3 style="margin: 0.75rem 0 0.5rem 0; color: #92400e;">⏰ HOS LIMIT APPROACHING</h3>
            <p style="margin: 0; color: #78350f;">You have 4.5 hours remaining before required 10-hour rest</p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 2rem; font-weight: bold; color: #d97706;">4.5h</div>
            <div style="color: #92400e;">remaining</div>
        </div>
    </div>
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #fcd34d;">
        <strong>Recommended:</strong> Plan overnight stop at Level 1 facility within next 3 hours
    </div>
</div>
""", unsafe_allow_html=True)

# Info Alert
st.markdown("""
<div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
            <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: bold;">ℹ️ INFO</span>
            <h3 style="margin: 0.75rem 0 0.5rem 0; color: #1e40af;">🅿️ Safe Parking Available</h3>
            <p style="margin: 0; color: #1e3a8a;">Pilot #587 has 32 spots available (12.5 miles ahead)</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# ALERT TYPES EXPLANATION
# =============================================================================

st.markdown("## 📋 Alert Types")

type_col1, type_col2, type_col3 = st.columns(3)

with type_col1:
    st.markdown("""
    ### 🔴 Red Zone Alerts
    - Approaching high-crime area
    - ETA and distance countdown
    - Safe stops before zone
    - Crime statistics for area
    
    **Trigger:** 100, 50, 20 miles before zone
    """)

with type_col2:
    st.markdown("""
    ### 🟡 Behavior Alerts
    - Speed Anomaly (creeping)
    - Unauthorized stop location
    - Dwell time warning
    - GPS signal issues
    
    **Trigger:** Real-time detection
    """)

with type_col3:
    st.markdown("""
    ### ⏰ HOS Alerts
    - Driving hours limit
    - 30-min break required
    - 10-hour rest needed
    - Violation prevention
    
    **Trigger:** 4h, 2h, 1h before limit
    """)

st.markdown("---")

# =============================================================================
# ALERT HISTORY
# =============================================================================

st.markdown("## 📜 Alert History (Last 24 Hours)")

# History table
history_data = [
    {"time": "2:30 PM", "type": "🔴 CRITICAL", "message": "Red Zone Alert - Memphis District", "status": "Active"},
    {"time": "1:45 PM", "type": "🟡 WARNING", "message": "HOS Alert - 4.5 hours remaining", "status": "Active"},
    {"time": "12:15 PM", "type": "ℹ️ INFO", "message": "Safe parking available at Pilot #587", "status": "Dismissed"},
    {"time": "11:30 AM", "type": "🟡 WARNING", "message": "Speed anomaly detected - 12 mph on I-40", "status": "Resolved"},
    {"time": "10:00 AM", "type": "✅ RESOLVED", "message": "Exited high-risk corridor successfully", "status": "Resolved"},
    {"time": "9:15 AM", "type": "🟡 WARNING", "message": "Entering high-risk corridor - I-40 West", "status": "Resolved"},
]

for alert in history_data:
    if "CRITICAL" in alert["type"]:
        bg_color = "#fee2e2"
        border_color = "#ef4444"
    elif "WARNING" in alert["type"]:
        bg_color = "#fef3c7"
        border_color = "#f59e0b"
    elif "INFO" in alert["type"]:
        bg_color = "#dbeafe"
        border_color = "#3b82f6"
    else:
        bg_color = "#d1fae5"
        border_color = "#10b981"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; padding: 0.75rem; background: {bg_color}; border-left: 4px solid {border_color}; border-radius: 8px; margin-bottom: 0.5rem;">
        <div style="width: 80px; color: #666; font-size: 0.85rem;">{alert["time"]}</div>
        <div style="width: 120px;">{alert["type"]}</div>
        <div style="flex: 1;">{alert["message"]}</div>
        <div style="color: #666; font-size: 0.85rem;">{alert["status"]}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# VOICE ALERT DEMO
# =============================================================================

st.markdown("## 🔊 Voice Alert Demo")
st.markdown("Test voice alerts using your browser's built-in speech synthesis.")

# Voice alert messages
voice_alerts = {
    "red_zone": "Warning! Red Zone ahead in 45 miles. Memphis High Crime District. Recommend stopping at Pilot 587 before entering zone.",
    "hos_warning": "Attention! You have 4 hours and 30 minutes remaining before required 10 hour rest. Plan your stop now.",
    "safe_parking": "Good news! Pilot 587 has 32 parking spots available, 12 miles ahead. Level 1 security.",
    "speed_anomaly": "Alert! Speed anomaly detected. Your speed dropped to 12 miles per hour. Are you okay?",
    "gps_jammer": "Critical! GPS signal lost for 45 seconds. Possible jammer detected. Contact dispatch immediately.",
    "emergency": "Emergency! Press SOS button to alert dispatch and share your location."
}

# JavaScript for Web Speech API
st.markdown("""
<script>
function speak(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    } else {
        alert('Sorry, your browser does not support text-to-speech.');
    }
}
</script>
""", unsafe_allow_html=True)

voice_col1, voice_col2 = st.columns(2)

with voice_col1:
    st.markdown("### 🚨 Critical Alerts")
    
    if st.button("🔴 Red Zone Warning", key="voice_red", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['red_zone']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)
    
    if st.button("📡 GPS Jammer Alert", key="voice_gps", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['gps_jammer']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)
    
    if st.button("🆘 Emergency Alert", key="voice_sos", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['emergency']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)

with voice_col2:
    st.markdown("### ⚠️ Warning Alerts")
    
    if st.button("⏰ HOS Warning", key="voice_hos", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['hos_warning']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)
    
    if st.button("🚗 Speed Anomaly", key="voice_speed", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['speed_anomaly']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)
    
    if st.button("🅿️ Safe Parking", key="voice_parking", use_container_width=True):
        st.components.v1.html(f"""
        <script>
            var msg = new SpeechSynthesisUtterance("{voice_alerts['safe_parking']}");
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        </script>
        <p style="color: green;">🔊 Playing alert...</p>
        """, height=30)

st.info("💡 **Tip:** Click any button above to hear the voice alert. Make sure your browser volume is on!")

st.markdown("---")

# =============================================================================
# ALERT SETTINGS
# =============================================================================

st.markdown("## ⚙️ Alert Settings")

setting_col1, setting_col2 = st.columns(2)

with setting_col1:
    st.markdown("### 🔔 Notification Preferences")
    st.checkbox("🔊 Sound alerts", value=True)
    st.checkbox("📳 Vibration alerts", value=True)
    st.checkbox("📱 Push notifications", value=True)
    st.checkbox("🗣️ Voice announcements", value=True)

with setting_col2:
    st.markdown("### 📏 Alert Distances")
    st.slider("Red Zone warning distance (miles)", 10, 200, 100)
    st.slider("HOS warning threshold (hours before limit)", 1, 6, 4)
    st.slider("Dwell time warning (minutes)", 5, 30, 10)
