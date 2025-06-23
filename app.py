import streamlit as st
import json
import os
import streamlit.components.v1 as components

st.title("Truck-Safe GPS Route Map")

# Only show map if route.json exists
if os.path.exists("route.json"):
    with open("route.json", "r") as f:
        route_data = json.load(f)

    route_coords = route_data["features"][0]["geometry"]["coordinates"]
    route_coords_js = json.dumps(route_coords)

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Truck GPS Map</title>
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
        mapboxgl.accessToken = 'pk.eyJ1IjoiZmxha29qb2RpIiwiYSI6ImNtYzlrNW5iZzE1YmoydW9ldnZmNTZpdnkifQ.GgxPKZLKgt0DJ5L9ggYP9A';

        const map = new mapboxgl.Map({{
            container: 'map',
            style: 'mapbox://styles/mapbox/streets-v11',
            center: {route_coords_js}[0],
            zoom: 12
        }});

        map.on('load', () => {{
            // GPS marker
            navigator.geolocation.getCurrentPosition(pos => {{
                new mapboxgl.Marker({{color: "red"}})
                    .setLngLat([pos.coords.longitude, pos.coords.latitude])
                    .addTo(map);
            }});

            // Route Line
            map.addSource('route', {{
                'type': 'geojson',
                'data': {{
                    'type': 'Feature',
                    'geometry': {{
                        'type': 'LineString',
                        'coordinates': {route_coords_js}
                    }}
                }}
            }});

            map.addLayer({{
                'id': 'route-line',
                'type': 'line',
                'source': 'route',
                'layout': {{
                    'line-join': 'round',
                    'line-cap': 'round'
                }},
                'paint': {{
                    'line-color': '#00FF99',
                    'line-width': 6
                }}
            }});
        }});
    </script>
    </body>
    </html>
    """, height=650)

else:
    st.warning("⚠️ No route found. Please calculate a route first to display it on the map.")
