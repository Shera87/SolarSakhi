
"""SolarSakhi resilience and decision-support utilities.

All forecasts and scenarios are estimates, not food-safety guarantees.
"""

from math import isfinite


# Illustrative demo profiles only. Validate against authoritative,
# crop- and variety-specific guidance before practical deployment.
CROP_PROFILES = {
    "General produce demo": {
        "min_temp": 4.0, "max_temp": 10.0,
        "max_storage_hours_demo": 72,
    },
    "Tomato demo": {
        "min_temp": 10.0, "max_temp": 13.0,
        "max_storage_hours_demo": 72,
    },
    "Leafy greens demo": {
        "min_temp": 2.0, "max_temp": 6.0,
        "max_storage_hours_demo": 48,
    },
}


def validate_number(name, value, minimum=None, maximum=None):
    """Validate numeric input and optional bounds."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric.") from None

    if not isfinite(number):
        raise ValueError(f"{name} must be finite.")

    if minimum is not None and number < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")

    if maximum is not None and number > maximum:
        raise ValueError(f"{name} must be at most {maximum}.")

    return number


def simulate_monsoon(
    solar_power_w,
    cooling_load_w,
    battery_percent,
    battery_capacity_wh,
    solar_drop_percent,
    cooling_increase_percent,
    days,
    usable_battery_fraction=0.8,
):
    """Estimate daily energy balance for a hypothetical scenario.

    Assumes constant daily solar availability and cooling load.
    This is a simplified planning model, not a weather forecast.
    """
    solar = validate_number("Solar power", solar_power_w, 0)
    load = validate_number("Cooling load", cooling_load_w, 0)
    battery_pct = validate_number("Battery level", battery_percent, 0, 100)
    capacity = validate_number("Battery capacity", battery_capacity_wh, 1)
    drop = validate_number("Solar reduction", solar_drop_percent, 0, 100)
    increase = validate_number(
        "Cooling increase", cooling_increase_percent, 0, 100
    )
    days = int(validate_number("Days", days, 1, 7))
    usable = validate_number("Usable battery fraction", usable_battery_fraction, 0, 1)

    # Power (W) multiplied by assumed operating hours per day gives Wh/day.
    # 5 hours of equivalent solar generation is a demo assumption.
    solar_hours_per_day = 5.0
    cooling_hours_per_day = 24.0

    daily_solar_wh = solar * (1 - drop / 100) * solar_hours_per_day
    daily_load_wh = load * (1 + increase / 100) * cooling_hours_per_day

    available_battery_wh = capacity * battery_pct / 100 * usable
    reserve_limit_wh = capacity * usable
    rows = []
    shortage_started = False

    for day in range(1, days + 1):
        energy_before_load = min(
            reserve_limit_wh,
            available_battery_wh + daily_solar_wh,
        )
        energy_after_load = energy_before_load - daily_load_wh
        shortage_wh = max(0.0, -energy_after_load)
        available_battery_wh = max(0.0, energy_after_load)

        if shortage_wh > 0:
            shortage_started = True

        rows.append({
            "day": day,
            "solar_energy_wh": round(daily_solar_wh, 2),
            "cooling_energy_wh": round(daily_load_wh, 2),
            "battery_remaining_wh": round(available_battery_wh, 2),
            "energy_shortage_wh": round(shortage_wh, 2),
            "shortage_detected": shortage_wh > 0,
        })

    return {
        "daily_solar_wh": round(daily_solar_wh, 2),
        "daily_load_wh": round(daily_load_wh, 2),
        "days": rows,
        "shortage_during_scenario": shortage_started,
        "assumptions": (
            "Assumes 5 equivalent solar-generation hours per day, "
            "constant daily load, simplified battery accounting and "
            "no temperature-dependent load or conversion losses."
        ),
    }


def calculate_batch_priority(
    current_temp,
    target_min,
    target_max,
    storage_hours,
    quantity_kg,
):
    """Return an explainable demo priority score from 0 to 100.

    Not a spoilage, shelf-life, or food-safety prediction.
    """
    temp = validate_number("Current temperature", current_temp)
    low = validate_number("Minimum target", target_min)
    high = validate_number("Maximum target", target_max)
    hours = validate_number("Storage duration", storage_hours, 0)
    quantity = validate_number("Quantity", quantity_kg, 0)

    if low >= high:
        raise ValueError("Minimum target must be below maximum target.")

    deviation = max(low - temp, 0.0, temp - high)
    temp_score = min(60.0, deviation * 15.0)
    duration_score = min(25.0, hours / 72.0 * 25.0)
    quantity_score = min(15.0, quantity / 100.0 * 15.0)

    score = round(temp_score + duration_score + quantity_score, 1)

    if score >= 60:
        label = "HIGH"
    elif score >= 30:
        label = "MEDIUM"
    else:
        label = "LOW"

    return {
        "score": score,
        "priority": label,
        "temperature_deviation_c": round(deviation, 2),
        "explanation": (
            f"Temperature deviation: {deviation:.2f} °C; "
            f"storage duration: {hours:.1f} hours; "
            f"quantity: {quantity:.1f} kg."
        ),
        "caveat": (
            "Demo prioritisation score only. It does not estimate "
            "actual spoilage or replace crop-specific handling guidance."
        ),
    }


def calculate_prediction_metrics(actual, predicted):
    """Calculate MAE and RMSE when paired actual readings are available."""
    actual_values = list(actual)
    predicted_values = list(predicted)

    if not actual_values or len(actual_values) != len(predicted_values):
        raise ValueError("Actual and predicted values must be non-empty and equal length.")

    errors = []
    for a, p in zip(actual_values, predicted_values):
        av = validate_number("Actual temperature", a)
        pv = validate_number("Predicted temperature", p)
        errors.append(pv - av)

    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = (sum(error ** 2 for error in errors) / len(errors)) ** 0.5

    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "count": len(errors)}
