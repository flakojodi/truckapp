import streamlit as st
import streamlit.components.v1 as components
import openrouteservice
import json
import os

# Set up Streamlit config
st.set_page_config(page_title="Truck Route App", layout="centered")
st.title("🚛 Truck Route Planner")

# Intro text
st.markdown("""
Use this tool to:
- 🧭 Plan truck-safe routes
- 🚧 Avoid low bridges and weight restrictions
- 📍 Track your real-time GPS location
""")

# Load and embed GPS map from gps.html
try:
    with open("public/gps.html", "r", encoding="utf-8") as f:
        gps_html = f.read()
    components.html(gps_html, height=600)
except FileNotFoundError:
    st.error("🚨 gps.html not found. Make sure it's in the 'public' folder.")

# Route input form
st.markdown("### 🛣️ Truck-Safe Route Planner")
start = st.text_input("Start location (e.g. Chicago, IL)")
end = st.text_input("Destination (e.g. Indianapolis, IN)")
route_btn = st.button("Calculate Route")

if route_btn and start and end:
    try:
        # Connect to OpenRouteService
        client = openrouteservice.Client(
            key="5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
        )

        # Geocode start and end addresses
        geocode_start = client.pelias_search(text=start)['features'][0]['geometry']['coordinates']
        geocode_end = client.pelias_search(text=end)['features'][0]['geometry']['coordinates']

        # Request truck-safe route
        route = client.directions(
            coordinates=[geocode_start, geocode_end],
            profile='driving-hgv',
            format='geojson'
        )

        # Show summary
        st.success("✅ Route calculated successfully!")
        distance = route['features'][0]['properties']['summary']['distance'] / 1000
        duration = route['features'][0]['properties']['summary']['duration'] / 60
        st.markdown(f"**Distance:** {distance:.1f} km")
        st.markdown(f"**Estimated Duration:** {duration:.1f} minutes")

        # Save route to JSON so gps.html can read it
        coords = route['features'][0]['geometry']['coordinates']
        os.makedirs("public", exist_ok=True)
        with open("public/route.json", "w", encoding="utf-8") as f:
            json.dump(coords, f)

        st.success("📍 Route saved to `route.json` — now visible on the map!")

    except Exception as e:
        st.error("❌ Failed to calculate route. Please check city names or try again.")
        st.exception(e)
