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

# ======================
# 📍 Address Input
# ======================
st.subheader("Enter Start and Destination")
col1, col2 = st.columns(2)
with col1:
    start_address = st.text_input("Start Location", "Chicago, IL")
with col2:
    end_address = st.text_input("Destination", "Oak Lawn, IL")

# ======================
# 🌐 Geocode Function
# ======================
def geocode(address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(address)}.json"
    params = {"access_token": MAPBOX_TOKEN}
    res = requests.get(url, params=params)
    data = res.json()
    coords = data["features"][0]["center"]
    return coords

# ======================
# 📦 Generate Route
# ======================
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

        route_geo = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": data["routes"][0]["geometry"],
                "properties": {}
            }]
        }

        steps = data["routes"][0]["legs"][0]["steps"]
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

# ======================
# 🔘 Start Nav Button
# ======================
if os.path.exists("route.json") and os.path.exists("steps.json") and os.path.exists("info.json"):
    st.markdown("### 🧭 Navigation Controls")
    if st.button("▶️ Start Navigation"):
        st.session_state.nav_started = True
        st.experimental_rerun()

    with open("info.json") as f:
        info = json.load(f)

    st.markdown(f"""
    **Estimated Arrival Time:** 🕒 {info['eta']}  
    **Distance Remaining:** 📏 {info['distance_km']} km
    """)

# ======================
# 🗺️ Display Map + Voice Nav
# ======================
if os.path.exists("route.json") and os.path.exists("steps.json"):
    with open("route.json") as f:
        route_data = json.load(f)
    route_coords = route_data["features"][0]["geometry"]["coordinates"]
    route_coords_js = json.dumps(route_coords)

    with open("steps.json") as f:
        steps = json.load(f)
    steps_js = json.dumps([
        {
            "instruction": step["maneuver"]["instruction"],
            "location": step["maneuver"]["location"]
        } for step in steps
    ])

    nav_on = str(st.session_state.nav_started).lower()

    components.html(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Live GPS Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
  <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
  <style>
    body {{ margin: 0; padding: 0; }}
    #map {{ width: 100%; height: 600px; }}
    #next-turn {{ padding: 10px; font-size: 18px; font-weight: bold; background: #111; color: #0f0; }}
  </style>
</head>
<body>
<div id='next-turn'>Waiting to start navigation...</div>
<div id='map'></div>
<script>
  mapboxgl.accessToken = '{MAPBOX_TOKEN}';
  const map = new mapboxgl.Map({{
    container: 'map',
    style: 'mapbox://styles/mapbox/navigation-night-v1',
    center: [-87.6298, 41.8781],
    zoom: 12
  }});

  const routeCoords = {route_coords_js};
  const steps = {steps_js};
  const navStarted = {nav_on};
  let stepIndex = 0;

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

  let userMarker = null;

  function haversine(lat1, lon1, lat2, lon2) {{
    const R = 6371e3;
    const toRad = x => x * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }}

  navigator.geolocation.watchPosition(pos => {{
    const lng = pos.coords.longitude;
    const lat = pos.coords.latitude;

    if (!userMarker) {{
      userMarker = new mapboxgl.Marker({{ color: 'red' }})
        .setLngLat([lng, lat])
        .addTo(map);
    }} else {{
      userMarker.setLngLat([lng, lat]);
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
  }}, err => console.error(err), {{
    enableHighAccuracy: true,
    maximumAge: 0,
    timeout: 5000
  }});
</script>
</body>
</html>
""", height=720)
else:
    st.info("⚠️ No route yet. Enter start and destination above to begin.")
