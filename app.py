import streamlit as st
import streamlit.components.v1 as components
import openrouteservice
import json

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

# Initialize route data
route_coords = None

# Route form
st.markdown("### 🛣️ Truck-Safe Route Planner")
start = st.text_input("Start location (e.g. Chicago, IL)")
end = st.text_input("Destination (e.g. Indianapolis, IN)")
route_btn = st.button("Calculate Route")

if route_btn and start and end:
    try:
        client = openrouteservice.Client(
            key="5b3ce3597851110001cf624888df041edc1b46f495f01545515f1ace"
        )
        geocode_start = client.pelias_search(text=start)['features'][0]['geometry']['coordinates']
        geocode_end = client.pelias_search(text=end)['features'][0]['geometry']['coordinates']

        route = client.directions(
            coordinates=[geocode_start, geocode_end],
            profile='driving-hgv',
            format='geojson'
        )

        st.success("✅ Route calculated successfully!")
        distance = route['features'][0]['properties']['summary']['distance'] / 1000
        duration = route['features'][0]['properties']['summary']['duration'] / 60
        st.markdown(f"**Distance:** {distance:.1f} km")
        st.markdown(f"**Estimated Duration:** {duration:.1f} minutes")

        route_coords = route['features'][0]['geometry']['coordinates']

    except Exception as e:
        st.error("❌ Failed to calculate route.")
        st.exception(e)

# Load HTML and inject JS route block
with open("public/gps.html", "r", encoding="utf-8") as f:
    html_template = f.read()

# Replace placeholder with real JS route variable
if route_coords:
    route_json = json.dumps(route_coords)
    injected = f"<script>const routeData = {route_json};</script>"
else:
    injected = "<script>const routeData = null;</script>"

html_final = html_template.replace("<!-- __ROUTE_DATA_PLACEHOLDER__ -->", injected)
components.html(html_final, height=600, scrolling=False)
