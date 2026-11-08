import sys
import tempfile
import tracemalloc
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
sys.path.insert(0, str(Path(__file__).parents[3] / "md"))
from abinslib.almost_isotropic_incoherent import mantid_like_combination_spectra  # noqa: E402
from abinslib.displacements import Displacements  # noqa: E402
from abinslib.util import calculate_indirect_q2  # noqa: E402
from euphonic import QpointPhononModes, Quantity  # noqa: E402
from ins import phonon_modes  # noqa: E402
from second_order import combination_spectra  # noqa: E402

SYMBOLS = ["O", "H", "C"]
MASSES = [16.0, 1.0, 12.0]


def write_spring_network(path, n_atoms, seed=1):
    """One cell of n_atoms joined pairwise by springs in random directions: three zero modes at Gamma, no other."""
    rng = np.random.default_rng(seed)
    fc = np.zeros((1, 3 * n_atoms, 3 * n_atoms))
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            d = rng.normal(size=3)
            block = rng.uniform(1000.0, 5000.0) * np.outer(d, d) / (d @ d)  # kJ/mol/nm^2
            fc[0, 3 * i:3 * i + 3, 3 * i:3 * i + 3] += block
            fc[0, 3 * j:3 * j + 3, 3 * j:3 * j + 3] += block
            fc[0, 3 * i:3 * i + 3, 3 * j:3 * j + 3] -= block
            fc[0, 3 * j:3 * j + 3, 3 * i:3 * i + 3] -= block
    np.savez(
        path, fc=fc, origins=np.zeros((1, 3), dtype=int), sc_matrix=np.eye(3, dtype=int), unit_cell_nm=np.eye(3),
        frac_positions=rng.uniform(size=(n_atoms, 3)), symbols=np.array([SYMBOLS[i % 3] for i in range(n_atoms)]),
        masses_amu=np.array([MASSES[i % 3] for i in range(n_atoms)]),
    )


def inputs(path, mesh, edges, weights=None):
    modes = phonon_modes(path, mesh)
    if weights is not None:  # the force constants do not depend on q, so any weights give a valid test
        modes = QpointPhononModes(modes.crystal, modes.qpts, modes.frequencies, modes.eigenvectors, np.asarray(weights))
    displacements = Displacements.from_modes(modes, temperature=Quantity(10.0, "kelvin"))
    bins = Quantity(edges, "meV")
    centres = (bins[1:] + bins[:-1]) / 2
    q2 = calculate_indirect_q2(centres, np.radians(135.0), Quantity(3.3, "meV"))
    return modes, displacements, displacements.to_atomic_displacements(), q2, bins


class TestSecondOrder(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.fc = Path(self._dir.name) / "fc.npz"

    def tearDown(self):
        self._dir.cleanup()

    def assert_matches_abinslib(self, mesh, edges, n_atoms=3, weights=None):
        write_spring_network(self.fc, n_atoms)
        args = inputs(self.fc, mesh, edges, weights)
        expected = mantid_like_combination_spectra(*args).y_data.magnitude
        got = combination_spectra(*args).y_data.magnitude
        self.assertGreater(np.abs(expected).max(), 0.0)
        np.testing.assert_allclose(got, expected, rtol=1e-10, atol=1e-12 * np.abs(expected).max())
        return args

    def test_matches_abinslib_with_unequal_q_weights(self):
        self.assert_matches_abinslib((2, 2, 1), np.linspace(0.0, 800.0, 801), weights=[0.4, 0.3, 0.2, 0.1])

    def test_gamma_only_with_translational_modes_is_finite_and_matches(self):
        args = self.assert_matches_abinslib((1, 1, 1), np.linspace(0.0, 800.0, 801))
        floor = Quantity(10.0, "1/cm").to("meV", "spectroscopy").magnitude  # ins.phonon_modes lifts zero modes to it
        self.assertAlmostEqual(args[0].frequencies.to("meV").magnitude.min(), floor, places=6)
        self.assertTrue(np.isfinite(combination_spectra(*args).y_data.magnitude).all())

    def test_pairs_above_the_last_bin_are_dropped(self):
        write_spring_network(self.fc, 3)
        top = inputs(self.fc, (1, 1, 1), np.linspace(0.0, 800.0, 801))[0].frequencies.to("meV").magnitude.max()
        self.assert_matches_abinslib((1, 1, 1), np.linspace(0.0, 0.7 * top, 401))

    def test_peak_memory_is_far_below_the_dense_tensor(self):
        n_atoms = 40
        write_spring_network(self.fc, n_atoms)
        args = inputs(self.fc, (1, 1, 1), np.linspace(0.0, 800.0, 801))
        dense_bytes = (3 * n_atoms) ** 2 * n_atoms * 8
        bound = 3 * dense_bytes / 4  # abinslib forms at least three arrays of dense_bytes

        def peak(function):
            tracemalloc.start()
            function(*args)
            _, top = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return top

        self.assertGreater(peak(mantid_like_combination_spectra), bound)  # the bound can fail
        self.assertLess(peak(combination_spectra), bound)


if __name__ == "__main__":
    unittest.main()
