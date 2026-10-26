# SolarSakhi – Solar-Powered Smart Mini Cold Storage

## 1. Project Overview

SolarSakhi is a Python-based software prototype designed to support energy-aware operation of small-scale, solar-powered cold storage systems. It combines machine learning-based temperature prediction, energy simulation, and decision-support features in a single interactive dashboard.

The project focuses on exploring how changing solar power availability and cooling demand may affect storage conditions and energy availability.

## 2. Problem Statement

Small-scale cold storage facilities may face unreliable electricity supply and reduced solar energy availability during cloudy or monsoon conditions. These challenges can affect temperature control and the storage of agricultural produce.

SolarSakhi provides a simulation-based dashboard to explore temperature trends, estimate energy availability, and prioritize produce batches for review when energy is limited.

## 3. Objectives

- Predict temperature using a machine learning model.
- Simulate solar power, battery availability, and cooling demand.
- Explore energy-shortage scenarios during monsoon conditions.
- Calculate an illustrative priority score for produce batches.
- Display monitoring information, charts, and preliminary prediction error metrics.
- Support energy-aware planning through an interactive dashboard.

## 4. Key Features

### ML-Based Temperature Prediction
Uses a trained machine learning model to estimate temperature from the model's input features.

### Solar Energy Management
Estimates how solar energy and battery storage may support the cooling load.

### Monsoon Survival Simulator
Allows users to vary solar power reduction, cooling load increase, battery capacity, and simulation duration to explore potential energy shortages.

### Produce Batch Rescue Priority
Calculates an illustrative priority score based on temperature deviation, storage duration, and batch quantity.

### Prediction Reliability Metrics
Displays preliminary Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) by comparing sequential simulated readings.

### Interactive Dashboard
Provides temperature and energy information, charts, alerts, scenario controls, and report exports.

## 5. Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Joblib
- Matplotlib / other visualization libraries used by the application
- Unittest for automated testing
- Git and GitHub

## 6. Project Structure

```text
SolarSakhi/
├── app.py
├── src/
│   ├── simulator.py
│   ├── energy_manager.py
│   ├── cooling_controller.py
│   └── resilience.py
├── models/
│   └── temperature_model.joblib
├── data/
│   └── cold_storage_data.csv
├── tests/
│   ├── test_components.py
│   └── test_resilience.py
└── README.md
```

## 7. How to Run

1. Install Python and create a virtual environment.
2. Install the dependencies listed in the project's requirements file.
3. Activate the virtual environment.
4. Run the application:

```bash
streamlit run app.py
```

5. Open the local URL displayed in the terminal.

## 8. Testing

The project currently has 11 automated unit tests, and all 11 passed in the latest test run.

The tests cover cooling decisions, simulator behaviour, energy validation, monsoon simulation, batch priority scoring, and prediction metrics.

## 9. Limitations

- The current implementation is a software simulation, not a hardware-integrated cold storage system.
- Solar power, battery behaviour, and PCM state are estimated using simplified assumptions.
- Batch priority scores are heuristic values and do not predict actual spoilage.
- Prediction error metrics are preliminary simulation comparisons, not independent real-world model validation.
- Crop temperature ranges are demonstration targets and must be verified against authoritative, crop-specific handling guidance before practical use.
- Real sensor integration and field testing have not yet been completed.

## 10. Future Enhancements

- Integrate ESP32 and temperature/humidity sensors.
- Use real solar and battery measurements.
- Improve battery backup and thermal modelling.
- Add notifications for temperature and energy alerts.
- Validate the prediction model using independent, real-world data.

## 11. Live Demo

Streamlit App: https://solarsakhi-rgrugopafjwgrlh4rlyedn.streamlit.app/

GitHub Repository: https://github.com/Shera87/SolarSakhi

## 12. Conclusion

SolarSakhi demonstrates how machine learning, solar energy simulation, and decision-support features can be combined to explore the challenges of small-scale cold storage. Its interactive dashboard helps users examine possible energy-shortage scenarios and identify produce batches that may need earlier review. Hardware integration and real-world validation remain future work.