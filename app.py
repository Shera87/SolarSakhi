
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.simulator import ColdStorageSimulator
from src.energy_manager import manage_energy
from src.cooling_controller import decide_cooling

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "temperature_model.joblib"

st.set_page_config(
    page_title="SolarSakhi",
    page_icon="🌱",
    layout="wide",
)

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Saved model not found. Run: python train_model.py"
        )
    return joblib.load(MODEL_PATH)

try:
    saved = load_model()
    model = saved["model"]
    features = saved["features"]
except Exception as exc:
    st.error(f"Could not load the ML model: {exc}")
    st.stop()

if "simulator" not in st.session_state:
    st.session_state.simulator = ColdStorageSimulator()

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🌱 SolarSakhi")
st.subheader("Smart Mini Cold Storage for Agricultural Produce")
st.caption(
    "Software prototype • Simulated sensor readings • "
    "ML-based temperature forecasting"
)

with st.sidebar:
    st.header("Storage Settings")
    crop = st.selectbox(
        "Illustrative crop profile",
        ["General produce demo", "Tomato demo", "Leafy greens demo"],
    )

    # Illustrative targets for software testing only.
    # Validate crop-specific ranges before real-world use.
    targets = {
        "General produce demo": (4.0, 10.0),
        "Tomato demo": (10.0, 13.0),
        "Leafy greens demo": (2.0, 6.0),
    }
    target_min, target_max = targets[crop]

    st.write(f"Demo target: {target_min}–{target_max} °C")
    st.warning(
        "Demo ranges only. Verify safe storage requirements for "
        "the exact crop and variety before practical use."
    )

    st.header("Energy Settings")
    cooling_power = st.slider(
        "Cooling load (W)", min_value=50, max_value=600,
        value=250, step=25
    )
    timestep_hours = st.selectbox(
        "Simulation time step",
        [0.25, 0.5, 1.0],
        format_func=lambda x: f"{x:g} hour(s)",
    )

st.divider()

if st.button("Generate Next Reading", type="primary"):
    # First generate a measurement using the previous cooling state.
    last_cooling = (
        st.session_state.history[-1]["cooling"]
        if st.session_state.history else False
    )
    reading = st.session_state.simulator.next_reading(
        cooling_on=last_cooling
    )

    features_now = {
        "ambient_temp": reading.ambient_temp,
        "humidity": reading.humidity,
        "current_temp": reading.current_temp,
        "solar_power": reading.solar_power,
        "battery_level": reading.battery_level,
        "pcm_level": reading.pcm_level,
        "cooling_on": int(last_cooling),
    }

    X = pd.DataFrame([features_now], columns=features)
    prediction = float(model.predict(X)[0])

    decision = decide_cooling(
        current_temp=reading.current_temp,
        predicted_temp=prediction,
        target_min=target_min,
        target_max=target_max,
        battery_level=reading.battery_level,
        solar_power=reading.solar_power,
    )

    energy = manage_energy(
        solar_power=reading.solar_power,
        cooling_power=cooling_power if decision["cooling"] else 0,
        battery_level=reading.battery_level,
        pcm_level=reading.pcm_level,
        timestep_hours=timestep_hours,
    )

    st.session_state.history.append({
        "time": reading.timestamp,
        "ambient_temp": reading.ambient_temp,
        "humidity": reading.humidity,
        "temperature": reading.current_temp,
        "prediction": prediction,
        "solar_power": reading.solar_power,
        "battery": energy["battery_level_after"],
        "pcm": energy["pcm_level_after"],
        "cooling": decision["cooling"],
        "status": decision["status"],
        "alert": decision["alert"],
        "power_status": energy["power_status"],
    })

if not st.session_state.history:
    st.info("Click 'Generate Next Reading' to start the simulation.")
    st.stop()

latest = st.session_state.history[-1]

st.caption(f"Last simulated reading: {latest['time']}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Storage Temperature", f"{latest['temperature']:.2f} °C")
col2.metric("Predicted Temperature", f"{latest['prediction']:.2f} °C")
col3.metric("Humidity", f"{latest['humidity']:.1f}%")
col4.metric("Solar Power", f"{latest['solar_power']:.0f} W")

col5, col6, col7 = st.columns(3)
col5.metric("Battery Level (estimated)", f"{latest['battery']:.1f}%")
col6.metric("PCM State (simulated)", f"{latest['pcm']:.1f}%")
col7.metric(
    "Cooling Recommendation",
    "ON" if latest["cooling"] else "OFF",
)

st.subheader("Cooling Decision")
st.write(f"**Status:** {latest['status']}")
st.write(f"**Alert:** {latest['alert']}")
st.write(f"**Energy:** {latest['power_status']}")

history_df = pd.DataFrame(st.session_state.history)

st.subheader("Temperature Monitoring")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=history_df["time"], y=history_df["temperature"],
    mode="lines+markers", name="Simulated temperature"
))
fig.add_trace(go.Scatter(
    x=history_df["time"], y=history_df["prediction"],
    mode="lines+markers", name="ML prediction"
))
fig.add_hline(
    y=target_max, line_dash="dash",
    annotation_text="Demo upper target"
)
fig.update_layout(
    xaxis_title="Simulation reading",
    yaxis_title="Temperature (°C)",
    legend_title="Series",
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Energy Monitoring")
energy_fig = go.Figure()
energy_fig.add_trace(go.Scatter(
    x=history_df["time"], y=history_df["solar_power"],
    mode="lines+markers", name="Solar power (W)"
))
energy_fig.update_layout(
    xaxis_title="Simulation reading",
    yaxis_title="Power (W)",
)
st.plotly_chart(energy_fig, use_container_width=True)

st.subheader("Recent Readings")
st.dataframe(history_df.tail(20), use_container_width=True)

csv_data = history_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Simulation History (CSV)",
    data=csv_data,
    file_name="solarsakhi_simulation.csv",
    mime="text/csv",
)

if st.button("Reset Simulation"):
    st.session_state.simulator = ColdStorageSimulator()
    st.session_state.history = []
    st.rerun()
