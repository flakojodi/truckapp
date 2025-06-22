import streamlit as st
import folium
from streamlit_folium import st_folium
import openrouteservice

# OpenRouteService client
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
client = openrouteservice.Client(key=ORS_API_KEY)

st.set_page_config(page_title="SafeMap Route App", layout="centered")
st.title("🚛 Truck Route Planner (SafeMap Version)")

# Address inputs
start = st.text_input("Start Location", "Chicago, IL")
end = st.text_input("End Location", "Indianapolis, IN")

# Get coordinates
def get_coords(address):
    try:
        r = client.pelias_search(text=address)
        return r["features"][0]["geometry"]["coordinates"]
    except Exception as e:
        st.error(f"Geocoding failed: {e}")
        return None

# Get route
def get_route(start_coords, end_coords):
    try:
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile="driving-car",
            format="geojson"
        )
        return route["features"][0]["geometry"]["coordinates"]
    except Exception as e:
        st.error(f"Routing failed: {e}")
        return None

if st.button("🚀 Plot Route"):
    start_coords = get_coords(start)
    end_coords = get_coords(end)

    if not start_coords or not end_coords:
        st.warning("❌ Could not geocode one or both addresses.")
        st.stop()

    try:
        center_lat = (start_coords[1] + end_coords[1]) / 2
        center_lon = (start_coords[0] + end_coords[0]) / 2
    except Exception:
        center_lat, center_lon = 39.8283, -98.5795  # fallback center USA

    m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    # Add markers
    try:
        folium.Marker(
            [start_coords[1], start_coords[0]],
            tooltip="Start",
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.Marker(
            [end_coords[1], end_coords[0]],
            tooltip="End",
            icon=folium.Icon(color="red")
        ).add_to(m)
    except:
        st.warning("⚠️ Marker draw failed.")

    # Try drawing route
    route = get_route(start_coords, end_coords)
    if route:
        try:
            route_latlon = [[lat, lon] for lon, lat in route]
            folium.PolyLine(route_latlon, color="blue", weight=5).add_to(m)
            st.success("✅ Route added.")
        except Exception as e:
            st.warning(f"⚠️ Route draw failed: {e}")
            st.json(route)

    else:
        st.info("🔍 Route not found or skipped. Map still shown.")

    st_folium(m, width=700, height=500)
