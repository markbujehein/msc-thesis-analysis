import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
from compare import bin_integral, edges_from_centres, fit_scale, write_overlay  # noqa: E402


class TestCompare(unittest.TestCase):
    def test_bin_integral_of_constant(self):
        energy = np.linspace(0.0, 1.0, 1001)
        result = bin_integral(energy, np.full_like(energy, 3.0), np.array([0.1, 0.2, 0.4]))
        np.testing.assert_allclose(result, [3.0, 3.0], rtol=1e-9)

    def test_bin_integral_of_line_is_the_bin_midpoint(self):
        energy = np.linspace(0.0, 1.0, 1001)
        result = bin_integral(energy, energy, np.array([0.1, 0.2, 0.4]))
        np.testing.assert_allclose(result, [0.15, 0.3], rtol=1e-4)

    def test_fit_scale_recovers_known_factor(self):
        model = np.array([1.0, 4.0, 2.0, 0.5])
        self.assertAlmostEqual(fit_scale(model, 2.5 * model, np.array([0.1, 0.2, 0.3, 0.4])), 2.5, places=9)

    def test_edges_from_centres_log_bins(self):
        np.testing.assert_allclose(edges_from_centres(np.array([1.0, 2.0, 4.0])), [0.5, 1.5, 3.0, 5.0])

    def test_overlay_csv_round_trip(self):
        energy = np.array([1.0, 2.0])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "o.csv"
            write_overlay(path, energy, np.array([0.1, 0.2]), np.array([1.0, 2.0]), np.array([0.5, 0.5]))
            lines = path.read_text().splitlines()
        self.assertEqual(lines[0], "energy_meV,model,data,error")
        self.assertEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
