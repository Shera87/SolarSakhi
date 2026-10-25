
import unittest

from src.simulator import ColdStorageSimulator
from src.energy_manager import manage_energy
from src.cooling_controller import decide_cooling


class TestSolarSakhi(unittest.TestCase):

    def test_simulator_returns_reading(self):
        simulator = ColdStorageSimulator(seed=42)
        reading = simulator.next_reading()

        self.assertGreaterEqual(reading.current_temp, 0)
        self.assertLessEqual(reading.current_temp, 30)
        self.assertTrue(reading.simulated)

    def test_cooling_recommended_when_too_warm(self):
        result = decide_cooling(
            current_temp=8,
            predicted_temp=10,
            target_min=4,
            target_max=9,
            battery_level=80,
            solar_power=500,
        )
        self.assertTrue(result["cooling"])

    def test_cooling_not_needed_within_range(self):
        result = decide_cooling(
            current_temp=6,
            predicted_temp=7,
            target_min=4,
            target_max=9,
            battery_level=80,
            solar_power=500,
        )
        self.assertFalse(result["cooling"])

    def test_energy_values_are_valid(self):
        result = manage_energy(
            solar_power=600,
            cooling_power=250,
            battery_level=60,
            pcm_level=40,
        )
        self.assertGreaterEqual(result["battery_level_after"], 0)
        self.assertLessEqual(result["battery_level_after"], 100)
        self.assertGreaterEqual(result["pcm_level_after"], 0)
        self.assertLessEqual(result["pcm_level_after"], 100)

    def test_invalid_battery_level_is_rejected(self):
        with self.assertRaises(ValueError):
            manage_energy(
                solar_power=600,
                cooling_power=250,
                battery_level=120,
                pcm_level=40,
            )


if __name__ == "__main__":
    unittest.main()
