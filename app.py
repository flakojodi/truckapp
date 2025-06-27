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
    start = st.text_input("", key="start", label_visibility="collapsed")
    st.session_state.start_address = start
    truck_height = float(st.text_input("Truck Height (in feet)", "13.5"))
with col2:
    st.markdown("**Destination**")
    end = st.text_input("", key="end", label_visibility="collapsed")
    st.session_state.end_address = end
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
