import streamlit as st
import requests
import time

# ---------------------------
# Auto-detect location
# ---------------------------
def detect_location():
    try:
        ip_data = requests.get("https://ipapi.co/json/").json()
        city = ip_data.get("city", "")
        country = ip_data.get("country_code", "")
        lat = ip_data.get("latitude", None)
        lon = ip_data.get("longitude", None)
        return city, country, lat, lon
    except:
        return None, None, None, None

# ---------------------------
# Fetch AQI
# ---------------------------
def get_live_aqi(lat, lon, api_key):
    try:
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        aqi_data = requests.get(aqi_url).json()
        if "list" not in aqi_data:
            return None, None
        aqi_level = aqi_data["list"][0]["main"]["aqi"]
        components = aqi_data["list"][0]["components"]
        return aqi_level, components
    except:
        return None, None

# ---------------------------
# AQI mapping
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

# ---------------------------
# Cloud animation
# ---------------------------
def parallax_clouds_dynamic(aqi_level):
    aqi_colors = {
        1: "#87ceeb",
        2: "#a0d6ff",
        3: "#ffdd99",
        4: "#ff9999",
        5: "#4d4d4d"
    }
    bg_color = aqi_colors.get(aqi_level, "#87ceeb")
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(to bottom, {bg_color}, #ffffff);
            transition: background 2s ease;
        }}
        .cloud-layer1 {{
            background: url('https://i.ibb.co/5s7G9m3/cloud.png') repeat-x;
            position: fixed;
            top: 50px;
            left: 0;
            width: 200%;
            height: 200px;
            background-size: 350px 200px;
            animation: moveLayer1 120s linear infinite;
            z-index: -3;
        }}
        @keyframes moveLayer1 {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        </style>
        <div class="cloud-layer1"></div>
    """, unsafe_allow_html=True)

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Live Air Quality", page_icon="🌍", layout="wide")
st.title("🌬️ Live Air Quality Monitor")

api_key = "YOUR_API_KEY"  # Replace with OpenWeather API key

# Detect location automatically
city, country, lat, lon = detect_location()

if city:
    st.success(f"📍 Detected Location: {city}, {country}")
else:
    st.warning("⚠ Could not detect location.")

# Fetch AQI immediately
if lat and lon:
    aqi_level, components = get_live_aqi(lat, lon, api_key)

    if aqi_level:
        desc, color, icon = get_aqi_description(aqi_level)
        parallax_clouds_dynamic(aqi_level)

        st.markdown(f"## {icon} AQI Level: **{aqi_level} - {desc}**")
        st.markdown("### 🌫️ Pollutant Levels (µg/m³)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PM2.5", components["pm2_5"])
            st.metric("PM10", components["pm10"])
        with col2:
            st.metric("NO₂", components["no2"])
            st.metric("SO₂", components["so2"])
        with col3:
            st.metric("O₃", components["o3"])
            st.metric("CO", components["co"])
    else:
        st.error("❌ Could not fetch AQI data.")
else:
    st.error("❌ No coordinates available.")
