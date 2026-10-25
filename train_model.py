
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

DATA_PATH = DATA_DIR / "cold_storage_data.csv"
MODEL_PATH = MODEL_DIR / "temperature_model.joblib"

def create_dataset(rows=3000):
    rng = np.random.default_rng(42)

    ambient_temp = rng.uniform(20, 42, rows)
    humidity = rng.uniform(30, 95, rows)
    current_temp = rng.uniform(2, 18, rows)
    solar_power = rng.uniform(0, 1000, rows)
    battery_level = rng.uniform(10, 100, rows)
    pcm_level = rng.uniform(0, 100, rows)
    cooling_on = rng.integers(0, 2, rows)

    # Synthetic teaching data, not measurements from real equipment.
    next_temp = (
        current_temp
        + 0.055 * (ambient_temp - current_temp)
        + 0.012 * (humidity - 60)
        - 1.1 * cooling_on
        - 0.004 * pcm_level
        + rng.normal(0, 0.35, rows)
    )

    return pd.DataFrame({
        "ambient_temp": ambient_temp,
        "humidity": humidity,
        "current_temp": current_temp,
        "solar_power": solar_power,
        "battery_level": battery_level,
        "pcm_level": pcm_level,
        "cooling_on": cooling_on,
        "next_temp": next_temp,
    })

def main():
    df = create_dataset()
    df.to_csv(DATA_PATH, index=False)

    features = [
        "ambient_temp",
        "humidity",
        "current_temp",
        "solar_power",
        "battery_level",
        "pcm_level",
        "cooling_on",
    ]

    X = df[features]
    y = df["next_temp"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    joblib.dump({"model": model, "features": features}, MODEL_PATH)

    print("SolarSakhi model trained and saved!")
    print(f"Dataset: {DATA_PATH}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Test MAE: {mae:.2f} °C")
    print(f"Test R²: {r2:.3f}")
    print("Note: These metrics use synthetic data only.")

if __name__ == "__main__":
    main()
