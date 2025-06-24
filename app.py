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
# 📍 Input Fields
# ==========================
st.subheader("Enter Route and Truck Info")
col1, col2 = st.columns(2)
with col1:
    start_address = st.text_input("Start Location", "Chicago, IL")
    truck_height = float(st.text_input("Truck Height (in feet)", "13.5"))
with col2:
    end_address = st.text_input("Destination", "Oak Lawn, IL")
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
if st.button("🚚 Generate Route"):
    try:
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

        # Check for low bridge conflict
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

# ==========================
# 🔘 Start Navigation + ETA
# ==========================
if os.path.exists("route.json") and os.path.exists("steps.json"):
    st.markdown("### 🧭 Navigation Controls")
    if st.button("▶️ Start Navigation"):
        st.session_state.nav_started = True

    if os.path.exists("info.json"):
        with open("info.json") as f:
            info = json.load(f)
        st.markdown(f"""
        **Estimated Arrival Time:** 🕒 {info['eta']}  
        **Distance Remaining:** 📏 {info['distance_km']} km
        """)
# ==========================
# 🗺️ Render Map + GPS Features
# ==========================
if os.path.exists("route.json") and os.path.exists("steps.json"):
    with open("route.json") as f:
        route_data = json.load(f)
    with open("steps.json") as f:
        steps = json.load(f)

    route_coords_js = json.dumps(route_data["features"][0]["geometry"]["coordinates"])
    steps_js = json.dumps([
        {"instruction": s["maneuver"]["instruction"], "location": s["maneuver"]["location"]}
        for s in steps
    ])
    nav_on = "true" if st.session_state.nav_started else "false"

    components.html(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Truck GPS</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
  <link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet">
  <style>
    body {{ margin: 0; }}
    #map {{ height: 600px; }}
    #next-turn, #street-name {{
      padding: 10px; font-size: 16px; font-weight: bold;
      background: #111; color: #0f0;
    }}
  </style>
</head>
<body>
<div id="next-turn">Waiting for GPS...</div>
<div id="street-name">📍 Street: ...</div>
<div id="map"></div>
<script>
mapboxgl.accessToken = '{MAPBOX_TOKEN}';
const routeCoords = {route_coords_js};
const steps = {steps_js};
const navStarted = {nav_on};
let stepIndex = 0;
let rerouteTriggered = false;
let currentDest = steps.length > 0 ? steps[steps.length - 1].location : null;

const map = new mapboxgl.Map({{
  container: 'map',
  style: 'mapbox://styles/mapbox/navigation-night-v1',
  center: routeCoords[0],
  zoom: 14,
  pitch: 45,
  bearing: 0
}});

map.on('load', () => {{
  map.addSource('route', {{
    type: 'geojson',
    data: {{
      type: 'Feature',
      geometry: {{
        type: 'LineString',
        coordinates: routeCoords
      }}
    }}
  }});
  map.addLayer({{
    id: 'route-line',
    type: 'line',
    source: 'route',
    layout: {{
      'line-join': 'round',
      'line-cap': 'round'
    }},
    paint: {{
      'line-color': '#00FF99',
      'line-width': 5
    }}
  }});
}});

function speak(text) {{
  const msg = new SpeechSynthesisUtterance(text);
  msg.rate = 1;
  window.speechSynthesis.speak(msg);
}}

let marker = null;

function haversine(lat1, lon1, lat2, lon2) {{
  const R = 6371e3;
  const toRad = x => x * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}}

function reverseGeocode(lat, lng) {{
  fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${{lng}},${{lat}}.json?access_token={MAPBOX_TOKEN}`)
    .then(res => res.json())
    .then(data => {{
      if (data.features.length > 0) {{
        const name = data.features[0].place_name;
        document.getElementById("street-name").innerText = "📍 " + name;
      }}
    }});
}}

navigator.geolocation.watchPosition(pos => {{
  const lat = pos.coords.latitude;
  const lng = pos.coords.longitude;
  const heading = pos.coords.heading || 0;

  map.easeTo({{
    center: [lng, lat],
    bearing: heading
  }});

  reverseGeocode(lat, lng);

  if (!marker) {{
    marker = new mapboxgl.Marker({{ color: 'red' }})
      .setLngLat([lng, lat])
      .addTo(map);
  }} else {{
    marker.setLngLat([lng, lat]);
  }}

  if (navStarted && stepIndex < steps.length) {{
    const step = steps[stepIndex];
    const [stepLng, stepLat] = step.location;
    const dist = haversine(lat, lng, stepLat, stepLng);

    document.getElementById("next-turn").innerText = step.instruction;

    if (dist < 35) {{
      speak(step.instruction);
      stepIndex += 1;
      if (stepIndex >= steps.length) {{
        speak("You have arrived.");
        document.getElementById("next-turn").innerText = "✅ Arrived at destination!";
      }}
    }}
  }}

  // 🛑 Auto-Reroute if off path
  if (navStarted && stepIndex < steps.length && !rerouteTriggered) {{
    const [targetLng, targetLat] = steps[stepIndex].location;
    const offTrack = haversine(lat, lng, targetLat, targetLng) > 200;
    if (offTrack) {{
      rerouteTriggered = true;
      speak("Recalculating route...");
      window.location.reload(); // Simple reset for now
    }}
  }}
}}, err => console.error(err), {{
  enableHighAccuracy: true,
  timeout: 5000,
  maximumAge: 0
}});
</script>
</body>
</html>
""", height=700)
