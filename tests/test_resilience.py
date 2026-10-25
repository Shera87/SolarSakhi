
import unittest

from src.energy_manager import manage_energy
from src.resilience import (
    simulate_monsoon,
    calculate_batch_priority,
    calculate_prediction_metrics,
)


class TestSolarSakhiImprovements(unittest.TestCase):

    def test_energy_manager_returns_valid_battery_level(self):
        result = manage_energy(
            solar_power=500,
            cooling_power=250,
            battery_level=50,
            pcm_level=50,
        )

        self.assertGreaterEqual(result["battery_level_after"], 0)
        self.assertLessEqual(result["battery_level_after"], 100)
        self.assertIn("power_status", result)

    def test_energy_manager_rejects_invalid_efficiency(self):
        with self.assertRaises(ValueError):
            manage_energy(
                solar_power=500,
                cooling_power=250,
                battery_level=50,
                pcm_level=50,
                solar_efficiency=1.5,
            )

    def test_energy_manager_detects_energy_shortage(self):
        result = manage_energy(
            solar_power=0,
            cooling_power=500,
            battery_level=10,
            pcm_level=50,
            battery_capacity_wh=1000,
        )

        self.assertGreater(result["energy_shortage_wh"], 0)

    def test_monsoon_simulation_returns_requested_days(self):
        result = simulate_monsoon(
            solar_power_w=500,
            cooling_load_w=200,
            battery_percent=80,
            battery_capacity_wh=2000,
            solar_drop_percent=60,
            cooling_increase_percent=20,
            days=3,
        )

        self.assertEqual(len(result["days"]), 3)
        self.assertIn("daily_solar_wh", result)
        self.assertIn("daily_load_wh", result)
        self.assertIn("shortage_during_scenario", result)

    def test_batch_priority_score_is_in_range(self):
        result = calculate_batch_priority(
            current_temp=15,
            target_min=2,
            target_max=6,
            storage_hours=24,
            quantity_kg=50,
        )

        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertIn(result["priority"], ["LOW", "MEDIUM", "HIGH"])

    def test_prediction_metrics_are_calculated(self):
        result = calculate_prediction_metrics(
            actual=[10, 12, 14],
            predicted=[11, 11, 15],
        )

        self.assertAlmostEqual(result["mae"], 1.0)
        self.assertAlmostEqual(result["rmse"], 1.0)
        self.assertEqual(result["count"], 3)


if __name__ == "__main__":
    unittest.main()
