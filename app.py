import streamlit as st

st.set_page_config(page_title="Truck Route Planner", layout="centered")

st.title("🚛 Truck Route Planner - MVP")

st.markdown("Enter your vehicle's dimensions below:")

height = st.number_input("Vehicle Height (in feet)", min_value=0.0, value=13.6)
width = st.number_input("Vehicle Width (in feet)", min_value=0.0, value=8.5)
length = st.number_input("Vehicle Length (in feet)", min_value=0.0, value=53.0)
weight = st.number_input("Vehicle Weight (in pounds)", min_value=0.0, value=80000.0)

if st.button("Submit"):
    st.success("✅ Vehicle specs submitted!")
    st.markdown(f"""
    ### Your Vehicle Specs:
    - **Height:** {height} ft  
    - **Width:** {width} ft  
    - **Length:** {length} ft  
    - **Weight:** {weight} lbs  
    """)
