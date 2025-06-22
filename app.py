import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# Your OpenRouteService API key
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
client = openrouteservice.Client(key=ORS_API_KEY)

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

# Sidebar truck specs (optional)
st.sidebar.header("Vehicle Specs")
st.sidebar.number_input("Height (ft)", value=13.6)
st.sidebar.number_input("Width (ft)", value=8.5)
st.sidebar.number_input("Length (ft)", value=53.0)
st.sidebar.number_input("Weight (lbs)", value=80000.0)

st.header("📍 Enter Route")
start = st.text_input("Start Address", "Chicago, IL")
end = st.text_input("Destination Address", "Indianapolis, IN")

def geocode(address):
    try:
        response = client.pelias_search(text=address)
        coords = response['features'][0]['geometry']['coordinates']
        return coords  # [lon, lat]
    except Exception as e:
        st.error(f"Geocoding error for '{address}': {e}")
        return None

def get_route(start_coords, end_coords):
    try:
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
        return route['features'][0]['geometry']['coordinates']
    except Exception as e:
        st.error(f"Routing error: {e}")
        return None

if st.button("Generate Route"):
    start_coords = geocode(start)
    end_coords = geocode(end)

    if not start_coords or not end_coords:
        st.warning("❌ Invalid address. Try a bigger city or fix typos.")
        st.stop()

    route_coords = get_route(start_coords, end_coords)

    if not route_coords:
        st.warning("❌ Could not generate a route. Try nearby cities.")
        st.stop()

    # Flip [lon, lat] → [lat, lon] for folium
    route_latlon = [[coord[1], coord[0]] for coord in route_coords]

    center_lat = (start_coords[1] + end_coords[1]) / 2
    center_lon = (start_coords[0] + end_coords[0]) / 2

    try:
        m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

        folium.Marker([start_coords[1], start_coords[0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([end_coords[1], end_coords[0]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)

        folium.PolyLine(route_latlon, color="blue", weight=5, opacity=0.8).add_to(m)

        st.success("✅ Route successfully loaded!")
        st_folium(m, width=700, height=500)

    except Exception as e:
        st.error(f"❌ Map rendering error: {e}")
        st.write("Here are the coordinates for manual debug:")
        st.json(route_latlon)
        fallback = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
        st_folium(fallback, width=700, height=500)
