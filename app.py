import streamlit as st
import openrouteservice
import pandas as pd

# ORS key + client
ORS_API_KEY = "5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
client = openrouteservice.Client(key=ORS_API_KEY)

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner")

start = st.text_input("Start Address", "Chicago, IL")
end = st.text_input("End Address", "Indianapolis, IN")

def geocode(address):
    try:
        res = client.pelias_search(text=address)
        coords = res["features"][0]["geometry"]["coordinates"]
        return coords  # [lon, lat]
    except Exception as e:
        st.error(f"Geocoding failed: {e}")
        return None

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

if st.button("🛣️ Generate Safe Preview"):
    start_coords = geocode(start)
    end_coords = geocode(end)

    if not start_coords or not end_coords:
        st.error("❌ One or both locations could not be found.")
        st.stop()

    route = get_route(start_coords, end_coords)

    if not route:
        st.error("❌ Could not generate route.")
        st.stop()

    # Display only a sample of route points for safety
    coords_df = pd.DataFrame(
        [[coord[1], coord[0]] for coord in route[::50]],  # Every 50th point to reduce load
        columns=["lat", "lon"]
    )

    st.success("✅ Route preview loaded (simplified).")
    st.map(coords_df)

    # Optional: let user download the raw coords
    if st.checkbox("Show raw route data"):
        st.write("Full Route Coordinates (raw):")
        st.json(route)
