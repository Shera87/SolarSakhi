
"""Illustrative energy manager for the SolarSakhi software prototype."""

from math import isfinite


def manage_energy(
    solar_power,
    cooling_power,
    battery_level,
    pcm_level,
    timestep_hours=0.25,
    battery_capacity_wh=2000,
    solar_efficiency=0.90,
    charge_efficiency=0.90,
    discharge_efficiency=0.90,
    minimum_battery_reserve=0.10,
):
    """Estimate solar, battery and simplified PCM state changes.

    Efficiencies, reserve and PCM behaviour are demonstration assumptions.
    Replace them with hardware specifications before practical deployment.
    """

    values = {
        "solar_power": solar_power,
        "cooling_power": cooling_power,
        "battery_level": battery_level,
        "pcm_level": pcm_level,
        "timestep_hours": timestep_hours,
        "battery_capacity_wh": battery_capacity_wh,
        "solar_efficiency": solar_efficiency,
        "charge_efficiency": charge_efficiency,
        "discharge_efficiency": discharge_efficiency,
        "minimum_battery_reserve": minimum_battery_reserve,
    }

    for name, value in values.items():
        try:
            values[name] = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be numeric.") from None

        if not isfinite(values[name]):
            raise ValueError(f"{name} must be finite.")

    solar_power = values["solar_power"]
    cooling_power = values["cooling_power"]
    battery_level = values["battery_level"]
    pcm_level = values["pcm_level"]
    timestep_hours = values["timestep_hours"]
    battery_capacity_wh = values["battery_capacity_wh"]
    solar_efficiency = values["solar_efficiency"]
    charge_efficiency = values["charge_efficiency"]
    discharge_efficiency = values["discharge_efficiency"]
    minimum_battery_reserve = values["minimum_battery_reserve"]

    if solar_power < 0 or cooling_power < 0:
        raise ValueError("Power values cannot be negative.")

    if not 0 <= battery_level <= 100:
        raise ValueError("battery_level must be between 0 and 100.")

    if not 0 <= pcm_level <= 100:
        raise ValueError("pcm_level must be between 0 and 100.")

    if timestep_hours <= 0 or battery_capacity_wh <= 0:
        raise ValueError("Time step and battery capacity must be positive.")

    for name, efficiency in (
        ("solar_efficiency", solar_efficiency),
        ("charge_efficiency", charge_efficiency),
        ("discharge_efficiency", discharge_efficiency),
    ):
        if not 0 < efficiency <= 1:
            raise ValueError(f"{name} must be greater than 0 and at most 1.")

    if not 0 <= minimum_battery_reserve < 1:
        raise ValueError("minimum_battery_reserve must be in [0, 1).")

    # Step 1: Convert incoming solar power to usable power.
    usable_solar = solar_power * solar_efficiency

    # Step 2: Solar supplies the cooling load first.
    solar_to_cooling = min(usable_solar, cooling_power)
    remaining_cooling_w = cooling_power - solar_to_cooling
    surplus_solar_w = max(0.0, usable_solar - solar_to_cooling)

    # Step 3: Estimate battery energy and preserve the reserve.
    battery_energy_wh = battery_capacity_wh * battery_level / 100.0
    reserve_wh = battery_capacity_wh * minimum_battery_reserve

    required_battery_output_wh = remaining_cooling_w * timestep_hours
    available_battery_wh = max(0.0, battery_energy_wh - reserve_wh)

    # Energy delivered is lower than energy removed from the battery.
    battery_used_wh = min(
        available_battery_wh,
        required_battery_output_wh / discharge_efficiency,
    )

    battery_delivered_wh = battery_used_wh * discharge_efficiency
    battery_energy_wh -= battery_used_wh

    remaining_shortage_wh = max(
        0.0, required_battery_output_wh - battery_delivered_wh
    )

    # Step 4: Charge the battery from surplus solar.
    available_capacity_wh = battery_capacity_wh - battery_energy_wh
    potential_charge_wh = (
        surplus_solar_w * timestep_hours * charge_efficiency
    )

    battery_charged_wh = min(
        available_capacity_wh, potential_charge_wh
    )
    battery_energy_wh += battery_charged_wh

    battery_level_after = 100.0 * battery_energy_wh / battery_capacity_wh

    # Step 5: Keep the existing simplified PCM demonstration.
    # This is a heuristic, not a thermal-energy or temperature model.
    pcm_change = 0.0

    if surplus_solar_w > 100:
        pcm_change = min(3.0, surplus_solar_w / 1000.0 * 5.0)
    elif remaining_cooling_w > 0:
        pcm_change = -1.5

    pcm_level_after = max(
        0.0, min(100.0, pcm_level + pcm_change)
    )

    if remaining_shortage_wh > 0:
        power_status = "Insufficient energy for full cooling load"
    elif surplus_solar_w > 0 and battery_level_after < 99.9:
        power_status = "Solar surplus available"
    elif surplus_solar_w > 0:
        power_status = "Battery fully charged"
    else:
        power_status = "Energy balanced"

    return {
        "usable_solar_w": round(usable_solar, 1),
        "solar_to_cooling_w": round(solar_to_cooling, 1),
        "battery_level_after": round(battery_level_after, 1),
        "battery_used_wh": round(battery_used_wh, 2),
        "battery_delivered_wh": round(battery_delivered_wh, 2),
        "battery_charged_wh": round(battery_charged_wh, 2),
        "battery_reserve_wh": round(reserve_wh, 2),
        "energy_shortage_wh": round(remaining_shortage_wh, 2),
        "pcm_level_after": round(pcm_level_after, 1),
        "power_status": power_status,
    }
