import streamlit as st

st.set_page_config(page_title="Truck GPS App", layout="centered")
st.title("🚛 Truck Route Planner")

st.markdown("Use this tool to plan truck-safe routes and track your real-time location.")

# Embed GPS map (hosted inside an iframe)
st.markdown("### Real-Time GPS Map (Built-In)")
st.components.v1.iframe("https://flakojodi.github.io/truckapp/gps.html", height=600, scrolling=True)
