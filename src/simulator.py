from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class SensorReading:
    ambient_temp: float
    humidity: float
    current_temp: float
    solar_power: float
    battery_level: float
    pcm_level: float
    timestamp: str
    simulated: bool = True


class ColdStorageSimulator:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.current_temp = 8.0
        self.battery_level = 70.0
        self.pcm_level = 45.0

    def next_reading(self, cooling_on=False):
        ambient_temp = self.rng.uniform(26, 38)
        humidity = self.rng.uniform(45, 90)
        solar_power = max(0, self.rng.gauss(450, 220))

        # Simulated solar energy available for cooling.
        usable_solar = solar_power * 0.90
        cooling_power = 250 if cooling_on else 0

        # Solar power supplies cooling first.
        solar_to_cooling = min(usable_solar, cooling_power)
        remaining_cooling = cooling_power - solar_to_cooling

        # Battery supplies any remaining cooling demand.
        if remaining_cooling > 0:
            battery_drop = remaining_cooling / 2000 * 100 * 0.25
            self.battery_level = max(
                0, self.battery_level - battery_drop
            )

        # Charge battery using surplus solar power.
        surplus_solar = max(0, usable_solar - solar_to_cooling)
        if surplus_solar > 0:
            battery_gain = surplus_solar / 2000 * 100 * 0.25
            self.battery_level = min(
                100, self.battery_level + battery_gain
            )

        # PCM charges when solar power is available.
        if cooling_on and usable_solar > cooling_power:
            self.pcm_level = min(100, self.pcm_level + 0.5)
        elif cooling_on and self.battery_level < 20:
            self.pcm_level = max(0, self.pcm_level - 1.0)
        elif not cooling_on:
            self.pcm_level = max(0, self.pcm_level - 0.2)

        # Simplified temperature dynamics for demonstration.
        heat_gain = 0.04 * (ambient_temp - self.current_temp)
        cooling_effect = 0.8 if cooling_on else 0.0
        pcm_effect = 0.12 if self.pcm_level > 20 else 0.0
        noise = self.rng.uniform(-0.08, 0.08)

        self.current_temp += (
            heat_gain - cooling_effect - pcm_effect + noise
        )

        self.current_temp = max(0, min(30, self.current_temp))

        return SensorReading(
            ambient_temp=round(ambient_temp, 2),
            humidity=round(humidity, 2),
            current_temp=round(self.current_temp, 2),
            solar_power=round(solar_power, 2),
            battery_level=round(self.battery_level, 2),
            pcm_level=round(self.pcm_level, 2),
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )