import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
from ins import phonon_modes, simulate_tosca  # noqa: E402

HBAR_MEV_PS = 0.6582119569
K = 5000.0  # kJ/mol/nm^2
EDGES = np.linspace(0.0, 600.0, 1201)  # meV, 0.5 meV wide


def write_dimer(path):
    """O-H dimer along x in a 1 nm cubic cell, one cell, bond force constant K (kJ/mol/nm^2)."""
    fc = np.zeros((1, 6, 6))
    fc[0, 0, 0] = fc[0, 3, 3] = K
    fc[0, 0, 3] = fc[0, 3, 0] = -K
    np.savez(
        path, fc=fc, origins=np.zeros((1, 3), dtype=int), sc_matrix=np.eye(3, dtype=int),
        unit_cell_nm=np.eye(3), frac_positions=np.array([[0.1, 0.5, 0.5], [0.2, 0.5, 0.5]]),
        symbols=np.array(["O", "H"]), masses_amu=np.array([16.0, 1.0]),
    )


def write_detectors(path, rows):
    path.write_text("bank,two_theta_deg,efixed_mev\n" + "".join(f"back,{t},{e}\n" for t, e in rows))


class TestIns(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.dir = Path(self._dir.name)
        self.fc = self.dir / "fc.npz"
        write_dimer(self.fc)

    def tearDown(self):
        self._dir.cleanup()

    def test_gamma_frequency_of_dimer_matches_analytic(self):
        modes = phonon_modes(self.fc, (1, 1, 1))
        expected = HBAR_MEV_PS * np.sqrt(K / (16.0 / 17.0))
        self.assertAlmostEqual(modes.frequencies.to("meV").magnitude[0].max(), expected, delta=0.02)

    def run_sim(self, rows, edges=EDGES, expected_detectors=None):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, rows)
        return simulate_tosca(self.fc, detectors, edges, q_mesh=(1, 1, 1), expected_detectors=expected_detectors or len(rows))

    def test_each_detector_uses_its_own_angle_and_efixed(self):
        rows = [(135.0, 3.3), (128.0, 4.1)]
        _, both = self.run_sim(rows)
        _, first = self.run_sim(rows[:1])
        _, second = self.run_sim(rows[1:])
        np.testing.assert_allclose(both, (first + second) / 2, rtol=1e-9)
        self.assertGreater(np.abs(first - second).max(), 1e-6 * np.abs(first).max())

    def test_intensity_is_finite_with_bins_starting_at_zero_energy(self):
        energy, y = self.run_sim([(135.0, 3.3)])
        self.assertEqual(energy.shape, y.shape)
        self.assertTrue(np.isfinite(y).all())
        self.assertGreater(y.max(), 0.0)

    def test_modes_below_the_threshold_carry_no_intensity(self):
        energy, y = self.run_sim([(135.0, 3.3)])
        self.assertLess(y[energy < 40.0].max(), 1e-3 * y.max())  # the dimer has one internal mode, at 48 meV

    def test_wrong_detector_count_raises(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)] * 69)
        with self.assertRaises(ValueError):
            simulate_tosca(self.fc, detectors, EDGES, q_mesh=(1, 1, 1))


if __name__ == "__main__":
    unittest.main()
