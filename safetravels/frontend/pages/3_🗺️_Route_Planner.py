"""
Route Planner - Plan Safe Routes
================================

Plan trips with Red Zone avoidance and stop recommendations.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import os

st.set_page_config(page_title="Route Planner", page_icon="🗺️", layout="wide")

API_URL = "http://127.0.0.1:8000/api/v1"
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def geocode_address(address):
    """Convert address to coordinates using Google Geocoding API."""
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GOOGLE_API_KEY},
            timeout=5
        )
        if r.status_code == 200 and r.json().get("status") == "OK":
            result = r.json()["results"][0]
            loc = result["geometry"]["location"]
            return loc["lat"], loc["lng"], result.get("formatted_address", address)
    except Exception as e:
        st.warning(f"Could not geocode address: {e}")
    return None, None, None

def get_route_info(origin, destination):
    """Get route information from Google Routes API."""
    try:
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_API_KEY,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs"
        }
        data = {
            "origin": {"address": origin},
            "destination": {"address": destination},
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE"
        }
        r = requests.post(url, headers=headers, json=data, timeout=10)
        if r.status_code == 200:
            routes = r.json().get("routes", [])
            if routes:
                route = routes[0]
                distance_miles = route.get("distanceMeters", 0) / 1609.34
                duration_mins = int(route.get("duration", "0s").replace("s", "")) // 60
                return {
                    "distance_miles": round(distance_miles, 1),
                    "duration_hours": duration_mins // 60,
                    "duration_mins": duration_mins % 60,
                    "success": True
                }
    except Exception as e:
        st.warning(f"Could not get route: {e}")
    return {"success": False}

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">🗺️ Route Planner</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Plan safe routes with Red Zone avoidance & stop recommendations</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ROUTE INPUT
# =============================================================================

st.markdown("### 📍 Enter Your Route")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🚀 Starting Point")
    start_address = st.text_input(
        "From",
        value="Dallas, TX",
        placeholder="Enter starting address, city, or location..."
    )

with col2:
    st.markdown("#### 🏁 Destination")
    end_address = st.text_input(
        "To",
        value="Memphis, TN",
        placeholder="Enter destination address, city, or location..."
    )

# Options
st.markdown("### ⚙️ Route Options")

opt_col1, opt_col2, opt_col3 = st.columns(3)

with opt_col1:
    avoid_red_zones = st.checkbox("🔴 Avoid Red Zones", value=True)
    include_stops = st.checkbox("🅿️ Include Safe Stops", value=True)

with opt_col2:
    hos_hours = st.number_input("Current HOS Hours Driven", value=2.0, min_value=0.0, max_value=11.0, step=0.5)
    departure_time = st.time_input("Departure Time")

with opt_col3:
    route_preference = st.selectbox("Optimize For", ["Safest Route", "Fastest Route", "Balanced"])
    
plan_btn = st.button("🚀 Plan My Route", type="primary", use_container_width=True)

# Geocode addresses and get route
start_lat, start_lon = 32.7767, -96.7970  # Default Dallas
end_lat, end_lon = 35.1495, -90.0490  # Default Memphis
route_info = None

if plan_btn:
    with st.spinner("🔍 Finding best route..."):
        # Geocode start
        lat, lng, addr = geocode_address(start_address)
        if lat and lng:
            start_lat, start_lon = lat, lng
            st.success(f"📍 Start: **{addr}**")
        
        # Geocode end
        lat, lng, addr = geocode_address(end_address)
        if lat and lng:
            end_lat, end_lon = lat, lng
            st.success(f"🏁 Destination: **{addr}**")
        
        # Get route
        route_info = get_route_info(start_address, end_address)
        if route_info.get("success"):
            st.info(f"📏 Distance: **{route_info['distance_miles']} miles** | ⏱️ Time: **{route_info['duration_hours']}h {route_info['duration_mins']}m**")

st.markdown("---")

# =============================================================================
# ROUTE COMPARISON
# =============================================================================

st.markdown("## 📊 Route Comparison")

route_col1, route_col2, route_col3 = st.columns(3)

with route_col1:
    st.markdown("""
    <div style="background: #f0fdf4; border: 2px solid #22c55e; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin:0; color: #16a34a;">🟢 SAFEST</h4>
            <span style="background: #22c55e; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">RECOMMENDED</span>
        </div>
        <div style="margin: 1rem 0;">
            <div><strong>Distance:</strong> 524 miles</div>
            <div><strong>Time:</strong> 8h 15m</div>
            <div><strong>Fuel Cost:</strong> ~$145</div>
        </div>
        <div style="margin: 1rem 0; padding: 0.5rem; background: #dcfce7; border-radius: 8px;">
            <div style="color: #16a34a;">✅ 0 Red Zones</div>
            <div style="color: #16a34a;">✅ 3 Safe Stops</div>
            <div style="color: #16a34a;">✅ All Level 1-2 stops</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Select Safest Route", key="safe_route", use_container_width=True)

