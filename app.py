
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.simulator import ColdStorageSimulator
from src.energy_manager import manage_energy
from src.cooling_controller import decide_cooling

from src.resilience import (
    CROP_PROFILES,
    simulate_monsoon,
    calculate_batch_priority,
    calculate_prediction_metrics,
)

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


    st.header("What-if Simulation")

    solar_drop = st.slider(
        "Solar power decrease (%)",
        min_value=0,
        max_value=100,
        value=30,
        step=10,
    )

    cooling_increase = st.slider(
        "Cooling load increase (%)",
        min_value=0,
        max_value=100,
        value=20,
        step=10,
    )


st.divider()

if st.button("Generate Next Reading", type="primary"):
    # First generate a measurement using the previous cooling state.
    last_cooling = (
        st.session_state.history[-1]["cooling"]
        if st.session_state.history else False
    )
    reading = st.session_state.simulator.next_reading(
        cooling_on=last_cooling,
        timestep_hours=timestep_hours,
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
        cooling_on=last_cooling,
    )

    energy = manage_energy(
        solar_power=reading.solar_power,
        cooling_power=cooling_power if decision["cooling"] else 0,
        battery_level=reading.battery_level,
        pcm_level=reading.pcm_level,
        timestep_hours=timestep_hours,
    )
    st.session_state.simulator.battery_level = energy["battery_level_after"]
    st.session_state.simulator.pcm_level = energy["pcm_level_after"]
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


st.subheader("Smart Temperature Risk Alert")

current_temp = latest["temperature"]
predicted_temp = latest["prediction"]

if (
    current_temp < target_min
    or current_temp > target_max
    or predicted_temp < target_min
    or predicted_temp > target_max
):
    risk_level = "HIGH"
    risk_message = (
        "Current or predicted temperature is outside "
        "the selected demo target range."
    )
elif (
    current_temp < target_min + 1
    or current_temp > target_max - 1
    or predicted_temp < target_min + 1
    or predicted_temp > target_max - 1
):
    risk_level = "MEDIUM"
    risk_message = (
        "Temperature is close to a demo target boundary."
    )
else:
    risk_level = "LOW"
    risk_message = (
        "Current and predicted temperatures are within "
        "the selected demo target range."
    )

st.metric("Temperature Risk Indicator", risk_level)
st.write(risk_message)
st.caption(
    "Illustrative temperature-risk indicator only. "
    "It does not predict actual food spoilage or food safety."
)


st.subheader("Solar Energy Efficiency Score")

if latest["cooling"]:
    active_cooling_load = cooling_power
    solar_coverage = (
    latest["solar_power"] / active_cooling_load * 100
)

    st.metric(
        "Solar Coverage of Cooling Load",
        f"{solar_coverage:.1f}%",
    )
    st.caption(
        "Estimated instantaneous solar-power coverage of the "
        "configured cooling load; not total system efficiency."
    )
else:
    st.info("Cooling is OFF. Solar coverage score is not applicable.")



st.subheader("Estimated Backup Runtime")

# Assumption for demonstration only; replace with a real battery
# capacity when the hardware design is known.
DEMO_BATTERY_CAPACITY_WH = 1000

if cooling_power > 0:
    stored_energy_wh = (
        DEMO_BATTERY_CAPACITY_WH * latest["battery"] / 100
    )
    backup_hours = stored_energy_wh / cooling_power

    st.metric(
        "Estimated Runtime Without Solar",
        f"{backup_hours:.2f} hours",
    )
else:
    st.info("Cooling load is unavailable for runtime estimation.")

st.caption(
    "Estimate assumes a 1,000 Wh battery and ignores inverter "
    "losses, battery limits, changing loads and other real-world factors."
)

st.subheader("What-if Scenario Results")

scenario_solar = latest["solar_power"] * (1 - solar_drop / 100)
scenario_load = cooling_power * (1 + cooling_increase / 100)

scenario_col1, scenario_col2 = st.columns(2)

scenario_col1.metric(
    "Solar Power After Change",
    f"{scenario_solar:.1f} W",
    delta=f"-{solar_drop}% solar",
)

