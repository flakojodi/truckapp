import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# 💡 Your OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"

# Page setup
st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

# Sidebar truck info
st.sidebar.header("Vehicle Specs")
st.sidebar.number_input("Height (ft)", value=13.6)
st.sidebar.number_input("Width (ft)", value=8.5)
st.sidebar.number_input("Length (ft)", value=53.0)
st.sidebar.number_input("Weight (lbs)", value=80000.0)

# Location input
st.header("📍 Enter Route Details")
start_address = st.text_input("Start Address", placeholder="e.g. Chicago, IL")
end_address = st.text_input("Destination Address", placeholder="e.g. Indianapolis, IN")

# Geocode function using ORS
def get_coords(address):
    url = f"https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": ORS_API_KEY,
        "text": address,
        "size": 1
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        features = r.json().get("features")
        if features:
            return features[0]["geometry"]["coordinates"]  # [lon, lat]
    return None

# Route function using ORS
def get_route(start, end):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY}
    body = {
        "coordinates": [start, end],
        "instructions": False
    }
    r = requests.post(url, json=body, headers=headers)
    if r.status_code == 200:
        try:
            return r.json()["features"][0]["geometry"]["coordinates"]
        except:
            return None
    return None

# Main action
if st.button("Generate Route"):
    start_coords = get_coords(start_address)
    end_coords = get_coords(end_address)

    if not start_coords or not end_coords:
        st.error("Could not geocode one or both addresses. Try again.")
    else:
        route = get_route(start_coords, end_coords)

        if not route:
            st.error("Routing failed. Try more specific or nearby cities.")
        else:
            st.success("✅ Route found!")

            # Convert to [lat, lon] for folium
            route_latlon = [[coord[1], coord[0]] for coord in route]

            # Center map
            center_lat = (start_coords[1] + end_coords[1]) / 2
            center_lon = (start_coords[0] + end_coords[0]) / 2

            # Create map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
            folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([end_coords[1], end_coords[0]], tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)
            folium.PolyLine(route_latlon, color="blue", weight=4).add_to(m)

            st_folium(m, width=700, height=500)
