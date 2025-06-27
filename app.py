import streamlit as st
import requests
import json
import urllib.parse
import streamlit.components.v1 as components
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🚛 Truck-Safe GPS Navigation")

MAPBOX_TOKEN = "pk.eyJ1IjoiZmxha29qb2RpIiwiYSI6ImNtYzlrNW5iZzE1YmoydW9ldnZmNTZpdnkifQ.GgxPKZLKgt0DJ5L9ggYP9A"

if "start_address" not in st.session_state:
    st.session_state.start_address = ""
if "end_address" not in st.session_state:
    st.session_state.end_address = ""

# Custom autocomplete UI using JS
st.components.v1.html(f"""
<script>
window.addEventListener("message", (event) => {{
    if (event.data.type === "start_selected") {{
        window.parent.postMessage({{type: "streamlit:setComponentValue", value: {{ start: event.data.value }} }}, "*");
    }}
    if (event.data.type === "end_selected") {{
        window.parent.postMessage({{type: "streamlit:setComponentValue", value: {{ end: event.data.value }} }}, "*");
    }}
}});
</script>
""", height=0)

st.subheader("Enter Route and Truck Info")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Start Location**")
    components.html(f"""
    <input id='startInput' placeholder='Type start location...' style='width:100%;padding:10px;font-size:16px;'>
    <div id='startResults' style='border:1px solid #ccc;max-height:150px;overflow-y:auto;background:white;'></div>
    <script>
    const startInput = document.getElementById('startInput');
    const startResults = document.getElementById('startResults');
    startInput.addEventListener('input', async () => {{
        const val = startInput.value;
        if (val.length < 3) return startResults.innerHTML = "";
        const res = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${{encodeURIComponent(val)}}.json?access_token={MAPBOX_TOKEN}`);
        const data = await res.json();
        startResults.innerHTML = data.features.map(f => `<div onclick='selectStart("${{f.place_name.replace(/"/g, "&quot;")}}")' style='padding:8px;border-bottom:1px solid #eee;cursor:pointer;'>📍 ${{f.place_name}}</div>`).join('');
    }});
    function selectStart(place) {{
        startInput.value = place;
        startResults.innerHTML = "";
        window.parent.postMessage({{type: 'start_selected', value: place}}, '*');
    }}
    </script>
    """, height=200)
    truck_height = float(st.text_input("Truck Height (feet)", "13.5"))

with col2:
    st.markdown("**Destination**")
    components.html(f"""
    <input id='endInput' placeholder='Type destination...' style='width:100%;padding:10px;font-size:16px;'>
    <div id='endResults' style='border:1px solid #ccc;max-height:150px;overflow-y:auto;background:white;'></div>
    <script>
    const endInput = document.getElementById('endInput');
    const endResults = document.getElementById('endResults');
    endInput.addEventListener('input', async () => {{
        const val = endInput.value;
        if (val.length < 3) return endResults.innerHTML = "";
        const res = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${{encodeURIComponent(val)}}.json?access_token={MAPBOX_TOKEN}`);
        const data = await res.json();
        endResults.innerHTML = data.features.map(f => `<div onclick='selectEnd("${{f.place_name.replace(/"/g, "&quot;")}}")' style='padding:8px;border-bottom:1px solid #eee;cursor:pointer;'>📍 ${{f.place_name}}</div>`).join('');
    }});
    function selectEnd(place) {{
        endInput.value = place;
        endResults.innerHTML = "";
        window.parent.postMessage({{type: 'end_selected', value: place}}, '*');
    }}
    </script>
    """, height=200)
    truck_weight = st.text_input("Truck Weight (tons)", "20")

# ==========================
# Geocode + Safety Check
# ==========================
def geocode(address):
    res = requests.get(f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(address)}.json",
                       params={"access_token": MAPBOX_TOKEN})
    return res.json()["features"][0]["center"]

def is_route_safe(steps, max_height):
    low_bridges = [
        {"location": [-87.6244, 41.8808], "clearance_ft": 12.5},
        {"location": [-87.6354, 41.8757], "clearance_ft": 13.0},
    ]
    for step in steps:
        lng, lat = step["maneuver"]["location"]
        for bridge in low_bridges:
            dist = ((lng - bridge["location"][0])**2 + (lat - bridge["location"][1])**2)**0.5
            if dist < 0.005 and bridge["clearance_ft"] < max_height:
                return False
    return True

# ==========================
# Route Generation
# ==========================
start = st.session_state.get("start_address")
end = st.session_state.get("end_address")

if start and end:
    try:
        start_coords = geocode(start)
        end_coords = geocode(end)

        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        params = {
            "access_token": MAPBOX_TOKEN,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true"
        }
        res = requests.get(url, params=params)
        data = res.json()

        steps = data["routes"][0]["legs"][0]["steps"]
        geometry = data["routes"][0]["geometry"]

        if not is_route_safe(steps, truck_height):
            st.error("🚫 Route includes a low-clearance bridge for your truck height!")
        else:
            st.success("✅ Route is truck-safe. Preview below:")
            route_geo = {
                "type": "FeatureCollection",
                "features": [{"type": "Feature", "geometry": geometry, "properties": {}}]
            }
            components.html(f"""
            <div id='map' style='height: 600px;'></div>
            <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
            <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
            <script>
            mapboxgl.accessToken = '{MAPBOX_TOKEN}';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/navigation-night-v1',
                center: [{start_coords[0]}, {start_coords[1]}],
                zoom: 12
            }});
            map.on('load', () => {{
                map.addSource('route', {{ type: 'geojson', data: {json.dumps(route_geo)} }});
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
            </script>
            """, height=620)
    except Exception as e:
        st.error(f"❌ Error generating route: {e}")
