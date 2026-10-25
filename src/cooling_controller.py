
def decide_cooling(
    current_temp,
    predicted_temp,
    target_min,
    target_max,
    battery_level,
    solar_power,
    cooling_on=False,
):
    """
    Illustrative cooling decision logic for the SolarSakhi
    software prototype. Not validated for hardware control.
    """

    if target_min >= target_max:
        raise ValueError("target_min must be lower than target_max")

    if not 0 <= battery_level <= 100:
        raise ValueError("battery_level must be between 0 and 100")

    if solar_power < 0:
        raise ValueError("solar_power cannot be negative")

    # Use separate ON/OFF thresholds to reduce rapid switching.
    hysteresis = 0.5
    turn_on_at = target_max
    turn_off_at = target_max - hysteresis

    temperature_to_check = max(current_temp, predicted_temp)

    if cooling_on:
        should_cool = temperature_to_check > turn_off_at
    else:
        should_cool = temperature_to_check >= turn_on_at

    energy_available = battery_level >= 20 or solar_power >= 150

    if should_cool and energy_available:
        return {
            "cooling": True,
            "status": "Cooling recommended",
            "reason": "Temperature is high or approaching the upper target.",
            "alert": "Temperature excursion risk",
        }

    if should_cool and not energy_available:
        return {
            "cooling": False,
            "status": "Energy shortage warning",
            "reason": "Temperature is high but available energy is limited.",
            "alert": "High temperature and low energy",
        }

    if current_temp < target_min:
        return {
            "cooling": False,
            "status": "Cooling not recommended",
            "reason": "Temperature is below the selected target range.",
            "alert": "Check temperature and crop target",
        }

    return {
        "cooling": False,
        "status": "Cooling not currently needed",
        "reason": "Temperature is within the target range.",
        "alert": "Normal",
    }
