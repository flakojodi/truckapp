import streamlit as st
import json
import requests
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

start_html = f"""
<h4>Start Location</h4>
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
    window.parent.postMessage({{ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {{ key: "start_address", value: val }} }}, "*");
    startField.value = val;
    startContainer.innerHTML = "";
}}
</script>
"""

end_html = f"""
<h4>Destination</h4>
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
    window.parent.postMessage({{ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {{ key: "end_address", value: val }} }}, "*");
    endField.value = val;
    endContainer.innerHTML = "";
}}
</script>
"""

components.html(start_html, height=240)
components.html(end_html, height=240)
components.html("""
<script>
window.addEventListener("message", event => {
  if (event.data.type === "start") {
    window.parent.postMessage({ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: { key: "start_address", value: event.data.value } }, "*");
  }
  if (event.data.type === "end") {
    window.parent.postMessage({ isStreamlitMessage: true, type: "streamlit:setComponentValue", value: { key: "end_address", value: event.data.value } }, "*");
  }
});
</script>
""", height=0)

def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(address)}.json"
    params = {"access_token": MAPBOX_TOKEN}
    res = requests.get(url, params=params)
    data = res.json()
    coords = data["features"][0]["center"]
    return coords

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
            route_geo = json.dumps({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": data["routes"][0]["geometry"],
                    "properties": {}
                }]
            })
            st.success("✅ Route is safe. Preview below:")

            map_html = f"""
            <div id='map' style='height: 600px;'></div>
            <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
            <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
            <script>
            window.onload = function () {{
              setTimeout(function() {{
                mapboxgl.accessToken = '{MAPBOX_TOKEN}';
                const map = new mapboxgl.Map({{
                  container: 'map',
                  style: 'mapbox://styles/mapbox/navigation-night-v1',
                  center: [{start_coords[0]}, {start_coords[1]}],
                  zoom: 13
                }});
                map.on('load', function () {{
                  map.addSource('route', {{ type: 'geojson', data: {route_geo} }});
                  map.addLayer({{
                    id: 'route-line',
                    type: 'line',
                    source: 'route',
                    layout: {{ 'line-join': 'round', 'line-cap': 'round' }},
                    paint: {{ 'line-color': '#00FF99', 'line-width': 6 }}
                  }});
                  new mapboxgl.Marker().setLngLat([{start_coords[0]}, {start_coords[1]}]).addTo(map);
                  new mapboxgl.Marker({{ color: 'red' }}).setLngLat([{end_coords[0]}, {end_coords[1]}]).addTo(map);
                }});
              }}, 500);
            }};
            </script>
            """
            components.html(map_html, height=640)

    except Exception as e:
        st.error(f"Error: {e}")
