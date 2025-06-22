
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Truck Route Planner", layout="centered")
st.title("🚛 Truck Route Planner - Map Version")

st.sidebar.header("Vehicle Specs")
height = st.sidebar.number_input("Height (ft)", value=13.6)
width = st.sidebar.number_input("Width (ft)", value=8.5)
length = st.sidebar.number_input("Length (ft)", value=53.0)
weight = st.sidebar.number_input("Weight (lbs)", value=80000.0)

st.header("🗺️ Route Info")
start = st.text_input("Starting Address", placeholder="e.g. Chicago, IL")
end = st.text_input("Destination Address", placeholder="e.g. Indianapolis, IN")

if st.button("Generate Route Map"):
    geolocator = Nominatim(user_agent="truck_route_app")

    start_loc = geolocator.geocode(start)
    end_loc = geolocator.geocode(end)
    if not start_loc or not end_loc:
        st.error("Could not find one or both locations.")
    else:
        m = folium.Map(location=[(start_loc.latitude + end_loc.latitude)/2,
                                 (start_loc.longitude + end_loc.longitude)/2],
                       zoom_start=6)
        folium.Marker([start_loc.latitude, start_loc.longitude], icon=folium.Icon(color='green'), tooltip='Start').add_to(m)
        folium.Marker([end_loc.latitude, end_loc.longitude], icon=folium.Icon(color='red'), tooltip='End').add_to(m)
        folium.PolyLine([[start_loc.latitude, start_loc.longitude],
                         [end_loc.latitude, end_loc.longitude]],
                        color='blue', weight=5, opacity=0.7).add_to(m)
        st_folium(m, width=700, height=500)
