
def manage_energy(
    solar_power,
    cooling_power,
    battery_level,
    pcm_level,
    timestep_hours=0.25,
    battery_capacity_wh=2000,
):
    """Illustrative energy model for the SolarSakhi software prototype."""

    if solar_power < 0 or cooling_power < 0:
        raise ValueError("Power values cannot be negative")

    if not 0 <= battery_level <= 100:
        raise ValueError("battery_level must be between 0 and 100")

    if not 0 <= pcm_level <= 100:
        raise ValueError("pcm_level must be between 0 and 100")

    if timestep_hours <= 0 or battery_capacity_wh <= 0:
        raise ValueError("Time step and battery capacity must be positive")

    # Approximate solar conversion efficiency.
    usable_solar = solar_power * 0.90

    # Solar supplies the cooling load first.
    solar_to_cooling = min(usable_solar, cooling_power)
    remaining_cooling_w = cooling_power - solar_to_cooling
    surplus_solar_w = max(0.0, usable_solar - solar_to_cooling)

    # Convert battery percentage into stored energy.
    battery_energy_wh = battery_capacity_wh * battery_level / 100.0

    # Battery supplies any cooling power not covered by solar.
    required_battery_wh = remaining_cooling_w * timestep_hours
    battery_used_wh = min(battery_energy_wh, required_battery_wh)
    battery_energy_wh -= battery_used_wh

    # Charge the battery with surplus solar energy.
    charge_efficiency = 0.90
    available_capacity_wh = battery_capacity_wh - battery_energy_wh
    potential_charge_wh = surplus_solar_w * timestep_hours * charge_efficiency
    battery_charged_wh = min(available_capacity_wh, potential_charge_wh)
    battery_energy_wh += battery_charged_wh

    battery_level_after = 100.0 * battery_energy_wh / battery_capacity_wh

    if required_battery_wh > battery_used_wh:
        power_status = "Insufficient energy for full cooling load"
    elif surplus_solar_w > 0 and battery_level_after < 100:
        power_status = "Solar surplus available"
    elif surplus_solar_w > 0:
        power_status = "Battery fully charged"
    else:
        power_status = "Energy balanced"

    # Simplified PCM state estimate.
    pcm_change = 0.0

    if surplus_solar_w > 100:
        pcm_change = min(3.0, surplus_solar_w / 1000.0 * 5.0)
    elif remaining_cooling_w > 0:
        pcm_change = -1.5

    pcm_level_after = max(0.0, min(100.0, pcm_level + pcm_change))

    return {
        "usable_solar_w": round(usable_solar, 1),
        "solar_to_cooling_w": round(solar_to_cooling, 1),
        "battery_level_after": round(battery_level_after, 1),
        "battery_used_wh": round(battery_used_wh, 1),
        "battery_charged_wh": round(battery_charged_wh, 1),
        "pcm_level_after": round(pcm_level_after, 1),
        "power_status": power_status,
    }
