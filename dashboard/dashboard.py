"""
🌱 Greenhouse Monitoring System - Real-World Units Dashboard
Displays Solar Irradiance in Lux (lx), Air Quality Index (AQI), CO2 (ppm), Oxygen (%),
Temperature (°C), Humidity (%), and Vapor Pressure Deficit (VPD).
"""

import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import math
import time
import os
import sys

# Add anomaly detector module to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "anomaly")))
from anomaly_detector import (
    detect_anomalies_detailed,
    adc_to_lux,
    adc_to_aqi,
    estimate_co2_ppm,
    estimate_oxygen_pct,
    DEFAULT_THRESHOLDS
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "greenhouse.db"))


def calculate_vpd(temperature: float, humidity: float) -> float:
    """Calculate Vapor Pressure Deficit (VPD) in kPa."""
    if temperature is None or humidity is None or humidity <= 0:
        return 0.0
    vp_sat = 0.61078 * math.exp((17.27 * temperature) / (temperature + 237.3))
    vp_act = vp_sat * (humidity / 100.0)
    return max(0.0, vp_sat - vp_act)


def load_sensor_data(limit: int = 100) -> pd.DataFrame:
    """Fetch latest sensor readings from SQLite database."""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        df = pd.read_sql_query(f"""
            SELECT id, timestamp, temperature, humidity, light, gas
            FROM sensor_data
            ORDER BY id DESC
            LIMIT {limit}
        """, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# =====================================================================
# Page Configuration & Styling
# =====================================================================
st.set_page_config(
    page_title="Greenhouse Climate & Gas Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .pulse-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #10b981;
        animation: pulse 2s infinite;
        margin-right: 6px;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .badge-normal {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-danger {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-optimal-card {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 1px solid #86efac;
        border-radius: 12px;
        padding: 18px 22px;
        color: #065f46;
        margin-bottom: 20px;
    }
    .status-alert-card {
        background: linear-gradient(135deg, #fef2f2 0%, #fff1f2 100%);
        border: 1px solid #fca5a5;
        border-radius: 12px;
        padding: 18px 22px;
        color: #991b1b;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Sidebar: Real-World Unit Threshold Controls
# =====================================================================
st.sidebar.markdown("## ⚙️ Threshold Setters")
st.sidebar.caption("All thresholds are in standard physical & horticultural units:")

with st.sidebar.expander("🌡️ Temperature (°C)", expanded=True):
    temp_min = st.slider("Min Temperature (°C)", 0.0, 30.0, 15.0, 0.5)
    temp_max = st.slider("Max Temperature (°C)", 20.0, 50.0, 40.0, 0.5)

with st.sidebar.expander("💧 Relative Humidity (%)", expanded=True):
    hum_min = st.slider("Min Humidity (%)", 10.0, 50.0, 25.0, 1.0)
    hum_max = st.slider("Max Humidity (%)", 50.0, 100.0, 85.0, 1.0)

with st.sidebar.expander("☀️ Solar Light (Lux / lx)", expanded=True):
    lux_min = st.slider("Min Solar Light (Lux)", 0, 10000, 2000, 200)
    lux_max = st.slider("Max Solar Light (Lux)", 10000, 65000, 55000, 1000)

with st.sidebar.expander("🫁 Air Quality Index (AQI)", expanded=True):
    aqi_max = st.slider("Max Air Quality Index (AQI)", 50, 300, 150, 10, help="0-50: Good, 51-100: Moderate, 101-150: Elevated, 151+: Unhealthy")

with st.sidebar.expander("🌿 CO₂ Level (ppm)", expanded=False):
    co2_min = st.slider("Min CO₂ Depletion (ppm)", 300, 800, 350, 25)
    co2_max = st.slider("Max CO₂ Stale Limit (ppm)", 1000, 2500, 1800, 50)

with st.sidebar.expander("💨 Oxygen O₂ (%)", expanded=False):
    o2_min = st.slider("Min Oxygen Threshold (%)", 18.0, 20.5, 19.8, 0.1)

active_thresholds = {
    "temp_low": temp_min,
    "temp_high": temp_max,
    "humidity_low": hum_min,
    "humidity_high": hum_max,
    "lux_low": lux_min,
    "lux_high": lux_max,
    "aqi_high": aqi_max,
    "co2_low": co2_min,
    "co2_high": co2_max,
    "o2_low": o2_min
}

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Stream Controls")
history_limit = st.sidebar.slider("History Window Size", 20, 300, 100, 10)
auto_refresh = st.sidebar.toggle("Live Telemetry Stream", value=True)
refresh_interval = st.sidebar.selectbox("Refresh Speed", [2, 3, 5], index=0, format_func=lambda s: f"{s} seconds")


# =====================================================================
# Load Data & Feature Computation
# =====================================================================
df = load_sensor_data(limit=history_limit)

if df.empty:
    st.info("⏳ **Waiting for sensor data stream...** Ensure `python backend/app.py` is running and sensors are transmitting.")
    st.stop()

df_chrono = df.iloc[::-1].copy().reset_index(drop=True)
df_chrono["timestamp_dt"] = pd.to_datetime(df_chrono["timestamp"])

# Convert all readings into real-world units
df_chrono["lux"] = df_chrono["light"].apply(adc_to_lux)
df_chrono["light_pct"] = df_chrono["light"].apply(lambda l: round((l / 4095.0) * 100, 1))

aqi_results = df_chrono["gas"].apply(adc_to_aqi)
df_chrono["aqi"] = [r[0] for r in aqi_results]
df_chrono["aqi_category"] = [r[1] for r in aqi_results]

df_chrono["co2_ppm"] = df_chrono["gas"].apply(estimate_co2_ppm)
df_chrono["oxygen_pct"] = df_chrono.apply(lambda r: estimate_oxygen_pct(r["light"], r["gas"]), axis=1)
df_chrono["vpd_kpa"] = df_chrono.apply(lambda r: calculate_vpd(r["temperature"], r["humidity"]), axis=1)

latest = df_chrono.iloc[-1]
prev = df_chrono.iloc[-2] if len(df_chrono) > 1 else latest

# Deltas
temp_delta = latest["temperature"] - prev["temperature"] if prev["temperature"] is not None else 0.0
hum_delta = latest["humidity"] - prev["humidity"] if prev["humidity"] is not None else 0.0
lux_delta = latest["lux"] - prev["lux"]
aqi_delta = latest["aqi"] - prev["aqi"]
co2_delta = latest["co2_ppm"] - prev["co2_ppm"]
o2_delta = latest["oxygen_pct"] - prev["oxygen_pct"]

# Anomaly Evaluation
eval_result = detect_anomalies_detailed(
    temperature=latest["temperature"],
    humidity=latest["humidity"],
    light=latest["light"],
    gas=latest["gas"],
    thresholds=active_thresholds
)

# Header Banner
ts_str = str(latest["timestamp"]).split("T")[-1][:8]
st.markdown(f"""
<div class="header-banner">
    <div>
        <h1 style="margin:0; font-size: 1.85rem; font-weight: 700; color: #ffffff;">🌱 Smart Greenhouse Climate & Gas Intelligence</h1>
        <p style="margin:4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">Real-time physical telemetry: Lux, AQI, CO₂, Oxygen, and Vapor Pressure Deficit (VPD)</p>
    </div>
    <div style="text-align: right;">
        <span class="badge-normal" style="background:#064e3b; color:#6ee7b7; border-color:#059669;">
            <span class="pulse-dot"></span> LIVE SENSORS CONNECTED
        </span>
        <div style="font-size:0.8rem; color:#94a3b8; margin-top:5px;">Last Packet: {ts_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# Row 1: Primary Environmental Telemetry (Standard Real-World Units)
# =====================================================================
st.markdown("### 🌡️ Primary Environmental Telemetry")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Temperature",
        value=f"{latest['temperature']:.1f} °C",
        delta=f"{temp_delta:+.1f} °C" if len(df_chrono) > 1 else None
    )
    if eval_result["metrics_status"]["temperature"] != "NORMAL":
        st.markdown(f"<span class='badge-danger'>⚠️ Anomaly (> {active_thresholds['temp_high']}°C)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-normal'>🟢 Target: {active_thresholds['temp_low']}–{active_thresholds['temp_high']}°C</span>", unsafe_allow_html=True)

with col2:
    st.metric(
        label="Relative Humidity",
        value=f"{latest['humidity']:.1f} %",
        delta=f"{hum_delta:+.1f} %" if len(df_chrono) > 1 else None
    )
    if eval_result["metrics_status"]["humidity"] != "NORMAL":
        st.markdown(f"<span class='badge-danger'>⚠️ Anomaly</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-normal'>🟢 Target: {active_thresholds['humidity_low']}–{active_thresholds['humidity_high']}%</span>", unsafe_allow_html=True)

with col3:
    st.metric(
        label="☀️ Solar Illuminance",
        value=f"{latest['lux']:,} Lux",
        delta=f"{lux_delta:+d} Lux" if len(df_chrono) > 1 else None
    )
    if eval_result["metrics_status"]["light"] != "NORMAL":
        st.markdown(f"<span class='badge-warning'>⚠️ Out of Range</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-normal'>🟢 Solar Intensity: {latest['light_pct']}%</span>", unsafe_allow_html=True)

with col4:
    cur_aqi = latest["aqi"]
    cur_cat = latest["aqi_category"]
    st.metric(
        label="🫁 Air Quality Index (AQI)",
        value=f"{cur_aqi} AQI",
        delta=f"{aqi_delta:+d} AQI" if len(df_chrono) > 1 else None
    )
    if eval_result["metrics_status"]["gas"] != "NORMAL" or cur_aqi > active_thresholds["aqi_high"]:
        st.markdown(f"<span class='badge-danger'>⚠️ {cur_cat} (> {active_thresholds['aqi_high']} AQI)</span>", unsafe_allow_html=True)
    elif cur_aqi <= 50:
        st.markdown(f"<span class='badge-normal'>🟢 {cur_cat} (Fresh Air)</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span class='badge-normal'>🟢 {cur_cat} (Clean Ambient)</span>", unsafe_allow_html=True)


# =====================================================================
# Row 2: Gas Dynamics, CO2, Oxygen, and VPD
# =====================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🌿 Botanical Gas Balance & Transpiration Index")

g1, g2, g3 = st.columns(3)

with g1:
    cur_co2 = latest["co2_ppm"]
    st.metric(
        label="CO₂ Concentration & Availability",
        value=f"{cur_co2} ppm",
        delta=f"{co2_delta:+d} ppm" if len(df_chrono) > 1 else None
    )
    if cur_co2 < active_thresholds["co2_low"]:
        st.markdown("<span class='badge-danger'>🔴 CO₂ Depletion (< 350 ppm)</span>", unsafe_allow_html=True)
    elif 800 <= cur_co2 <= 1400:
        st.markdown("<span class='badge-normal'>🟢 Optimal Photosynthesis Enrichment</span>", unsafe_allow_html=True)
    elif cur_co2 > active_thresholds["co2_high"]:
        st.markdown("<span class='badge-warning'>🟡 Stale Air / Elevated CO₂</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-normal'>🟢 Standard Ambient</span>", unsafe_allow_html=True)

with g2:
    cur_o2 = latest["oxygen_pct"]
    st.metric(
        label="Estimated Oxygen (O₂) Balance",
        value=f"{cur_o2:.1f} %",
        delta=f"{o2_delta:+.2f} %" if len(df_chrono) > 1 else None
    )
    if cur_o2 < active_thresholds["o2_low"]:
        st.markdown(f"<span class='badge-warning'>🟡 Low Oxygen (< {active_thresholds['o2_low']}%)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-normal'>🟢 Healthy Atmospheric Balance</span>", unsafe_allow_html=True)

with g3:
    vpd_val = latest["vpd_kpa"]
    st.metric(
        label="Vapor Pressure Deficit (VPD)",
        value=f"{vpd_val:.2f} kPa",
        delta="Transpiration Rate"
    )
    if 0.8 <= vpd_val <= 1.4:
        st.markdown("<span class='badge-normal'>🟢 Optimal Transpiration Sweet-Spot</span>", unsafe_allow_html=True)
    elif vpd_val < 0.8:
        st.markdown("<span class='badge-warning'>🟡 Gentle Transpiration (Low Stress)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge-warning'>🟡 Elevated Evaporative Stress</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =====================================================================
# System Health & Anomaly Notification Card
# =====================================================================
if eval_result["status"] == "NORMAL":
    st.markdown("""
    <div class="status-optimal-card">
        <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 4px;">
            🟢 ALL SYSTEMS OPTIMAL
        </div>
        <div style="font-size: 0.95rem; opacity: 0.9;">
            All physical sensor parameters (Temperature, Humidity, Lux, AQI, CO₂, O₂) are well within standard target setpoints.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="status-alert-card">
        <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 6px;">
            🔴 ANOMALY DETECTED ({len(eval_result['anomalies'])} Active Alert{'s' if len(eval_result['anomalies'])>1 else ''})
        </div>
        <div style="font-size: 0.95rem; font-weight: 500;">
            One or more threshold limits have been breached. Immediate environmental correction is recommended.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_a1, col_a2 = st.columns([1, 1])
    with col_a1:
        st.markdown("#### ⚠️ Active Alerts:")
        for anom in eval_result["anomalies"]:
            st.error(f"**Alert:** {anom}")
            
    with col_a2:
        st.markdown("#### 💡 Corrective Action Checklist:")
        for rem in eval_result["remediations"]:
            st.info(f"**Action:** {rem}")

st.markdown("<br>", unsafe_allow_html=True)


# =====================================================================
# Historical Time-Series Visualizations in Physical Units
# =====================================================================
st.markdown("### 📈 Interactive Environmental Trends (Real-World Units)")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌡️ Temperature (°C)", "💧 Humidity (%)", "☀️ Solar Light (Lux)", "🫁 Air Quality (AQI)", "🌱 CO₂ Level (ppm)", "💨 Oxygen (O₂ %)"
])

def create_styled_chart(df_data, col_name, title, unit, color="#2563eb", min_thresh=None, max_thresh=None):
    base = alt.Chart(df_data).encode(
        x=alt.X("timestamp_dt:T", title="Timestamp", axis=alt.Axis(format="%H:%M:%S", labelFontSize=11, titleFontSize=12))
    )
    
    area = base.mark_area(opacity=0.15, color=color).encode(
        y=alt.Y(f"{col_name}:Q", title=f"{title} ({unit})", scale=alt.Scale(zero=False))
    )
    
    line = base.mark_line(color=color, strokeWidth=2.5).encode(
        y=alt.Y(f"{col_name}:Q"),
        tooltip=[
            alt.Tooltip("timestamp_dt:T", title="Time", format="%Y-%m-%d %H:%M:%S"),
            alt.Tooltip(f"{col_name}:Q", title=f"{title} ({unit})", format=",.1f")
        ]
    )
    
    points = base.mark_circle(size=30, color=color).encode(
        y=alt.Y(f"{col_name}:Q")
    )
    
    layers = [area, line, points]

    if max_thresh is not None:
        high_rule = alt.Chart(pd.DataFrame({"y": [max_thresh]})).mark_rule(
            color="#ef4444", strokeDash=[6, 6], strokeWidth=1.8
        ).encode(y="y:Q")
        layers.append(high_rule)

    if min_thresh is not None:
        low_rule = alt.Chart(pd.DataFrame({"y": [min_thresh]})).mark_rule(
            color="#3b82f6", strokeDash=[6, 6], strokeWidth=1.8
        ).encode(y="y:Q")
        layers.append(low_rule)

    return alt.layer(*layers).properties(height=280)


with tab1:
    st.altair_chart(create_styled_chart(df_chrono, "temperature", "Temperature", "°C", color="#f97316", min_thresh=active_thresholds["temp_low"], max_thresh=active_thresholds["temp_high"]), use_container_width=True)
    st.caption(f"🔵 Min Temp ({active_thresholds['temp_low']}°C) | 🔴 Max Temp ({active_thresholds['temp_high']}°C)")

with tab2:
    st.altair_chart(create_styled_chart(df_chrono, "humidity", "Humidity", "%", color="#0284c7", min_thresh=active_thresholds["humidity_low"], max_thresh=active_thresholds["humidity_high"]), use_container_width=True)
    st.caption(f"🔵 Min Humidity ({active_thresholds['humidity_low']}%) | 🔴 Max Humidity ({active_thresholds['humidity_high']}%)")

with tab3:
    st.altair_chart(create_styled_chart(df_chrono, "lux", "Solar Illuminance", "Lux", color="#eab308", min_thresh=active_thresholds["lux_low"], max_thresh=active_thresholds["lux_high"]), use_container_width=True)
    st.caption(f"🔵 Min Light ({active_thresholds['lux_low']:,} Lux) | 🔴 Max Light ({active_thresholds['lux_high']:,} Lux)")

with tab4:
    st.altair_chart(create_styled_chart(df_chrono, "aqi", "Air Quality Index", "AQI", color="#8b5cf6", max_thresh=active_thresholds["aqi_high"]), use_container_width=True)
    st.caption(f"🔴 Hazard Limit ({active_thresholds['aqi_high']} AQI) — 0-50: Good, 51-100: Moderate, 101-150: Elevated, 151+: Unhealthy")

with tab5:
    st.altair_chart(create_styled_chart(df_chrono, "co2_ppm", "CO₂ Concentration", "ppm", color="#10b981", min_thresh=active_thresholds["co2_low"], max_thresh=active_thresholds["co2_high"]), use_container_width=True)
    st.caption(f"🔵 Min CO₂ ({active_thresholds['co2_low']} ppm) | 🔴 Max CO₂ ({active_thresholds['co2_high']} ppm)")

with tab6:
    st.altair_chart(create_styled_chart(df_chrono, "oxygen_pct", "Oxygen Level", "%", color="#06b6d4", min_thresh=active_thresholds["o2_low"]), use_container_width=True)
    st.caption(f"🔵 Min Oxygen Target ({active_thresholds['o2_low']}%)")


# =====================================================================
# Telemetry Table & Export
# =====================================================================
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📦 View Historical Telemetry Dataset & Download CSV"):
    display_df = df_chrono[["timestamp", "temperature", "humidity", "lux", "light_pct", "aqi", "aqi_category", "co2_ppm", "oxygen_pct", "vpd_kpa"]].iloc[::-1]
    st.dataframe(display_df, use_container_width=True)
    st.download_button(
        label="📥 Download Telemetry as CSV",
        data=display_df.to_csv(index=False).encode('utf-8'),
        file_name="greenhouse_telemetry_export.csv",
        mime="text/csv"
    )


# =====================================================================
# Auto-Refresh Control
# =====================================================================
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()