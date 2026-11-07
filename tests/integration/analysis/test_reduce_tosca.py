"""Run with: pixi run test-integration-mantid (about 1 min)."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
from reduce_tosca import reduce_run, write_csv  # noqa: E402

DATA = Path(__file__).parents[3] / "data" / "zeppelin-experimental-data"


class TestReduceTosca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = reduce_run(DATA / "TSC25990.nxs")

    def test_axes_and_shapes(self):
        e, y = self.r["energy_meV"], self.r["banks"]
        self.assertEqual(y.shape, (2, len(e)))
        self.assertEqual(self.r["errors"].shape, y.shape)
        self.assertTrue(np.all(np.diff(e) > 0))
        self.assertTrue(np.isfinite(y).all() and np.isfinite(self.r["errors"]).all())
        self.assertAlmostEqual(e[0], -2.5 + 0.0075, places=3)  # bin centre of the first bin
        self.assertLess(e[-1], 1000)

    def test_bank_scale_factors_are_close_to_one(self):
        self.assertEqual(len(self.r["scale_factors"]), 2)
        for s in self.r["scale_factors"]:
            self.assertTrue(0.9 < s < 1.1)

    def test_title_names_thymol(self):
        self.assertIn("thymol", self.r["title"])

    def test_csv_round_trip(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.csv"
            write_csv(self.r, path)
            rows = np.loadtxt(path, delimiter=",", skiprows=1)
            self.assertEqual(rows.shape, (len(self.r["energy_meV"]), 5))
            np.testing.assert_allclose(rows[:, 0], self.r["energy_meV"], rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
