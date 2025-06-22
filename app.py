import streamlit as st
import streamlit.components.v1 as components
import openrouteservice
import json
import os

# Set Streamlit app config
st.set_page_config(page_title="Truck Route App", layout="centered")
st.title("🚛 Truck Route Planner")

# Intro text
st.markdown("""
Use this tool to:
- Plan truck-safe routes
- Avoid low bridges and weight limits
- Track your live GPS location
""")

# GPS Map Embed (served locally from /public folder)
st.markdown("### 📍 Real-Time GPS Tracker")
components.iframe("public/gps.html", height=600, scrolling=True)

# Route Planner
st.markdown("### 🧭 Truck-Safe Route Planner")
start = st.text_input("Start location (e.g. Chicago, IL)")
end = st.text_input("Destination (e.g. Indianapolis, IN)")
route_btn = st.button("Calculate Route")

if route_btn and start and end:
    try:
        # Connect to OpenRouteService
        client = openrouteservice.Client(
            key="5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
        )

        # Geocode start and end
        geocode_start = client.pelias_search(text=start)['features'][0]['geometry']['coordinates']
        geocode_end = client.pelias_search(text=end)['features'][0]['geometry']['coordinates']

        # Get truck-safe route (HGV)
        route = client.directions(
            coordinates=[geocode_start, geocode_end],
            profile='driving-hgv',
            format='geojson'
        )

        st.success("✅ Route calculated!")

        # Display summary
        distance = route['features'][0]['properties']['summary']['distance'] / 1000
        duration = route['features'][0]['properties']['summary']['duration'] / 60
        st.markdown(f"**Distance:** {distance:.1f} km")
        st.markdown(f"**Estimated Duration:** {duration:.1f} minutes")

        # Save route coordinates to public/route.json
        coords = route['features'][0]['geometry']['coordinates']
        route_path = os.path.join("public", "route.json")
        with open(route_path, "w") as f:
            json.dump(coords, f)

        st.success("📍 Route saved — now visible on map!")

    except Exception as e:
        st.error("❌ Error calculating route. Check input or try again.")
        st.exception(e)
