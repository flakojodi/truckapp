import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests

# 🚚 Your OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner - Real Routing")

# Sidebar: Truck specs
st.sidebar.header("Vehicle Specs")
height = st.sidebar.number_input("Height (ft)", value=13.6)
width = st.sidebar.number_input("Width (ft)", value=8.5)
length = st.sidebar.number_input("Length (ft)", value=53.0)
weight = st.sidebar.number_input("Weight (lbs)", value=80000.0)

# Route inputs
st.header("🗺️ Route Info")
start = st.text_input("Starting Address", placeholder="e.g. Chicago, IL")
end = st.text_input("Destination Address", placeholder="e.g. Indianapolis, IN")

def get_coords(address):
    geolocator = Nominatim(user_agent="truck_route_app")
    location = geolocator.geocode(address)
    if location:
        return [location.longitude, location.latitude]
    return None

def get_route(start_coords, end_coords):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY}
    body = {
        "coordinates": [start_coords, end_coords],
        "instructions": False
    }
    response = requests.post(url, json=body, headers=headers)
    return response.json()

if st.button("Generate Truck Route"):
    start_coords = get_coords(start)
    end_coords = get_coords(end)

    if not start_coords or not end_coords:
        st.error("Could not geocode one or both addresses.")
    else:
        st.success("Route calculated! Scroll down to see the map.")

        route_data = get_route(start_coords, end_coords)
        coords = route_data['features'][0]['geometry']['coordinates']

        m = folium.Map(location=[(start_coords[1] + end_coords[1]) / 2,
                                 (start_coords[0] + end_coords[0]) / 2],
                       zoom_start=7)

        folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker([end_coords[1], end_coords[0]], tooltip="End", icon=folium.Icon(color='red')).add_to(m)

        route_coords = [[lat, lon] for lon, lat in coords]
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        st_folium(m, width=700, height=500)
