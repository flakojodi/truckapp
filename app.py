import streamlit as st
import streamlit.components.v1 as components

# Page config
st.set_page_config(page_title="Truck Route App", layout="centered")

# Title
st.title("🚛 Truck Route Planner")

# Instructions
st.markdown("""
Use this tool to:
- Plan truck-safe routes
- Avoid low bridges and weight limits
- Track your live GPS location
""")

# GPS Embed Section
st.markdown("### 📍 Real-Time GPS Tracker (Live)")
components.iframe("https://flakojodi.github.io/truckapp/gps.html", height=600, scrolling=True)

# Optional: Add routing section header for next step
st.markdown("### 🧭 Truck-Safe Route Planner (Coming Soon)")
st.info("Start and destination routing will appear here in the next update.")
