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
if "current_coords" not in st.session_state:
    st.session_state.current_coords = None

st.subheader("Enter Route and Truck Info")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Start Location**")
    use_gps = st.checkbox("📡 Use My Current Location")
    if use_gps:
        components.html("""
        <script>
        navigator.geolocation.getCurrentPosition(function(position) {
            const coords = position.coords.latitude + "," + position.coords.longitude;
            const input = window.parent.document.querySelector('[name="gps_coords"]');
            if (input) {
                input.value = coords;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        </script>
        <input type="hidden" name="gps_coords">
        """, height=0)
        gps_input = st.text_input("", key="gps_coords", label_visibility="collapsed")
        if gps_input:
            lat, lon = map(float, gps_input.split(","))
            geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json?access_token={MAPBOX_TOKEN}"
            res = requests.get(geocode_url)
            place = res.json()["features"][0]["place_name"]
            st.session_state.start_address = place
    else:
        start_input = st.text_input("Type to search start location", key="start")
        if start_input:
            st.session_state.start_address = start_input
            suggestions = requests.get(f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(start_input)}.json?access_token={MAPBOX_TOKEN}").json()
            if suggestions.get("features"):
                for feature in suggestions["features"][:5]:
                    if st.button("📍 " + feature["place_name"], key=feature["id"]):
                        st.session_state.start_address = feature["place_name"]
    truck_height = float(st.text_input("Truck Height (in feet)", "13.5"))

with col2:
    st.markdown("**Destination**")
    end_input = st.text_input("Type to search destination", key="end")
    if end_input:
        st.session_state.end_address = end_input
        suggestions = requests.get(f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(end_input)}.json?access_token={MAPBOX_TOKEN}").json()
        if suggestions.get("features"):
            for feature in suggestions["features"][:5]:
                if st.button("📍 " + feature["place_name"], key=feature["id"]):
                    st.session_state.end_address = feature["place_name"]
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
# 📦 Generate Route Automatically + Show Map
# ==========================
if st.session_state.start_address and st.session_state.end_address:
    try:
        start_coords = geocode(st.session_state.start_address)
        end_coords = geocode(st.session_state.end_address)

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
            st.success("✅ Safe route found! Preview below:")
            route_geojson = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {}
                }]
            }

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
                zoom: 12
            }});
            map.on('load', () => {{
                map.addSource('route', {{
                    type: 'geojson',
                    data: {json.dumps(route_geojson)}
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
        st.error(f"❌ Error: {e}")
