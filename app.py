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

# ==========================
# 📍 Input Fields with Autocomplete
# ==========================
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
        window.parent.postMessage({{type: 'start_selected', value: place}}, '*');
    }}
    </script>
    """, height=200)
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
        window.parent.postMessage({{type: 'end_selected', value: place}}, '*');
    }}
    </script>
    """, height=200)
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
# 📦 Generate Route
# ==========================
if True:
    try:
        start_address = st.query_params.get("start", [""])[0]
        end_address = st.query_params.get("end", [""])[0]

        if not start_address or not end_address:
            st.warning("Please enter both a start and destination address.")
        else:
            start_coords = geocode(start_address)
            end_coords = geocode(end_address)

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
    except Exception as e:
        st.error(f"❌ Error: {e}")
