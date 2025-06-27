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
    st.markdown("**Start Location**")
    components.html(f"""
    <input id='startInput' placeholder='Enter start location...' style='width:100%;padding:10px;font-size:16px;'>
    <div id='startResults' style='border:1px solid #ccc;max-height:150px;overflow-y:auto;background:white;position:relative;z-index:1000;'></div>
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
        const hiddenInput = window.parent.document.querySelector('[name="start_hidden"]');
        if (hiddenInput) {{ hiddenInput.value = place; hiddenInput.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
    }}
    </script>
    <input type='hidden' name='start_hidden'>
    """, height=250)
    truck_height = float(st.text_input("Truck Height (in feet)", "13.5"))

with col2:
    st.markdown("**Destination**")
    components.html(f"""
    <input id='endInput' placeholder='Enter destination...' style='width:100%;padding:10px;font-size:16px;'>
    <div id='endResults' style='border:1px solid #ccc;max-height:150px;overflow-y:auto;background:white;position:relative;z-index:1000;'></div>
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
        const hiddenInput = window.parent.document.querySelector('[name="end_hidden"]');
        if (hiddenInput) {{ hiddenInput.value = place; hiddenInput.dispatchEvent(new Event('input', {{ bubbles: true }})); }}
    }}
    </script>
    <input type='hidden' name='end_hidden'>
    """, height=250)
    truck_weight = st.text_input("Truck Weight (in tons)", "20")

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
# 📦 Generate Route Automatically
# ==========================
start = st.session_state.start_address
end = st.session_state.end_address

if start and end:
    st.write("📍 Start Address:", start)
st.write("🏁 End Address:", end)
try:
        st.write("📍 Start Address:", start)
        st.write("🏁 End Address:", end)

        res = requests.get(directions_url, params=params)
        st.write("🛰️ Mapbox Directions API Response:", res.status_code)
        st.write(res.json())
st.write("🛰️ Mapbox Directions API Response:", res.status_code)
st.write(res.json())
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

            duration_sec = data["routes"][0]["duration"]
            distance_meters = data["routes"][0]["distance"]
            eta_time = datetime.utcnow() + timedelta(seconds=duration_sec)

            with open("route.json", "w") as f:
                json.dump(route_geo, f)
            with open("steps.json", "w") as f:
                json.dump(steps, f)
            with open("info.json", "w") as f:
                json.dump({
                    "eta": eta_time.strftime("%I:%M %p"),
                    "distance_km": round(distance_meters / 1000, 1)
                }, f)

            st.session_state.nav_started = False
            st.success("✅ Route created! Scroll down to begin.")

            # 🗺️ Render Map
            components.html(f"""
            <div id='map' style='height: 600px;'></div>
            <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
            <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
            <script>
            mapboxgl.accessToken = '{MAPBOX_TOKEN}';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v11',
                center: [{start_coords[0]}, {start_coords[1]}],
                zoom: 13
            }});
            map.on('load', () => {{
                map.addSource('route', {{
                    type: 'geojson',
                    data: {json.dumps(route_geo)}
                }});
                map.addLayer({{
                    id: 'route-line',
                    type: 'line',
                    source: 'route',
                    layout: {{ 'line-join': 'round', 'line-cap': 'round' }},
                    paint: {{ 'line-color': '#00FF99', 'line-width': 5 }}
                }});
                new mapboxgl.Marker().setLngLat([{start_coords[0]}, {start_coords[1]}]).addTo(map);
                new mapboxgl.Marker({{ color: 'red' }}).setLngLat([{end_coords[0]}, {end_coords[1]}]).addTo(map);
            }});
            </script>
            """, height=620)

    except Exception as e:
        st.exception(e)
