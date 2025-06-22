import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

# Sidebar: Truck specs
st.sidebar.header("Vehicle Specs")
height = st.sidebar.number_input("Height (ft)", value=13.6)
width = st.sidebar.number_input("Width (ft)", value=8.5)
length = st.sidebar.number_input("Length (ft)", value=53.0)
weight = st.sidebar.number_input("Weight (lbs)", value=80000.0)

# Address input
st.header("🗺️ Route Info")
start = st.text_input("Starting Address", placeholder="e.g. Chicago, IL")
end = st.text_input("Destination Address", placeholder="e.g. Indianapolis, IN")

# Geocoding with OpenRouteService
def geocode_address(address):
    url = f"https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": ORS_API_KEY,
        "text": address,
        "size": 1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        try:
            coords = data["features"][0]["geometry"]["coordinates"]  # [lon, lat]
            return coords
        except (KeyError, IndexError):
            return None
    return None

# Routing with OpenRouteService
def get_route(start_coords, end_coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY}
    body = {
        "coordinates": [start_coords, end_coords],
        "instructions": False
    }
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()["features"][0]["geometry"]["coordinates"]
        except (KeyError, IndexError):
            return None
    return None

# Main button
if st.button("Generate Truck Route"):
    start_coords = geocode_address(start)
    end_coords = geocode_address(end)

    if not start_coords or not end_coords:
        st.error("Could not geocode one or both addresses.")
    else:
        route_coords = get_route(start_coords, end_coords)
        if not route_coords:
            st.error("Could not retrieve route. Try different cities.")
        else:
            st.success("✅ Route generated! Scroll down to view map.")

            # Convert coordinates to [lat, lon] for folium
            route_latlon = [[lat, lon] for lon, lat in route_coords]

            # Create map centered between start and end
            mid_lat = (start_coords[1] + end_coords[1]) / 2
            mid_lon = (start_coords[0] + end_coords[0]) / 2
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)

            folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([end_coords[1], end_coords[0]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)
            folium.PolyLine(route_latlon, color="blue", weight=5).add_to(m)

            st_folium(m, width=700, height=500)
