import streamlit as st
import requests
import joblib
import numpy as np

# ---------------------------
# Load KNN Model
# ---------------------------
model = joblib.load("air_quality_knn.pkl")
scaler = joblib.load("scaler.pkl")
feature_names = joblib.load("feature_names.pkl")

# ---------------------------
# Detect location via IP
# ---------------------------
def detect_location():
    try:
        ip_data = requests.get("https://ipapi.co/json/").json()
        return ip_data.get("city"), ip_data.get("region"), ip_data.get("country_code"), ip_data.get("latitude"), ip_data.get("longitude")
    except:
        return None, None, None, None, None

# ---------------------------
# Get coordinates from city
# ---------------------------
def get_coordinates_from_city(city_name, api_key):
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
        geo_data = requests.get(geo_url).json()
        if len(geo_data) == 0:
            return None, None, None, None
        city = geo_data[0]["name"]
        state = geo_data[0].get("state", "")
        country = geo_data[0]["country"]
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        return city, state, country, lat, lon
    except:
        return None, None, None, None

# ---------------------------
# Get live AQI data
# ---------------------------
def get_live_aqi(lat, lon, api_key):
    try:
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        aqi_data = requests.get(aqi_url).json()
        if "list" not in aqi_data:
            return None, None
        return aqi_data["list"][0]["main"]["aqi"], aqi_data["list"][0]["components"]
    except:
        return None, None

# ---------------------------
# AQI descriptions
# ---------------------------
def get_aqi_description(aqi):
    mapping = {
        1: ("Good", "#87ceeb", "☀️"),
        2: ("Fair", "#a0d6ff", "🌤"),
        3: ("Moderate", "#ffdd99", "⛅"),
        4: ("Poor", "#ff9999", "🌫"),
        5: ("Very Poor", "#4d4d4d", "⛈️")
    }
    return mapping.get(aqi, ("Unknown", "#87ceeb", "❓"))

def get_health_tip(aqi):
    tips = {
        1: "Air quality is excellent. Enjoy outdoor activities!",
        2: "Fair air quality — acceptable for most, but sensitive groups should limit outdoor exposure.",
        3: "Moderate pollution — people with breathing issues should take precautions.",
        4: "Poor air quality — reduce outdoor activities.",
        5: "Very Poor! Stay indoors and use air purifiers if possible."
    }
    return tips.get(aqi, "No advice available.")