scenario_col2.metric(
    "Cooling Load After Change",
    f"{scenario_load:.1f} W",
    delta=f"+{cooling_increase}% load",
)



if scenario_load > 0:
    scenario_coverage = scenario_solar / scenario_load * 100

    st.write(
        f"**Hypothetical solar coverage:** "
        f"{scenario_coverage:.1f}%"
    )

    st.write(
        f"**Solar power surplus:** "
        f"{max(0, scenario_solar - scenario_load):.1f} W"
    )

    if scenario_solar < scenario_load:
        st.warning(
            "Hypothetical solar power is below the cooling load. "
            "Additional energy would be needed to meet the full load."
        )
    else:
        st.success(
            "Hypothetical solar power meets or exceeds the cooling load."
        )
else:
    st.info("Cooling is OFF in the current simulation.")

history_df = pd.DataFrame(st.session_state.history)


# ---------------- ML PREDICTION RELIABILITY ----------------

st.divider()
st.header("🤖 ML Prediction Reliability")

st.caption(
    "Compare ML predictions with later simulated temperature readings. "
    "Metrics are estimates from this simulation, not real-world validation."
)

if len(st.session_state.history) >= 2:
    reliability_df = pd.DataFrame(st.session_state.history)

    # Compare each previous prediction with the next recorded temperature.
    actual_temps = reliability_df["temperature"].iloc[1:].tolist()
    predicted_temps = reliability_df["prediction"].iloc[:-1].tolist()

    try:
        metrics = calculate_prediction_metrics(
            actual=actual_temps,
            predicted=predicted_temps,
        )

        metric_col1, metric_col2, metric_col3 = st.columns(3)

        metric_col1.metric("MAE", f"{metrics['mae']:.3f} °C")
        metric_col2.metric("RMSE", f"{metrics['rmse']:.3f} °C")
        metric_col3.metric("Comparisons", metrics["count"])

        st.caption(
            "MAE = average absolute prediction error. "
            "RMSE gives larger errors more weight. "
            "This comparison assumes each prediction is intended "
            "to forecast the next recorded reading."
        )

    except ValueError as error:
        st.warning(f"Metrics could not be calculated: {error}")

else:
    st.info(
        "Generate at least 2 readings to calculate preliminary "
        "prediction error metrics."
    )



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


st.subheader("Energy and Storage Comparison")

# 1. Solar Power vs Cooling Power
st.write("1. Solar Power vs Cooling Power")

power_df = pd.DataFrame({
    "Power Type": ["Solar Power", "Cooling Power Load"],
    "Power (W)": [
        latest["solar_power"],
        cooling_power if latest["cooling"] else 0,
    ],
})

power_fig = go.Figure(go.Bar(
    x=power_df["Power Type"],
    y=power_df["Power (W)"],
    marker_color=["#F4B400", "#FF6B6B"],
    text=power_df["Power (W)"].round(1),
    textposition="outside",
))
power_fig.update_layout(
    yaxis_title="Power (W)",
    showlegend=False,
)
st.plotly_chart(power_fig, use_container_width=True)

# 2. Battery Level vs PCM State
st.write("2. Battery Level vs PCM State")

storage_df = pd.DataFrame({
    "Storage Component": ["Battery Level", "PCM State"],
    "Level (%)": [latest["battery"], latest["pcm"]],
})

storage_fig = go.Figure(go.Bar(
    x=storage_df["Storage Component"],
    y=storage_df["Level (%)"],
    marker_color=["#2ECC71", "#9B59B6"],
    text=storage_df["Level (%)"].round(1),
    textposition="outside",
))
storage_fig.update_layout(
    yaxis_title="Level (%)",
    yaxis_range=[0, 110],
    showlegend=False,
)
st.plotly_chart(storage_fig, use_container_width=True)

# 3. Crop Temperature Range
st.write("3. Crop Temperature Range")

temperature_df = pd.DataFrame({
    "Temperature Type": [
        "Minimum Target",
        "Current Temperature",
        "Predicted Temperature",
        "Maximum Target",
    ],
    "Temperature (°C)": [
        target_min,
        latest["temperature"],
        latest["prediction"],
        target_max,
    ],
})

