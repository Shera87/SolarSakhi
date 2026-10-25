
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

    def next_reading(self, cooling_on=False, timestep_hours=0.25):
        if timestep_hours <= 0:
            raise ValueError("timestep_hours must be positive")

        ambient_temp = self.rng.uniform(26, 38)
        humidity = self.rng.uniform(45, 90)
        solar_power = max(0.0, self.rng.gauss(450, 180))

        
        # Simplified illustrative thermal simulation.
        heat_gain = 0.08 * max(0.0, ambient_temp - self.current_temp) * timestep_hours
        cooling_effect = 1.5 * timestep_hours if cooling_on else 0.0
        pcm_effect = 0.15 * timestep_hours if self.pcm_level > 20 else 0.0
        noise = self.rng.uniform(-0.02, 0.02)

        self.current_temp += heat_gain - cooling_effect - pcm_effect + noise
        self.current_temp = max(0.0, min(40.0, self.current_temp))


        return SensorReading(
            ambient_temp=round(ambient_temp, 2),
            humidity=round(humidity, 2),
            current_temp=round(self.current_temp, 2),
            solar_power=round(solar_power, 2),
            battery_level=round(self.battery_level, 2),
            pcm_level=round(self.pcm_level, 2),
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
