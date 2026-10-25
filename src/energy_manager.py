
def manage_energy(
    solar_power,
    cooling_power,
    battery_level,
    pcm_level,
    timestep_hours=0.25,
    battery_capacity_wh=2000,
):
    """
    Simulate energy flow for the SolarSakhi software prototype.

    solar_power and cooling_power are watts.
    battery_level and pcm_level are percentages.
    This is an illustrative model, not a hardware-validated design.
    """

    if solar_power < 0 or cooling_power < 0:
        raise ValueError("Power values cannot be negative")

    if not 0 <= battery_level <= 100:
        raise ValueError("battery_level must be between 0 and 100")

    if not 0 <= pcm_level <= 100:
        raise ValueError("pcm_level must be between 0 and 100")

    if timestep_hours <= 0 or battery_capacity_wh <= 0:
        raise ValueError("Time step and battery capacity must be positive")

    # Approximate useful solar power after conversion losses.
    usable_solar = solar_power * 0.90

    # Cooling uses solar power first.
    solar_to_cooling = min(usable_solar, cooling_power)
    remaining_cooling = cooling_power - solar_to_cooling
    surplus_solar = usable_solar - solar_to_cooling

    # The battery supplies any remaining cooling load.
    battery_energy_wh = battery_capacity_wh * battery_level / 100
    battery_used_wh = min(
        battery_energy_wh,
        remaining_cooling * timestep_hours,
    )
    battery_energy_wh -= battery_used_wh

    battery_level_after = 100 * battery_energy_wh / battery_capacity_wh

    # Store surplus solar energy in the battery (simplified model).
    charge_wh = min(
        surplus_solar * timestep_hours,
        battery_capacity_wh - battery_energy_wh,
    )
    battery_energy_wh += charge_wh
    battery_level_after = 100 * battery_energy_wh / battery_capacity_wh

    if remaining_cooling > 0 and battery_used_wh < remaining_cooling * timestep_hours:
        power_status = "Insufficient energy for full cooling load"
    elif surplus_solar > 0:
        power_status = "Solar surplus available"
    else:
        power_status = "Energy balanced"

    # Simplified PCM state model:
    # PCM charges when surplus solar is available and discharges
    # slowly when cooling is needed without enough solar.
    pcm_change = 0.0

    if surplus_solar > 100:
        pcm_change = min(3.0, (surplus_solar / 1000) * 5)
    elif remaining_cooling > 0:
        pcm_change = -1.5

    pcm_level_after = max(0.0, min(100.0, pcm_level + pcm_change))

    return {
        "usable_solar_w": round(usable_solar, 1),
        "solar_to_cooling_w": round(solar_to_cooling, 1),
        "battery_level_after": round(battery_level_after, 1),
        "battery_used_wh": round(battery_used_wh, 1),
        "battery_charged_wh": round(charge_wh, 1),
        "pcm_level_after": round(pcm_level_after, 1),
        "power_status": power_status,
    }