with route_col2:
    st.markdown("""
    <div style="background: #fefce8; border: 2px solid #eab308; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin:0; color: #ca8a04;">🟡 FASTEST</h4>
            <span style="background: #f59e0b; color: white; padding: 4px 8px; border-radius: 20px; font-size: 0.8rem;">⚠️ 2 RED ZONES</span>
        </div>
        <div style="margin: 1rem 0;">
            <div><strong>Distance:</strong> 480 miles</div>
            <div><strong>Time:</strong> 7h 30m</div>
            <div><strong>Fuel Cost:</strong> ~$132</div>
        </div>
        <div style="margin: 1rem 0; padding: 0.5rem; background: #fef3c7; border-radius: 8px;">
            <div style="color: #d97706;">⚠️ 2 Red Zones on route</div>
            <div style="color: #d97706;">⚠️ Memphis High-Crime District</div>
            <div style="color: #16a34a;">✅ 2 Safe Stops</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Select Fastest Route", key="fast_route", use_container_width=True)

with route_col3:
    st.markdown("""
    <div style="background: #f5f5f5; border: 2px solid #9ca3af; border-radius: 12px; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin:0; color: #6b7280;">⚖️ BALANCED</h4>
            <span style="background: #9ca3af; color: white; padding: 4px 8px; border-radius: 20px; font-size: 0.8rem;">1 RED ZONE</span>
        </div>
        <div style="margin: 1rem 0;">
            <div><strong>Distance:</strong> 510 miles</div>
            <div><strong>Time:</strong> 8h 05m</div>
            <div><strong>Fuel Cost:</strong> ~$140</div>
        </div>
        <div style="margin: 1rem 0; padding: 0.5rem; background: #f3f4f6; border-radius: 8px;">
            <div style="color: #d97706;">⚠️ 1 Red Zone (avoidable)</div>
            <div style="color: #16a34a;">✅ 3 Safe Stops</div>
            <div style="color: #16a34a;">✅ Mostly Level 1-2</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.button("Select Balanced Route", key="bal_route", use_container_width=True)

st.markdown("---")

# =============================================================================
# ROUTE MAP
# =============================================================================

st.markdown("## 🗺️ Route Visualization")

m = folium.Map(location=[(start_lat + end_lat)/2, (start_lon + end_lon)/2], zoom_start=6)

# Start marker
folium.Marker(
    [start_lat, start_lon],
    popup="🚀 START: Dallas, TX",
    icon=folium.Icon(color="blue", icon="play", prefix="fa")
).add_to(m)

# End marker
folium.Marker(
    [end_lat, end_lon],
    popup="🏁 END: Memphis, TN",
    icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
).add_to(m)

# Red Zone (circle)
folium.Circle(
    [35.1495, -90.0490],
    radius=30000,  # 30km
    popup="🔴 RED ZONE: Memphis High-Crime District",
    color="red",
    fill=True,
    fill_opacity=0.3
).add_to(m)

# Safe stops on route
folium.Marker(
    [33.5, -92.5],
    popup="🟢 Pilot #587 (Score: 87)<br/>Level 1",
    icon=folium.Icon(color="green", icon="parking", prefix="fa")
).add_to(m)

folium.Marker(
    [34.2, -91.0],
    popup="🟢 TA #234 (Score: 91)<br/>Level 1",
    icon=folium.Icon(color="green", icon="parking", prefix="fa")
).add_to(m)

# Route line
route_coords = [[start_lat, start_lon], [33.5, -92.5], [34.2, -91.0], [end_lat, end_lon]]
folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.8).add_to(m)

st_folium(m, width=1000, height=500)

# =============================================================================
# RECOMMENDED STOPS ALONG ROUTE
# =============================================================================

st.markdown("---")
st.markdown("## 🅿️ Recommended Stops Along Route")

stop_col1, stop_col2, stop_col3 = st.columns(3)

with stop_col1:
    st.markdown("""
    <div style="background: white; border: 1px solid #22c55e; border-radius: 12px; padding: 1rem;">
        <div style="color: #666; font-size: 0.85rem;">STOP 1 • Mile 125</div>
        <h4 style="margin: 0.25rem 0;">Pilot #587</h4>
        <div style="color: #16a34a; font-weight: bold;">🟢 Level 1 • 87/100</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem;">
            Recommended for: <strong>30-min break</strong><br/>
            ETA: 2h 15m from start
        </div>
    </div>
    """, unsafe_allow_html=True)

with stop_col2:
    st.markdown("""
    <div style="background: white; border: 1px solid #22c55e; border-radius: 12px; padding: 1rem;">
        <div style="color: #666; font-size: 0.85rem;">STOP 2 • Mile 280</div>
        <h4 style="margin: 0.25rem 0;">TA Travel Center #234</h4>
        <div style="color: #16a34a; font-weight: bold;">🟢 Level 1 • 91/100</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem;">
            Recommended for: <strong>Fuel + Food</strong><br/>
            ETA: 4h 45m from start
        </div>
    </div>
    """, unsafe_allow_html=True)

with stop_col3:
    st.markdown("""
    <div style="background: white; border: 1px solid #f59e0b; border-radius: 12px; padding: 1rem;">
        <div style="color: #666; font-size: 0.85rem;">STOP 3 • Mile 420 (IF OVERNIGHT)</div>
        <h4 style="margin: 0.25rem 0;">Love's #892</h4>
        <div style="color: #d97706; font-weight: bold;">🟡 Level 2 • 72/100</div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem;">
            Recommended for: <strong>Overnight rest</strong><br/>
            ⚠️ BEFORE Red Zone entry
        </div>
    </div>
    """, unsafe_allow_html=True)
