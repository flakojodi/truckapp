import streamlit as st
import streamlit.components.v1 as components
import requests
import openrouteservice
from openrouteservice import convert

# Config
st.set_page_config(page_title="Truck Route App", layout="centered")
st.title("🚛 Truck Route Planner")

st.markdown("""
Use this tool to:
- Plan truck-safe routes
- Avoid low bridges and weight limits
- Track your live GPS location
""")

# Embedded live GPS map
st.markdown("### 📍 Real-Time GPS Tracker (Live)")
components.iframe("https://flakojodi.github.io/truckapp/gps.html", height=600, scrolling=True)

# Routing form
st.markdown("### 🧭 Truck-Safe Route Planner")
start = st.text_input("Start location (e.g. Chicago, IL)")
end = st.text_input("Destination (e.g. Indianapolis, IN)")
route_btn = st.button("Calculate Route")

if route_btn and start and end:
    try:
        client = openrouteservice.Client(key="5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace")  # Free key

        geocode_start = client.pelias_search(text=start)['features'][0]['geometry']['coordinates']
        geocode_end = client.pelias_search(text=end)['features'][0]['geometry']['coordinates']

        route = client.directions(
            coordinates=[geocode_start, geocode_end],
            profile='driving-hgv',  # HGV = truck-safe profile
            format='geojson'
        )

        st.success("✅ Route calculated!")
        st.markdown(f"**Distance:** {route['features'][0]['properties']['summary']['distance'] / 1000:.1f} km")
        st.markdown(f"**Estimated Duration:** {route['features'][0]['properties']['summary']['duration'] / 60:.1f} minutes")

        st.markdown("📍 **Coordinates:**")
        coords = route['features'][0]['geometry']['coordinates']
        st.code(str(coords))

    except Exception as e:
        st.error("❌ Failed to calculate route. Please check city names or try again.")
        st.exception(e)