# ---------------------------
# Animated clouds & dynamic background
# ---------------------------
def parallax_clouds_dynamic(aqi_level):
    bg_color = {
        1: "#87ceeb",
        2: "#a0d6ff",
        3: "#ffdd99",
        4: "#ff9999",
        5: "#4d4d4d"
    }.get(aqi_level, "#87ceeb")

    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(to bottom, {bg_color}, #ffffff);
            transition: background 2s ease;
        }}
        .cloud-layer {{
            background: url('https://i.ibb.co/5s7G9m3/cloud.png') repeat-x;
            position: fixed;
            top: 50px;
            left: 0;
            width: 200%;
            height: 200px;
            background-size: 350px 200px;
            animation: moveClouds 120s linear infinite;
            z-index: -3;
        }}
        @keyframes moveClouds {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        </style>
        <div class="cloud-layer"></div>
    """, unsafe_allow_html=True)

# ---------------------------
# Display AQI info
# ---------------------------
def display_aqi_info(city, state, country, aqi_level, components):
    desc, _, icon = get_aqi_description(aqi_level)
    st.markdown(f"## 📍 **{city}, {state} ({country})**")
    st.markdown(f"### 📊 AQI: **{aqi_level} - {desc} {icon}**")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PM2.5", f"{components['pm2_5']} µg/m³")
        st.metric("PM10", f"{components['pm10']} µg/m³")
    with col2:
        st.metric("NO₂", f"{components['no2']} µg/m³")
        st.metric("O₃", f"{components['o3']} µg/m³")
    with col3:
        st.metric("SO₂", f"{components['so2']} µg/m³")
        st.metric("CO", f"{components['co']} µg/m³")

    st.markdown(f"💡 **Tip:** {get_health_tip(aqi_level)}")

# ---------------------------
# Prediction UI
# ---------------------------
def knn_prediction_ui():
    st.subheader("🤖 Predict Air Quality Category (KNN Model)")
    user_input = []
    for feature in feature_names:
        val = st.number_input(f"{feature}", min_value=0.0, format="%.2f")
        user_input.append(val)

    if st.button("Predict"):
        X_input = np.array(user_input).reshape(1, -1)
        X_scaled = scaler.transform(X_input)
        pred_class = int(model.predict(X_scaled)[0])
        desc, color, icon = get_aqi_description(pred_class)

        st.markdown(
            f"""
            <div style="
                background-color: {color};
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
            ">
            {icon} Predicted Air Quality Class: {pred_class} - {desc}
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------
# Main App
# ---------------------------
st.set_page_config(page_title="Live Air Quality", page_icon="🌍", layout="wide")
st.title("🌬️ Live Air Quality Monitor & KNN Prediction")

API_KEY = "4256fdd900f649fae78b69c83cef84d3"  # Replace with your OpenWeather API key

# Auto-detect
city, state, country, lat, lon = detect_location()

# Sidebar Location Settings
st.sidebar.subheader("🌍 Location Settings")
popular_cities = ["Auto-detect", "Delhi", "Mumbai", "Bengaluru", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad", "Jaipur"]
selected_city = st.sidebar.selectbox("Select a city:", popular_cities)
custom_city = st.sidebar.text_input("Or enter custom city:")

if selected_city != "Auto-detect":
    city, state, country, lat, lon = get_coordinates_from_city(selected_city, API_KEY)
elif custom_city:
    city, state, country, lat, lon = get_coordinates_from_city(custom_city, API_KEY)
elif not city or not lat or not lon:
    st.warning("⚠ Could not auto-detect location. Please choose or enter a city.")

# Fetch AQI
if city and lat and lon:
    aqi_level, components = get_live_aqi(lat, lon, API_KEY)
    if aqi_level:
        parallax_clouds_dynamic(aqi_level)
        display_aqi_info(city, state, country, aqi_level, components)
    else:
        st.error("❌ Could not fetch AQI data.")
else:
    st.error("❌ Location unavailable.")

st.markdown("---")
knn_prediction_ui()













#-----------<BACK - UP>----------------------------------#

# import streamlit as st
# import pandas as pd
# import numpy as np
# import joblib
# import requests

# # ==============================
# # Load Model, Scaler, Encoder
# # ==============================
# model = joblib.load("air_quality_knn.pkl")
# scaler = joblib.load("scaler.pkl")
# label_encoder = joblib.load("label_encoder.pkl")
# feature_names = joblib.load("feature_names.pkl")

# # ==============================
# # Color Map
# # ==============================
# color_map = {
#     "Good": "lightgreen",
#     "Moderate": "khaki",
#     "Poor": "orange",
#     "Very Poor": "red",
#     "Severe": "darkred"
# }

# cloud_color_map = {
#     "Good": "☁️",
#     "Moderate": "☁️",
#     "Poor": "🌥️",
#     "Very Poor": "🌥️",
#     "Severe": "🌫️"
# }

# # Function to inject clouds with correct emoji
# def cloud_background(cloud_icon):
#     st.markdown(f"""
#         <style>
#         body {{
#             background: linear-gradient(to bottom, #87ceeb, #e6f3ff);
#             overflow: hidden;
#         }}
#         .cloud {{
#             position: absolute;
#             top: 50px;
#             left: -200px;
#             font-size: 50px;
#             animation: moveClouds 60s linear infinite;
#         }}
#         .cloud2 {{
#             position: absolute;
#             top: 100px;
#             left: -200px;
#             font-size: 50px;
#             animation: moveClouds 80s linear infinite;
#         }}
#         .cloud3 {{
#             position: absolute;
#             top: 150px;
#             left: -200px;
#             font-size: 60px;
#             animation: moveClouds 90s linear infinite;
#         }}
#         @keyframes moveClouds {{
#             0% {{ left: -200px; }}
#             100% {{ left: 110%; }}
#         }}
#         </style>

#         <div class="cloud">{cloud_icon}</div>
#         <div class="cloud2">{cloud_icon}</div>
#         <div class="cloud3">{cloud_icon}</div>
#     """, unsafe_allow_html=True)

# # ==============================
# # Page Config
# # ==============================
# st.set_page_config(page_title="Air Quality Classification", layout="wide")
# cloud_background("☁️")  # Default background before prediction

# st.markdown("<h1 style='text-align:center; color:#004466;'>🌍 Real-Time Air Quality Classification</h1>", unsafe_allow_html=True)
# st.write("Predict air quality using KNN — Manual input, CSV upload, or Live Data.")

# # ==============================
# # Sidebar Mode Selection
# # ==============================
# mode = st.sidebar.radio("Choose Mode", ["Manual Input", "CSV Upload", "Live Air Quality Check"])

# # Manual Input
# if mode == "Manual Input":
#     st.subheader("☁️ Enter Air Quality Parameters")
#     inputs = []
#     for feature in feature_names:
#         value = st.number_input(f"{feature}:", min_value=0.0, step=0.1)
#         inputs.append(value)

#     if st.button("Predict Air Quality"):
#         X_input = np.array(inputs).reshape(1, -1)
#         X_scaled = scaler.transform(X_input)
#         prediction = model.predict(X_scaled)
#         label = label_encoder.inverse_transform(prediction)[0]

#         cloud_background(cloud_color_map[label])  # Change clouds after prediction

#         st.markdown(
#             f"<div style='padding:10px; background-color:{color_map[label]}; color:white; border-radius:5px; text-align:center;'>"
#             f"<h3>Air Quality: {label} {cloud_color_map[label]}</h3></div>",
#             unsafe_allow_html=True
#         )

# # CSV Upload
# elif mode == "CSV Upload":
#     st.subheader("📂 Upload CSV File")
#     uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
#     if uploaded_file is not None:
#         df = pd.read_csv(uploaded_file)
#         st.write("📄 Uploaded Data Preview:", df.head())

#         df = df[feature_names]
#         X_scaled = scaler.transform(df)
#         predictions = model.predict(X_scaled)
#         labels = label_encoder.inverse_transform(predictions)

#         df["Predicted Air Quality"] = labels

#         def highlight(val):
#             return f"background-color: {color_map[val]}; color: white;"

#         st.dataframe(df.style.applymap(highlight, subset=["Predicted Air Quality"]))

# # Live Air Quality Check
# elif mode == "Live Air Quality Check":
#     st.subheader("🌐 Get Live Air Quality Data")
#     city = st.text_input("Enter City Name")
#     api_key = "4256fdd900f649fae78b69c83cef84d3"

#     if st.button("Check Live Air Quality"):
#         if not city or not api_key:
#             st.error("Please enter both city name and API key.")
#         else:
#             try:
#                 # Step 1: Get coordinates
#                 geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
#                 geo_response = requests.get(geo_url)
#                 geo_data = geo_response.json()

#                 st.write("📍 Geo API Response:", geo_data)  # Debug

#                 if not geo_data:
#                     st.error("❌ City not found or Geo API returned no data.")
#                     st.stop()

#                 lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
#                 st.write(f"Coordinates: {lat}, {lon}")

#                 # Step 2: Get air quality data
#                 air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
#                 air_response = requests.get(air_url)
#                 air_data = air_response.json()

#                 st.write("🌬️ Air Pollution API Response:", air_data)  # Debug

#                 if "list" not in air_data or not air_data["list"]:
#                     st.error("❌ Air quality data not available for this location.")
#                     st.stop()

#                 # Extract data
#                 components = air_data["list"][0]["components"]
#                 aqi_value = air_data["list"][0]["main"]["aqi"]

#                 live_data = [
#                     components.get("pm2_5", 0),
#                     components.get("pm10", 0),
#                     components.get("no2", 0),
#                     components.get("so2", 0),
#                     components.get("o3", 0),
#                     aqi_value * 100
#                 ]

#                 # Prediction
#                 X_scaled = scaler.transform(np.array(live_data).reshape(1, -1))
#                 prediction = model.predict(X_scaled)
#                 label = label_encoder.inverse_transform(prediction)[0]

#                 cloud_background(cloud_color_map[label])

#                 st.markdown(
#                     f"<div style='padding:10px; background-color:{color_map[label]}; color:white; border-radius:5px; text-align:center;'>"
#                     f"<h3>Live Air Quality in {city}: {label} {cloud_color_map[label]}</h3></div>",
#                     unsafe_allow_html=True
#                 )

#             except Exception as e:
#                 st.error(f"Error fetching live data: {repr(e)}")  # More detailed error
