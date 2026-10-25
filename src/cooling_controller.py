
def decide_cooling(
    current_temp,
    predicted_temp,
    target_min,
    target_max,
    battery_level,
    solar_power,
):
    """
    Return a cooling recommendation for the software prototype.
    This is decision-support logic, not a validated hardware controller.
    """

    if target_min >= target_max:
        raise ValueError("target_min must be lower than target_max")

    if not 0 <= battery_level <= 100:
        raise ValueError("battery_level must be between 0 and 100")

    if solar_power < 0:
        raise ValueError("solar_power cannot be negative")

    if current_temp > target_max or predicted_temp > target_max:
        if battery_level >= 20 or solar_power >= 150:
            return {
                "cooling": True,
                "status": "Cooling recommended",
                "reason": (
                    "Temperature is above the target or predicted "
                    "to exceed it, and energy is available."
                ),
                "alert": "Temperature excursion risk",
            }

        return {
            "cooling": False,
            "status": "Energy shortage warning",
            "reason": (
                "Temperature is high, but available energy is limited. "
                "Check the power system and protect the stored produce."
            ),
            "alert": "High temperature and low energy",
        }

    if current_temp < target_min:
        return {
            "cooling": False,
            "status": "Cooling not recommended",
            "reason": "Temperature is below the selected target range.",
            "alert": "Check temperature and crop target",
        }

    if predicted_temp >= target_max - 0.5:
        return {
            "cooling": True,
            "status": "Preventive cooling recommended",
            "reason": "Predicted temperature is approaching the upper limit.",
            "alert": "Temperature may approach the upper limit",
        }

    return {
        "cooling": False,
        "status": "Cooling not currently needed",
        "reason": "Temperature is within range and is not predicted to exceed it.",
        "alert": "Normal",
    }
