import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[3] / "analysis"))
sys.path.insert(0, str(Path(__file__).parents[3] / "md"))
from ins import SAFETY_MARGIN, _cgroup_headroom, available_bytes, estimate_peak_bytes, phonon_modes, simulate_tosca  # noqa: E402
from abinslib.almost_isotropic_incoherent import (  # noqa: E402
    calculate_almost_isotropic_incoherent_spectra,
    mantid_like_combination_spectra,
)
from abinslib.displacements import Displacements  # noqa: E402
from abinslib.util import apply_weights, calculate_indirect_q2  # noqa: E402
from euphonic import Quantity  # noqa: E402
from resins import Instrument  # noqa: E402

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


class RecordingBar:
    """Same shape as mo.status.progress_bar; the class collects what the simulation reports."""

    created = []
    updates = []

    def __init__(self, total, title):
        RecordingBar.created.append((total, title))
        RecordingBar.updates = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, increment=1, title=None, subtitle=None):
        RecordingBar.updates.append((increment, subtitle))


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

    def run_sim_orders(self, rows, orders):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, rows)
        return simulate_tosca(self.fc, detectors, EDGES, q_mesh=(1, 1, 1), expected_detectors=len(rows), orders=orders)

    def run_sim(self, rows, edges=EDGES, expected_detectors=None):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, rows)
        return simulate_tosca(self.fc, detectors, edges, q_mesh=(1, 1, 1), expected_detectors=expected_detectors or len(rows))

    def test_bank_is_collapsed_to_its_mean_geometry(self):
        rows = [(135.0, 3.3), (128.0, 4.1)]
        _, collapsed = self.run_sim(rows)
        _, mean = self.run_sim([(131.5, 3.7)], expected_detectors=1)
        np.testing.assert_allclose(collapsed, mean, rtol=1e-9)
        _, first = self.run_sim(rows[:1])
        self.assertGreater(np.abs(collapsed - first).max(), 1e-6 * np.abs(first).max())

    def test_intensity_is_finite_with_bins_starting_at_zero_energy(self):
        energy, y = self.run_sim([(135.0, 3.3)])
        self.assertEqual(energy.shape, y.shape)
        self.assertTrue(np.isfinite(y).all())
        self.assertGreater(y.max(), 0.0)

    def test_modes_below_the_threshold_carry_no_intensity(self):
        energy, y = self.run_sim([(135.0, 3.3)])
        self.assertLess(y[energy < 40.0].max(), 1e-3 * y.max())  # the dimer has one internal mode, at 48 meV

    def test_one_qpoint_at_a_time_equals_all_qpoints_at_once(self):
        mesh, two_theta, efixed = (2, 2, 2), 135.0, 3.3
        modes = phonon_modes(self.fc, mesh)
        self.assertGreater(len(modes.qpts), 1)
        displacements = Displacements.from_modes(modes, temperature=Quantity(10.0, "kelvin"))
        angle, final = np.radians(two_theta), Quantity(efixed, "meV")
        bins = Quantity(EDGES, "meV")
        centres = (bins[1:] + bins[:-1]) / 2
        first = calculate_almost_isotropic_incoherent_spectra(
            modes, displacements, displacements.to_atomic_displacements(),
            calculate_indirect_q2(modes.frequencies, angle, final), bins)
        second = mantid_like_combination_spectra(
            modes, displacements, displacements.to_atomic_displacements(),
            calculate_indirect_q2(centres, angle, final), bins)
        raw = apply_weights(first + second, key="scattering_cross_section").sum().y_data.magnitude
        energy = centres.to("meV").magnitude
        expected = Instrument.from_default("TOSCA").get_resolution_function("AbINS_v1").broaden(
            points=energy[:, None], data=raw, mesh=energy)
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(two_theta, efixed)])
        _, got = simulate_tosca(self.fc, detectors, EDGES, q_mesh=mesh, expected_detectors=1)
        np.testing.assert_allclose(got, expected, rtol=1e-9, atol=1e-12 * np.abs(expected).max())

    def test_bar_has_one_step_per_stage(self):
        RecordingBar.created = []
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)])
        simulate_tosca(self.fc, detectors, EDGES, q_mesh=(2, 2, 2), expected_detectors=1, bar=RecordingBar)
        n_q = len(phonon_modes(self.fc, (2, 2, 2)).qpts)
        total = 4 + n_q  # modes, displacements, first order, second order per q-point, broadening
        self.assertEqual(len(RecordingBar.created), 1)
        self.assertEqual(RecordingBar.created[0][0], total)
        self.assertEqual(len(RecordingBar.updates), total)
        self.assertTrue(all(inc == 1 and isinstance(label, str) and label for inc, label in RecordingBar.updates))

    def test_orders_add_up_to_the_full_spectrum(self):
        rows = [(135.0, 3.3)]
        _, both = self.run_sim(rows)
        _, first = self.run_sim_orders(rows, (1,))
        _, second = self.run_sim_orders(rows, (2,))
        self.assertGreater(np.abs(second).max(), 0.0)
        np.testing.assert_allclose(first + second, both, rtol=1e-9, atol=1e-12 * np.abs(both).max())

    def test_bar_steps_follow_the_requested_orders(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)])
        n_q = len(phonon_modes(self.fc, (2, 2, 2)).qpts)
        for orders, total in (((1,), 4), ((2,), 3 + n_q), ((1, 2), 4 + n_q)):
            RecordingBar.created = []
            simulate_tosca(self.fc, detectors, EDGES, q_mesh=(2, 2, 2), expected_detectors=1, bar=RecordingBar, orders=orders)
            self.assertEqual(RecordingBar.created[0][0], total)
            self.assertEqual(len(RecordingBar.updates), total)

    def test_invalid_orders_raise(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)])
        for orders in ((), (3,), (0, 1)):
            with self.assertRaises(ValueError):
                simulate_tosca(self.fc, detectors, EDGES, q_mesh=(1, 1, 1), expected_detectors=1, orders=orders)

    def test_simulation_prints_nothing_to_stdout(self):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            self.run_sim([(135.0, 3.3)])
        self.assertEqual(printed.getvalue(), "")  # euphonic prints one 'Found reference data' line per atom

    def test_unknown_bank_raises(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)])
        with self.assertRaises(ValueError):
            simulate_tosca(self.fc, detectors, EDGES, bank="middle", q_mesh=(1, 1, 1), expected_detectors=1)

    def test_estimate_for_the_real_system_is_the_sum_of_its_arrays(self):
        # 450 atoms, 1350 modes, 4 q-points: eigenvectors 4 x 1350^2 x 16 B = 116.64 MB, three displacement arrays
        # 3 x 4 x 1350 x 450 x 72 B = 524.88 MB, one second-order block 6 x 1350^2 x 8 B = 87.48 MB
        self.assertEqual(estimate_peak_bytes(n_atoms=450, n_q=4), 729_000_000)

    def test_margin_covers_the_measured_peak_of_the_real_run(self):
        measured_peak = 1.14e9  # bytes, ru_maxrss of the 450-atom, 4 q-point run, LOG.md 2026-11-07
        self.assertGreaterEqual(SAFETY_MARGIN * estimate_peak_bytes(n_atoms=450, n_q=4), measured_peak)

    def test_refuses_to_start_when_the_estimate_exceeds_the_memory_limit(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)])
        with self.assertRaises(MemoryError):
            simulate_tosca(self.fc, detectors, EDGES, q_mesh=(1, 1, 1), expected_detectors=1, max_memory_bytes=1000)

    def test_cgroup_headroom_counts_reclaimable_file_cache_as_free(self):
        group = self.dir / "cg"
        group.mkdir()
        (group / "memory.max").write_text("1000\n")
        (group / "memory.current").write_text("900\n")
        (group / "memory.stat").write_text("anon 500\nfile 400\ninactive_file 300\nactive_file 100\n")
        self.assertEqual(_cgroup_headroom(group), 1000 - 900 + 300)  # the kernel reclaims inactive file pages on demand

    def test_cgroup_headroom_is_none_without_a_limit(self):
        group = self.dir / "cg"
        group.mkdir()
        (group / "memory.max").write_text("max\n")
        self.assertIsNone(_cgroup_headroom(group))

    def test_available_memory_is_positive_and_below_the_machine_total(self):
        total = int(next(line.split()[1] for line in open("/proc/meminfo") if line.startswith("MemTotal"))) * 1024
        self.assertGreater(available_bytes(), 0)
        self.assertLessEqual(available_bytes(), total)

    def test_wrong_detector_count_raises(self):
        detectors = self.dir / "d.csv"
        write_detectors(detectors, [(135.0, 3.3)] * 69)
        with self.assertRaises(ValueError):
            simulate_tosca(self.fc, detectors, EDGES, q_mesh=(1, 1, 1))


if __name__ == "__main__":
    unittest.main()
