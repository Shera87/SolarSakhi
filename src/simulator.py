
from dataclasses import dataclass
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
        from datetime import datetime

        ambient_temp = self.rng.uniform(26, 38)
        humidity = self.rng.uniform(45, 90)
        solar_power = max(0, self.rng.gauss(450, 220))

        # Simplified temperature dynamics for demonstration.
        heat_gain = 0.10 * (ambient_temp - self.current_temp)
        cooling_effect = 0.9 if cooling_on else 0.0
        pcm_effect = 0.08 if self.pcm_level > 20 else 0.0
        noise = self.rng.uniform(-0.25, 0.25)

        self.current_temp += (
            heat_gain - cooling_effect - pcm_effect + noise
        )
        self.current_temp = max(0, min(30, self.current_temp))

        # Simulated battery and PCM trends.
        if solar_power > 250:
            self.battery_level = min(100, self.battery_level + 0.8)
        elif cooling_on:
            self.battery_level = max(0, self.battery_level - 1.2)

        if cooling_on and solar_power > 250:
            self.pcm_level = min(100, self.pcm_level + 0.5)
        elif not cooling_on:
            self.pcm_level = max(0, self.pcm_level - 0.2)

        return SensorReading(
            ambient_temp=round(ambient_temp, 2),
            humidity=round(humidity, 2),
            current_temp=round(self.current_temp, 2),
            solar_power=round(solar_power, 2),
            battery_level=round(self.battery_level, 2),
            pcm_level=round(self.pcm_level, 2),
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
