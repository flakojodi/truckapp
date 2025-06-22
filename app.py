import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# ✅ OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

st.sidebar.header("Vehicle Specs (Optional)")
st.sidebar.number_input("Height (ft)", value=13.6)
st.sidebar.number_input("Width (ft)", value=8.5)
st.sidebar.number_input("Length (ft)", value=53.0)
st.sidebar.number_input("Weight (lbs)", value=80000.0)

st.header("📍 Enter Start & Destination")
start_address = st.text_input("Start Address", placeholder="e.g. Chicago, IL")
end_address = st.text_input("Destination Address", placeholder="e.g. Indianapolis, IN")

# 🔹 Get coordinates from OpenRouteService Geocoding
def get_coords(address):
    try:
        geo_url = "https://api.openrouteservice.org/geocode/search"
        params = {"api_key": ORS_API_KEY, "text": address, "size": 1}
        res = requests.get(geo_url, params=params)
        res.raise_for_status()
        features = res.json().get("features")
        if features:
            return features[0]["geometry"]["coordinates"]  # [lon, lat]
    except Exception as e:
        st.warning(f"Geocoding failed for '{address}': {e}")
    return None

# 🔹 Get route from OpenRouteService
def get_route(start, end):
    try:
        route_url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {"Authorization": ORS_API_KEY}
        body = {"coordinates": [start, end], "instructions": False}
        res = requests.post(route_url, json=body, headers=headers)
        res.raise_for_status()
        return res.json()["features"][0]["geometry"]["coordinates"]
    except Exception as e:
        st.warning(f"Routing failed: {e}")
        st.json(res.json())
    return None

if st.button("🛣️ Generate Route"):
    if not start_address or not end_address:
        st.warning("Please enter both addresses.")
        st.stop()

    start_coords = get_coords(start_address)
    end_coords = get_coords(end_address)

    if not start_coords or not end_coords:
        st.error("❌ Could not find one or both locations. Try more specific cities.")
        st.stop()

    route_coords = get_route(start_coords, end_coords)

    if not route_coords:
        st.error("❌ Route could not be retrieved. Scroll up to view error log.")
        st.stop()

    # Flip coordinates for folium
    latlon_route = [[lat, lon] for lon, lat in route_coords]

    center_lat = (start_coords[1] + end_coords[1]) / 2
    center_lon = (start_coords[0] + end_coords[0]) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([end_coords[1], end_coords[0]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(latlon_route, color="blue", weight=5, opacity=0.8).add_to(m)

    st.success("✅ Route generated below:")
    st_folium(m, width=700, height=500)
