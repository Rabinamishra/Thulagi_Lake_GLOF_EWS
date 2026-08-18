from pathlib import Path
import pandas as pd
import geopandas as gpd
import streamlit as st
import plotly.express as px

# ============================================================
# THULAGI LAKE GLOF EWS PROTOTYPE DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Thulagi Lake GLOF EWS",
    page_icon="🌊",
    layout="wide"
)

# ------------------------------------------------------------
# FILES
# ------------------------------------------------------------

RAINFALL_FILE = Path("data/rainfall/rainfall_daily.csv")
RAINFALL_INDICATORS = Path("data/rainfall/rainfall_indicators.csv")
WATER_FILE = Path("data/water_level/simulated_water_level.csv")
AOI_FILE = Path("data/spatial/thulagi_aoi.geojson")

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

rainfall = pd.read_csv(RAINFALL_FILE, parse_dates=["date"])
rainfall_indicators = pd.read_csv(RAINFALL_INDICATORS)

water = pd.read_csv(WATER_FILE, parse_dates=["timestamp"])

aoi = gpd.read_file(AOI_FILE)

# ------------------------------------------------------------
# LAKE AREA DATA — LOCKED
# ------------------------------------------------------------

lake_area = pd.DataFrame({
    "Year": [2016, 2018, 2020, 2022, 2024, 2025],
    "Area_km2": [0.8270, 0.8627, 0.8844, 0.9209, 0.9167, 0.9291]
})

# ------------------------------------------------------------
# CURRENT VALUES
# ------------------------------------------------------------

r = rainfall_indicators.iloc[0]

rainfall_status = r["rainfall_status"]
rainfall_percentile = r["historical_7day_percentile"]
rainfall_7day = r["rainfall_7day_mm"]

latest_water = water.iloc[-1]

water_level = latest_water["water_level_m"]
rise_rate = latest_water["rise_rate_m_per_hour"]

# ------------------------------------------------------------
# ALERT LOGIC
# Same logic as alert_engine.py
# ------------------------------------------------------------

if rainfall_status == "HIGH":
    rainfall_score = 2
elif rainfall_status == "ELEVATED":
    rainfall_score = 1
else:
    rainfall_score = 0

if rise_rate >= 0.05:
    water_status = "RAPID RISE"
    water_score = 2
elif rise_rate >= 0.02:
    water_status = "RISING"
    water_score = 1
else:
    water_status = "STABLE"
    water_score = 0

lake_change = lake_area.iloc[-1]["Area_km2"] - lake_area.iloc[-2]["Area_km2"]

if lake_change > 0.01:
    lake_status = "ELEVATED"
    lake_score = 1
else:
    lake_status = "NORMAL"
    lake_score = 0

total_score = rainfall_score + water_score + lake_score

if total_score >= 4:
    alert_level = "ALERT"
elif total_score >= 2:
    alert_level = "WATCH"
else:
    alert_level = "NORMAL"

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🌊 Thulagi Lake GLOF Early-Warning Prototype")

st.caption(
    "Multi-indicator decision-support prototype combining "
    "satellite lake monitoring, rainfall and water-level indicators."
)

# ------------------------------------------------------------
# ALERT
# ------------------------------------------------------------

if alert_level == "ALERT":
    st.error("🚨 ALERT — PROTOTYPE")
elif alert_level == "WATCH":
    st.warning("⚠️ WATCH — PROTOTYPE")
else:
    st.success("✅ NORMAL — PROTOTYPE")

st.write(
    "Current prototype classification is based on combined environmental evidence."
)

# ------------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Rainfall Evidence",
        rainfall_status
    )
    st.caption(f"7-day percentile: {rainfall_percentile:.2f}")

with col2:
    st.metric(
        "7-Day Rainfall",
        f"{rainfall_7day:.2f} mm"
    )

with col3:
    st.metric(
        "Water Level",
        f"{water_level:.2f} m"
    )
    st.caption(f"Rise rate: {rise_rate:.3f} m/hour")

with col4:
    st.metric(
        "Latest Lake Area",
        f"{lake_area.iloc[-1]['Area_km2']:.4f} km²"
    )
    st.caption("Latest satellite observation")

# ------------------------------------------------------------
# ALERT EXPLANATION
# ------------------------------------------------------------

st.subheader("Alert Explanation")

reasons = []

if rainfall_score > 0:
    reasons.append(
        f"🌧️ Recent rainfall is {rainfall_status.lower()} "
        f"({rainfall_percentile:.1f}th historical percentile)."
    )

if water_score > 0:
    reasons.append(
        f"💧 Water level is {water_status.lower()} "
        f"at {water_level:.2f} m."
    )

if lake_score > 0:
    reasons.append(
        f"🛰️ Latest observed lake area increased by "
        f"{lake_change:.4f} km² compared with the previous observation."
    )

for reason in reasons:
    st.write(reason)

# ------------------------------------------------------------
# RAINFALL TREND
# ------------------------------------------------------------

st.subheader("Recent Rainfall")

recent_rainfall = rainfall.tail(120)

fig_rain = px.line(
    recent_rainfall,
    x="date",
    y="rainfall_mm",
    labels={
        "date": "Date",
        "rainfall_mm": "Rainfall (mm)"
    }
)

fig_rain.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig_rain, width="stretch")

# ------------------------------------------------------------
# WATER LEVEL
# ------------------------------------------------------------

st.subheader("Water-Level Telemetry")

recent_water = water.tail(145)

fig_water = px.line(
    recent_water,
    x="timestamp",
    y="water_level_m",
    labels={
        "timestamp": "Time",
        "water_level_m": "Water Level (m)"
    }
)

fig_water.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig_water, width="stretch")

st.caption("⚠️ Water-level data shown here are SIMULATED for prototype demonstration.")

# ------------------------------------------------------------
# LAKE AREA HISTORY
# ------------------------------------------------------------

st.subheader("Satellite-Derived Lake-Area History")

fig_area = px.line(
    lake_area,
    x="Year",
    y="Area_km2",
    markers=True,
    labels={
        "Year": "Observation Year",
        "Area_km2": "Lake Area (km²)"
    }
)

fig_area.update_layout(
    height=350,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig_area, width="stretch")

# ------------------------------------------------------------
# MAP
# ------------------------------------------------------------

st.subheader("Thulagi Lake Monitoring Area")

map_data = aoi.to_crs(4326)

map_center = pd.DataFrame({
    "latitude": [28.493999],
    "longitude": [84.482029]
})

st.map(
    map_center,
    latitude="latitude",
    longitude="longitude",
    zoom=12
)

st.caption(
    "Monitoring AOI shown above. A hydrodynamic inundation model is "
    "not included in this prototype; therefore exposure areas are not "
    "presented as predicted flood boundaries."
)

# ------------------------------------------------------------
# METHODOLOGICAL NOTE
# ------------------------------------------------------------

st.divider()

st.subheader("Prototype Disclaimer")

st.info(
    "This system is a research and decision-support prototype. "
    "Alert levels demonstrate a multi-indicator EWS workflow and "
    "are not operational GLOF warning thresholds. Operational use "
    "would require validated thresholds, real-time sensor data, "
    "hydrodynamic inundation modelling, historical event validation, "
    "reliability testing and institutional authorization."
)

st.caption(
    "Thulagi Lake | Sentinel-2 + rainfall + simulated water-level telemetry"
)