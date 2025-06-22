import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# ✅ OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"

client = openrouteservice.Client(key=ORS_API_KEY)

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

st.sidebar.header("Vehicle Specs (Optional)")
st.sidebar.number_input("Height (ft)", value=13.6)
st.sidebar.number_input("Width (ft)", value=8.5)
st.sidebar.number_input("Length (ft)", value=53.0)
st.sidebar.number_input("Weight (lbs)", value=80000.0)

st.header("📍 Enter Route")
start = st.text_input("Start Address", "Chicago, IL")
end = st.text_input("Destination Address", "Indianapolis, IN")

# Geocode
def get_coords(address):
    try:
        geo = client.pelias_search(text=address)
        coords = geo["features"][0]["geometry"]["coordinates"]
        return coords
    except Exception as e:
        st.error(f"Geocoding failed for '{address}': {e}")
        return None

# Routing
def get_route(start, end):
    try:
        route = client.directions(
            coordinates=[start, end],
            profile="driving-car",
            format="geojson"
        )
        return route
    except Exception as e:
        st.error(f"Routing failed: {e}")
        return None

if st.button("Generate Route"):
    if not start or not end:
        st.warning("Enter both addresses.")
        st.stop()

    start_coords = get_coords(start)
    end_coords = get_coords(end)

    if not start_coords or not end_coords:
        st.warning("Could not find coordinates.")
        st.stop()

    route = get_route(start_coords, end_coords)

    if not route:
        st.warning("Route could not be retrieved.")
        st.stop()

    coords = route["features"][0]["geometry"]["coordinates"]
    latlon_route = [[lat, lon] for lon, lat in coords]

    center_lat = (start_coords[1] + end_coords[1]) / 2
    center_lon = (start_coords[0] + end_coords[0]) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)
    folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([end_coords[1], end_coords[0]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(latlon_route, color="blue", weight=5, opacity=0.8).add_to(m)

    st.success("✅ Route loaded!")
    st_folium(m, width=700, height=500)