temperature_fig = go.Figure(go.Bar(
    x=temperature_df["Temperature Type"],
    y=temperature_df["Temperature (°C)"],
    marker_color=["#3498DB", "#E67E22", "#8E44AD", "#E74C3C"],
    text=temperature_df["Temperature (°C)"].round(2),
    textposition="outside",
))
temperature_fig.update_layout(
    yaxis_title="Temperature (°C)",
    showlegend=False,
)
st.plotly_chart(temperature_fig, use_container_width=True)


st.subheader("Recent Readings")
st.dataframe(history_df.tail(20), use_container_width=True)

csv_data = history_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Simulation History (CSV)",
    data=csv_data,
    file_name="solarsakhi_simulation.csv",
    mime="text/csv",
)


st.subheader("Automatic Simulation Report")

report_solar_coverage = (
    f"{solar_coverage:.1f}%"
    if latest["cooling"] else "Not applicable (cooling OFF)"
)

report_runtime = (
    f"{backup_hours:.2f} hours"
    if cooling_power > 0 else "Unavailable"
)

report_text = f"""
SOLARSAKHI - SIMULATION REPORT
================================

Report Time: {latest['time']}
Crop Profile: {crop}

TEMPERATURE
-----------
Current Temperature: {latest['temperature']:.2f} °C
Predicted Temperature: {latest['prediction']:.2f} °C
Demo Minimum Target: {target_min:.1f} °C
Demo Maximum Target: {target_max:.1f} °C
Temperature Risk Indicator: {risk_level}
Risk Details: {risk_message}

ENERGY
------
Solar Power: {latest['solar_power']:.2f} W
Cooling Load Setting: {cooling_power} W
Cooling Recommendation: {'ON' if latest['cooling'] else 'OFF'}
Battery Level: {latest['battery']:.1f}%
PCM State: {latest['pcm']:.1f}%
Solar Coverage: {report_solar_coverage}
Estimated Backup Runtime: {report_runtime}
Energy Status: {latest['power_status']}

WHAT-IF SCENARIO
----------------
Solar Reduction: {solar_drop}%
Cooling Load Increase: {cooling_increase}%
Hypothetical Solar Power: {scenario_solar:.2f} W
Hypothetical Cooling Load: {scenario_load:.2f} W

IMPORTANT LIMITATIONS
---------------------
This is a software prototype using simulated sensor readings.
Temperature risk is not a validated food-spoilage prediction.
Runtime uses an assumed 1000 Wh battery and is approximate.
Solar coverage is not total system efficiency.
No real hardware sensor or cooling system is connected.
"""

st.download_button(
    "Download Simulation Report (TXT)",
    data=report_text,
    file_name="solarsakhi_report.txt",
    mime="text/plain",
)



if st.button("Reset Simulation"):
    st.session_state.simulator = ColdStorageSimulator()
    st.session_state.history = []
    st.rerun()


# ---------------- MONSOON SURVIVAL SIMULATOR ----------------

st.header("🌧️ Monsoon Survival Simulator")

st.caption(
    "Estimate energy availability during cloudy weather. "
    "This simplified scenario is not a weather forecast."
)

monsoon_col1, monsoon_col2 = st.columns(2)

with monsoon_col1:
    monsoon_solar_drop = st.slider(
        "Monsoon solar power reduction (%)",
        min_value=0,
        max_value=100,
        value=60,
        key="monsoon_solar_drop",
    )

    scenario_days = st.slider(
        "Simulation duration (days)",
        min_value=1,
        max_value=7,
        value=3,
        key="monsoon_days",
    )

with monsoon_col2:
    monsoon_load_increase = st.slider(
        "Monsoon cooling load increase (%)",
        min_value=0,
        max_value=100,
        value=20,
        key="monsoon_load_increase",
    )

    battery_capacity = st.number_input(
        "Assumed battery capacity (Wh)",
        min_value=1.0,
        max_value=100000.0,
        value=1000.0,
        step=100.0,
        key="monsoon_battery_capacity",
    )

