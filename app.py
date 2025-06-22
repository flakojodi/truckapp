// truck-gps-app (React + Mapbox)
// MVP: Real-time location tracking + route rendering

import { useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

mapboxgl.accessToken = 'pk.eyJ1IjoiZmxha29qb2RpIiwiYSI6ImNtYzdsdTlpZzBsanoybHEyamVva2Fpb2sifQ.zqpdCfGvzD0YCCCExKXsLg'; // ✅ Your token

export default function TruckGPSApp() {
  const [map, setMap] = useState(null);
  const [userCoords, setUserCoords] = useState(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(position => {
      const { latitude, longitude } = position.coords;
      setUserCoords([longitude, latitude]);
    });
  }, []);

  useEffect(() => {
    if (!userCoords) return;

    const initMap = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v11',
      center: userCoords,
      zoom: 13
    });

    new mapboxgl.Marker({ color: 'green' })
      .setLngLat(userCoords)
      .setPopup(new mapboxgl.Popup().setText('You are here'))
      .addTo(initMap);

    setMap(initMap);

    return () => initMap.remove();
  }, [userCoords]);

  return (
    <div className="w-full h-screen">
      <div id="map" className="w-full h-full rounded-xl shadow-lg" />
    </div>
  );
}
st.markdown("[🚛 Launch Live GPS Map](gps.html)", unsafe_allow_html=True)
