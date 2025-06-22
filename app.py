import streamlit as st

st.set_page_config(page_title="Truck Route App", layout="centered")

st.title("🚛 Truck Route Planner")

st.markdown("Use this tool to plan safe truck routes with bridge height, weight, and clearance in mind.")

# GPS map link
st.markdown("### Real-Time GPS Tracker")
st.markdown("[📍 Launch Live GPS Map](gps.html)", unsafe_allow_html=True)
