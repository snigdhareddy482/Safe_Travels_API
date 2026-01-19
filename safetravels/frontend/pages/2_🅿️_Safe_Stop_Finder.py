"""
Safe Stop Finder - Full Stop Search Experience
===============================================

Find safe parking with filters, details, and navigation.
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import json
import os

st.set_page_config(page_title="Safe Stop Finder", page_icon="🅿️", layout="wide")

API_URL = "http://127.0.0.1:8000/api/v1"
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyCJlOD5zLaZkKYFdiUtU3-QfPBLVTrBQlo")

# =============================================================================
# HELPER FUNCTION - GEOCODE ADDRESS
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

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%); padding: 1.5rem; border-radius: 15px; color: white; margin-bottom: 1rem;">
    <h1 style="margin:0;">🅿️ Safe Stop Finder</h1>
    <p style="margin:0.5rem 0 0 0; opacity:0.9;">Find secure parking with 100-point security scoring</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SEARCH FILTERS
# =============================================================================

st.markdown("### 🔍 Search Criteria")

filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])

with filter_col1:
    location_address = st.text_input(
        "📍 Your Current Location", 
        value="Dallas, TX",
        placeholder="Enter city, address, or truck stop name..."
    )

with filter_col2:
    radius = st.slider("Search Radius (miles)", 10, 200, 100)
    min_score = st.slider("Minimum Security Score", 0, 100, 60)

with filter_col3:
    min_tier = st.selectbox("Minimum Security Tier", ["Any", "Level 1 Only", "Level 1-2"])
    amenities = st.multiselect(
        "Required Amenities",
        ["Fuel", "Food", "Showers", "Laundry", "WiFi", "Repair"],
        default=["Fuel"]
    )

search_btn = st.button("🔍 Find Safe Stops Near Me", type="primary", use_container_width=True)

# Geocode the address
latitude, longitude = 32.7767, -96.7970  # Default to Dallas
formatted_address = location_address

if location_address:
    lat, lng, addr = geocode_address(location_address)
    if lat and lng:
        latitude, longitude = lat, lng
        formatted_address = addr
        if search_btn:
            st.success(f"📍 Searching near: **{formatted_address}** ({latitude:.4f}, {longitude:.4f})")

st.markdown("---")

# =============================================================================
# RESULTS
# =============================================================================

col_map, col_list = st.columns([1.5, 1])

with col_map:
    st.markdown("### 🗺️ Stop Locations")
    
    m = folium.Map(location=[latitude, longitude], zoom_start=9)
    
    # Current location
    folium.Marker(
        [latitude, longitude],
        popup="📍 Your Location",
        icon=folium.Icon(color="blue", icon="truck", prefix="fa")
    ).add_to(m)
    
    # Try to get stops from API
    stops_data = []
    try:
        response = requests.get(
            f"{API_URL}/safe-stops",
            params={"latitude": latitude, "longitude": longitude, "radius_miles": radius},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            stops_data = data.get("stops", [])
    except:
        pass
    
    # Fallback mock data
    if not stops_data:
        stops_data = [
            {"name": "Pilot Travel Center #587", "security_score": 87, "tier": "Level 1", "distance_miles": 12.5, "latitude": latitude + 0.1, "longitude": longitude + 0.05, "amenities": ["Fuel", "Food", "Showers"], "parking_spaces": 45, "available": 32},
            {"name": "Love's Travel Stop #567", "security_score": 65, "tier": "Level 2", "distance_miles": 28, "latitude": latitude - 0.15, "longitude": longitude + 0.1, "amenities": ["Fuel", "Food"], "parking_spaces": 30, "available": 8},
            {"name": "TA Travel Center #234", "security_score": 91, "tier": "Level 1", "distance_miles": 42, "latitude": latitude + 0.2, "longitude": longitude - 0.1, "amenities": ["Fuel", "Food", "Showers", "Laundry"], "parking_spaces": 60, "available": 45},
            {"name": "Flying J #892", "security_score": 78, "tier": "Level 2", "distance_miles": 55, "latitude": latitude - 0.25, "longitude": longitude - 0.15, "amenities": ["Fuel", "Food", "WiFi"], "parking_spaces": 35, "available": 12},
        ]
    
    # Add stop markers
    for stop in stops_data:
        score = stop.get("security_score", 50)
        name = stop.get("name", "Unknown")
        
        if score >= 80:
            color = "green"
            tier_icon = "🟢"
        elif score >= 60:
            color = "orange"
            tier_icon = "🟡"
        else:
            color = "red"
            tier_icon = "🔴"
        
        lat = stop.get("latitude", stop.get("location", {}).get("latitude", latitude + 0.1))
        lon = stop.get("longitude", stop.get("location", {}).get("longitude", longitude + 0.1))
        
        popup_html = f"""
        <b>{name}</b><br/>
        {tier_icon} Score: {score}/100<br/>
        📍 {stop.get('distance_miles', 'N/A')} miles<br/>
        🅿️ {stop.get('available', 'N/A')} spots available
        """
        
        folium.Marker(
            [lat, lon],
            popup=popup_html,
            icon=folium.Icon(color=color, icon="parking", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width=600, height=450)

with col_list:
    st.markdown("### 📋 Stop Results")
    st.markdown(f"**{len(stops_data)} stops found** within {radius} miles")
    st.markdown("---")
    
    for i, stop in enumerate(stops_data):
        score = stop.get("security_score", 50)
        name = stop.get("name", "Unknown")
        distance = stop.get("distance_miles", "N/A")
        available = stop.get("available", "N/A")
        
        if score >= 80:
            tier_badge = '<span style="background:#22c55e; color:white; padding:2px 8px; border-radius:10px; font-size:0.8rem;">Level 1</span>'
            score_color = "#16a34a"
        elif score >= 60:
            tier_badge = '<span style="background:#f59e0b; color:white; padding:2px 8px; border-radius:10px; font-size:0.8rem;">Level 2</span>'
            score_color = "#d97706"
        else:
            tier_badge = '<span style="background:#ef4444; color:white; padding:2px 8px; border-radius:10px; font-size:0.8rem;">Level 3</span>'
            score_color = "#dc2626"
        
        amenities_list = stop.get("amenities", ["Fuel"])
        amenity_icons = " ".join([f"✅ {a}" for a in amenities_list[:3]])
        
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>{name}</strong>
                {tier_badge}
            </div>
            <div style="display: flex; justify-content: space-between; margin: 0.5rem 0;">
                <span style="color: {score_color}; font-size: 1.8rem; font-weight: bold;">{score}/100</span>
                <div style="text-align: right; color: #666;">
                    📍 {distance} mi<br/>🅿️ {available} spots
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #666;">{amenity_icons}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.button(f"📞 Call", key=f"call_{i}", use_container_width=True)
        with col_b:
            st.button(f"🗺️ Navigate", key=f"nav_{i}", use_container_width=True)
        
        st.markdown("")

# =============================================================================
# STOP DETAILS MODAL (when selected)
# =============================================================================

st.markdown("---")
st.markdown("## 📊 Stop Details")

st.info("👆 Click on a stop above to see full details including photos, reviews, and security features.")

detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.markdown("""
    ### 🛡️ Security Features
    - ✅ **Gated Parking** - Controlled access
    - ✅ **24/7 Security Guards** - On-site patrol
    - ✅ **CCTV Monitoring** - Live cameras
    - ✅ **Well-Lit Facility** - No dark areas
    - ✅ **No Incidents** - Clean record (24+ months)
    """)

with detail_col2:
    st.markdown("""
    ### 🛠️ Amenities
    - ⛽ **Diesel Fuel** - 24/7 available
    - 🍔 **Restaurant** - Hot food, 6am-10pm
    - 🚿 **Showers** - $15, clean
    - 🧺 **Laundry** - Self-service
    - 📶 **WiFi** - Free, good signal
    - 🔧 **Truck Repair** - On-call mechanic
    """)