try:
    # Use values from the latest simulated reading.
    latest_solar = float(latest["solar_power"])
    latest_battery = float(latest["battery"])

    # Configured cooling load used as the scenario demand.
    latest_load = float(cooling_power)

    monsoon_result = simulate_monsoon(
        solar_power_w=latest_solar,
        cooling_load_w=latest_load,
        battery_percent=latest_battery,
        battery_capacity_wh=battery_capacity,
        solar_drop_percent=monsoon_solar_drop,
        cooling_increase_percent=monsoon_load_increase,
        days=scenario_days,
    )

    st.subheader("Daily Energy Projection")

    monsoon_df = pd.DataFrame(monsoon_result["days"])

    st.dataframe(
        monsoon_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Battery and Energy Shortage")

    st.line_chart(
        monsoon_df.set_index("day")[
            ["battery_remaining_wh", "energy_shortage_wh"]
        ]
    )

    if monsoon_result["shortage_during_scenario"]:
        st.error(
            "⚠️ The simplified model estimates an energy shortage "
            "on at least one simulated day."
        )
    else:
        st.success(
            "No energy shortage estimated under these assumptions. "
            "This does not guarantee safe storage conditions."
        )

    st.write(
        f"**Estimated daily solar energy:** "
        f"{monsoon_result['daily_solar_wh']:.0f} Wh"
    )

    st.write(
        f"**Estimated daily cooling demand:** "
        f"{monsoon_result['daily_load_wh']:.0f} Wh"
    )

    st.caption(monsoon_result["assumptions"])

except (KeyError, ValueError, TypeError) as error:
    st.error(f"Could not calculate the monsoon scenario: {error}")


# ---------------- PRODUCE BATCH RESCUE PRIORITY ----------------

st.divider()
st.header("📦 Produce Batch Rescue Priority")

st.caption(
    "Compare demo batches to support decisions when energy is limited. "
    "Scores are illustrative and do not predict spoilage or food safety."
)

batch_col1, batch_col2 = st.columns(2)

with batch_col1:
    batch_name = st.text_input(
        "Batch name",
        value="Batch A",
        key="batch_name",
    )

    batch_temp = st.number_input(
        "Current batch temperature (°C)",
        min_value=-20.0,
        max_value=60.0,
        value=float(latest["temperature"]),
        step=0.5,
        key="batch_temp",
    )

    batch_storage_hours = st.number_input(
        "Time in storage (hours)",
        min_value=0.0,
        max_value=1000.0,
        value=24.0,
        step=1.0,
        key="batch_storage_hours",
    )

with batch_col2:
    batch_quantity = st.number_input(
        "Batch quantity (kg)",
        min_value=0.0,
        max_value=100000.0,
        value=50.0,
        step=5.0,
        key="batch_quantity",
    )

    batch_target_min = st.number_input(
        "Batch target minimum (°C)",
        min_value=-20.0,
        max_value=59.0,
        value=float(target_min),
        step=0.5,
        key="batch_target_min",
    )

    batch_target_max = st.number_input(
        "Batch target maximum (°C)",
        min_value=-19.0,
        max_value=60.0,
        value=float(target_max),
        step=0.5,
        key="batch_target_max",
    )

if st.button("Calculate Batch Priority", key="calculate_batch_priority"):
    try:
        batch_result = calculate_batch_priority(
            current_temp=batch_temp,
            target_min=batch_target_min,
            target_max=batch_target_max,
            storage_hours=batch_storage_hours,
            quantity_kg=batch_quantity,
        )

        st.subheader(f"Priority Result: {batch_name or 'Unnamed batch'}")

        result_col1, result_col2 = st.columns(2)

        result_col1.metric(
            "Demo Priority Score",
            f"{batch_result['score']:.1f}/100",
        )

        result_col2.metric(
            "Priority Level",
            batch_result["priority"],
        )

        st.write(batch_result["explanation"])
        st.caption(batch_result["caveat"])

        if batch_result["priority"] == "HIGH":
            st.warning(
                "Review this batch promptly against verified crop-specific "
                "handling procedures and available resources."
            )
        elif batch_result["priority"] == "MEDIUM":
            st.info(
                "Review this batch and compare it with other batches."
            )
        else:
            st.success(
                "This batch has a lower demo score than higher-scoring "
                "batches; continue normal monitoring."
            )

    except ValueError as error:
        st.error(f"Please check the batch inputs: {error}")
