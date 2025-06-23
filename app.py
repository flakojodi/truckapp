import streamlit as st
import json
import requests
import os
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🚛 Truck-Safe GPS Navigation")

# =========================
# 🔐 CONFIG
# =========================
MAPBOX_TOKEN = "pk.eyJ1IjoiZmxha29qb2RpIiwiYSI6ImNtYzlrNW5iZzE1YmoydW9ldnZmNTZpdnkifQ.GgxPKZLKgt0DJ5L9ggYP9A"

# Chicago to Oak Lawn sample route
start = (-87.6298, 41.8781)
end = (-87.7525, 41.7190)

# =========================
# 🚚 BUTTON: Calculate Route
# =========================
if st.button("🚚 Calculate Route"):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start[0]},{start[1]};{end[0]},{end[1]}"
    params = {
        "alternatives": "false",
        "geometries": "geojson",
        "steps": "true",
        "overview": "full",
        "access_token": MAPBOX_TOKEN
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        steps = data["routes"][0]["legs"][0]["steps"]

        # Save route line
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

        st.success("✅ Route calculated and saved!")
        st.experimental_rerun()

    else:
        st.error(f"❌ Error from Mapbox: {response.text}")

# =========================
# 🗺️ MAP DISPLAY
# =========================

route_coords_js = "[]"
has_route = False

if os.path.exists("route.json"):
    with open("route.json", "r") as f:
        route_data = json.load(f)
    route_coords = route_data["features"][0]["geometry"]["coordinates"]
    route_coords_js = json.dumps(route_coords)
    has_route = True

components.html(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Truck GPS</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js'></script>
    <link href='https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css' rel='stylesheet' />
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 600px; }}
    </style>
</head>
<body>
<div id='map'></div>
<script>
    mapboxgl.accessToken = '{MAPBOX_TOKEN}';

    const map = new mapboxgl.Map({{
        container: 'map',
        style: 'mapbox://styles/mapbox/navigation-night-v1',
        center: [-87.6298, 41.8781],
        zoom: 11
    }});

    // GPS marker
    navigator.geolocation.getCurrentPosition(pos => {{
        const userLoc = [pos.coords.longitude, pos.coords.latitude];
        new mapboxgl.Marker({{ color: 'red' }})
            .setLngLat(userLoc)
            .addTo(map);
        map.setCenter(userLoc);
    }});

    const hasRoute = {str(has_route).lower()};
    if (hasRoute) {{
        const routeCoords = {route_coords_js};
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
    }}
</script>
</body>
</html>
""", height=650)

# =========================
# 📋 TURN-BY-TURN DIRECTIONS
# =========================

if os.path.exists("steps.json"):
    st.subheader("📋 Turn-by-Turn Directions")
    with open("steps.json", "r") as f:
        steps = json.load(f)
    for i, step in enumerate(steps):
        st.markdown(f"**{i+1}.** {step['maneuver']['instruction']} ({int(step['distance'])} meters)")
else:
    st.info("📍 Click 'Calculate Route' to generate directions.")
