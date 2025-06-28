import streamlit as st
import json
import requests
import os
import urllib.parse
import streamlit.components.v1 as components
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🚛 Truck-Safe GPS Navigation")

MAPBOX_TOKEN = "pk.eyJ1IjoiZmxha29qb2RpIiwiYSI6ImNtYzlrNW5iZzE1YmoydW9ldnZmNTZpdnkifQ.GgxPKZLKgt0DJ5L9ggYP9A"

if "nav_started" not in st.session_state:
    st.session_state.nav_started = False
if "start_address" not in st.session_state:
    st.session_state.start_address = ""
if "end_address" not in st.session_state:
    st.session_state.end_address = ""

st.subheader("Enter Route and Truck Info")
col1, col2 = st.columns(2)
with col1:
    truck_height = float(st.text_input("Truck Height (in feet)", "13.5"))
with col2:
    truck_weight = st.text_input("Truck Weight (in tons)", "20")

# JavaScript-enhanced Autocomplete Component
st.markdown("""
<style>
input[type="text"] {
  font-size: 16px;
  padding: 10px;
  width: 100%;
}
.suggestion {
  padding: 8px;
  border-bottom: 1px solid #ccc;
  cursor: pointer;
  background-color: #fff;
  z-index: 9999;
}
.suggestion:hover {
  background-color: #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("**Start Location**")
start_box = st.empty()
end_box = st.empty()

gps_input = st.text_input("Current GPS (for debug, optional)", key="gps_coords", label_visibility="collapsed")

start_html = f"""
<input type='text' id='startInput' placeholder='Start address...' oninput='getStartSuggestions()'>
<div id='startSuggestions'></div>
<script>
let startField = document.getElementById('startInput');
let startContainer = document.getElementById('startSuggestions');

function getStartSuggestions() {{
    let query = startField.value;
    if (query.length < 3) {{ startContainer.innerHTML = ''; return; }}
    fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${{query}}.json?access_token={MAPBOX_TOKEN}`)
      .then(res => res.json())
      .then(data => {{
        startContainer.innerHTML = data.features.map(f => `<div class='suggestion' onclick='selectStart("${{f.place_name}}")'>📍 ${{f.place_name}}</div>`).join('');
      }});
}}

function selectStart(val) {{
    window.parent.postMessage({{ isStreamlitMessage: true, type: "start", value: val }}, "*");
    startField.value = val;
    startContainer.innerHTML = "";
}}
</script>
"""

end_html = f"""
<input type='text' id='endInput' placeholder='End address...' oninput='getEndSuggestions()'>
<div id='endSuggestions'></div>
<script>
let endField = document.getElementById('endInput');
let endContainer = document.getElementById('endSuggestions');

function getEndSuggestions() {{
    let query = endField.value;
    if (query.length < 3) {{ endContainer.innerHTML = ''; return; }}
    fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${{query}}.json?access_token={MAPBOX_TOKEN}`)
      .then(res => res.json())
      .then(data => {{
        endContainer.innerHTML = data.features.map(f => `<div class='suggestion' onclick='selectEnd("${{f.place_name}}")'>📍 ${{f.place_name}}</div>`).join('');
      }});
}}

function selectEnd(val) {{
    window.parent.postMessage({{ isStreamlitMessage: true, type: "end", value: val }}, "*");
    endField.value = val;
    endContainer.innerHTML = "";
}}
</script>
"""

start_box.components.v1.html(start_html, height=220)
end_box.components.v1.html(end_html, height=220)

# Handle JS inputs from iframe
st_js_listener = components.html("""
<script>
window.addEventListener("message", event => {
  if (event.data.type === "start") {{
    window.parent.postMessage({ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {{ key: "start_address", value: event.data.value }} }, "*");
  }}
  if (event.data.type === "end") {{
    window.parent.postMessage({ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {{ key: "end_address", value: event.data.value }} }, "*");
  }}
});
</script>
""", height=0)

# ==========================
# 🌐 Geocode Function
# ==========================
def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(address)}.json"
    params = {"access_token": MAPBOX_TOKEN}
    res = requests.get(url, params=params)
    data = res.json()
    coords = data["features"][0]["center"]
    return coords

# ==========================
# 🚧 Simulated Bridge Height Check
# ==========================
def is_route_safe(steps, max_height_ft):
    low_bridges = [
        {"location": [-87.6244, 41.8808], "clearance_ft": 12.5},
        {"location": [-87.6354, 41.8757], "clearance_ft": 13.0}
    ]
    for step in steps:
        lng, lat = step["maneuver"]["location"]
        for bridge in low_bridges:
            dist = ((lng - bridge["location"][0])**2 + (lat - bridge["location"][1])**2)**0.5
            if dist < 0.005 and bridge["clearance_ft"] < max_height_ft:
                return False
    return True

# ==========================
# 📦 Generate Route
# ==========================
start = st.session_state.get("start_address", "")
end = st.session_state.get("end_address", "")

if st.button("🚚 Get Directions") and start and end:
    try:
        start_coords = geocode(start)
        end_coords = geocode(end)

        directions_url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        params = {
            "alternatives": "false",
            "geometries": "geojson",
            "steps": "true",
            "overview": "full",
            "access_token": MAPBOX_TOKEN
        }
        res = requests.get(directions_url, params=params)
        data = res.json()
        steps = data["routes"][0]["legs"][0]["steps"]

        if not is_route_safe(steps, truck_height):
            st.error("🚫 Route includes a low-clearance bridge for your truck height!")
        else:
            route_geo = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": data["routes"][0]["geometry"],
                    "properties": {}
                }]
            }
            with open("route.json", "w") as f:
                json.dump(route_geo, f)
            with open("steps.json", "w") as f:
                json.dump(steps, f)

            st.success("✅ Route generated! Map below:")

            st.map({"type": "scattermapbox", "coordinates": [start_coords, end_coords]})
    except Exception as e:
        st.error(f"Error: {e}")
