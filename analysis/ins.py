"""Simulated TOSCA spectrum from GAFF2 force constants (run with the `ins` environment).

Force constants come from md/supercell.py (kJ/mol/nm^2); detector angle and final energy per detector
from data/tosca_detectors_idf2016.csv, so nothing about the geometry is hardcoded.
"""
import csv
import io
from contextlib import redirect_stdout
from functools import reduce
from operator import add
from pathlib import Path

import numpy as np
from abinslib.almost_isotropic_incoherent import calculate_almost_isotropic_incoherent_spectra
from abinslib.displacements import Displacements
from abinslib.util import apply_weights, calculate_indirect_q2
from euphonic import Crystal, ForceConstants, QpointPhononModes, Quantity
from euphonic.util import mp_grid
from progress import NoBar  # md/progress.py; md/ must be on sys.path
from resins import Instrument
from second_order import combination_spectra

KJMOL_NM2_TO_MEV_A2 = 10.364269656 / 100  # 1 kJ/mol = 10.3643 meV, 1 nm^2 = 100 A^2


def phonon_modes(fc_path, q_mesh):
    """Euphonic phonon modes on a Monkhorst-Pack mesh from a force-constant file (md/supercell.py format)."""
    data = np.load(fc_path)
    crystal = Crystal(
        Quantity(data["unit_cell_nm"] * 10, "angstrom"), data["frac_positions"], data["symbols"],
        Quantity(data["masses_amu"], "amu"),
    )
    constants = ForceConstants(
        crystal, Quantity(data["fc"] * KJMOL_NM2_TO_MEV_A2, "meV / angstrom**2"), data["sc_matrix"], data["origins"],
    )
    modes = constants.calculate_qpoint_phonon_modes(mp_grid(q_mesh))
    # abinslib gives modes below 10 cm^-1 zero intensity, but a frequency of exactly 0 still yields 0 * inf = NaN
    # in the Bose factor; lifting them to the threshold keeps the zero intensity and avoids the NaN
    floor = Quantity(10.0, "1/cm").to("meV", "spectroscopy")
    frequencies = np.maximum(modes.frequencies.to("meV").magnitude, floor.magnitude)
    return QpointPhononModes(modes.crystal, modes.qpts, Quantity(frequencies, "meV"), modes.eigenvectors, modes.weights)


def _detectors(path, bank, expected):
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["bank"] == bank]
    if len(rows) != expected:
        raise ValueError(f"bank {bank}: expected {expected} detectors, found {len(rows)}")
    return [(float(r["two_theta_deg"]), float(r["efixed_mev"])) for r in rows]


def _qpoint(modes, index):
    """The single q-point `index` of `modes`, keeping its weight."""
    s = slice(index, index + 1)
    return QpointPhononModes(modes.crystal, modes.qpts[s], modes.frequencies[s], modes.eigenvectors[s], modes.weights[s])


def _qpoint_displacements(displacements, index):
    s = slice(index, index + 1)
    return Displacements(displacements=displacements.displacements[s], weights=displacements.weights[s],
                         bose_n=displacements.bose_n[s], temperature=displacements.temperature)


SAFETY_MARGIN = 2.0  # measured peak / estimate was 1.56 for 450 atoms and 4 q-points (margin test)


def estimate_peak_bytes(n_atoms, n_q):
    """Peak memory of simulate_tosca in bytes: eigenvectors, three displacement-sized arrays, one second-order block."""
    modes = 3 * n_atoms
    eigenvectors = n_q * modes * modes * 16  # complex128, (q, modes, atoms, 3)
    displacements = 3 * n_q * modes * n_atoms * 9 * 8  # (q, modes, atoms, 3, 3) float64, three alive at once
    second_order_block = 6 * modes * modes * 8
    return eigenvectors + displacements + second_order_block


def _cgroup_headroom(group):
    """Bytes a cgroup v2 directory may still allocate, or None without a limit.

    memory.current includes file cache that the kernel reclaims on demand, so inactive_file counts as free.
    """
    cap = (group / "memory.max").read_text().strip()
    if cap == "max":
        return None
    inactive = next(int(line.split()[1]) for line in (group / "memory.stat").read_text().splitlines()
                    if line.startswith("inactive_file "))
    return int(cap) - int((group / "memory.current").read_text()) + inactive


def available_bytes():
    """Memory this process may still use: MemAvailable, and the headroom of every cgroup it belongs to."""
    with open("/proc/meminfo") as f:
        limit = next(int(line.split()[1]) for line in f if line.startswith("MemAvailable")) * 1024
    with open("/proc/self/cgroup") as f:
        path = Path("/sys/fs/cgroup") / f.read().strip().split("::")[-1].lstrip("/")
    for group in (path, *path.parents):
        try:
            headroom = _cgroup_headroom(group)
        except (OSError, ValueError, StopIteration):
            headroom = None  # no cgroup v2 memory controller at this level
        if headroom is not None:
            limit = min(limit, headroom)
        if group == Path("/sys/fs/cgroup"):
            break
    return limit


def simulate_tosca(fc_path, detectors_csv, energy_edges_mev, bank="back", temperature_K=10.0, q_mesh=(2, 2, 1),
                   expected_detectors=70, bar=NoBar, max_memory_bytes=None, orders=(1, 2)):
    """Energy-bin centres (meV) and the TOSCA-broadened intensity per meV of one bank.

    TOSCA data are summed over the detectors of a bank during reduction, so the bank is simulated once, with its
    mean scattering angle and mean final energy (from the detector table), not detector by detector.

    energy_edges_mev must be uniform. Orders 1 (abinslib) and 2 (analysis/second_order.py, one atom at a time:
    abinslib's version needs several arrays of modes^2 x atoms), neutron cross sections applied, resolution
    `AbINS_v1` from resins. The scale is arbitrary.

    orders selects the phonon orders summed into the result, (1,), (2,) or (1, 2); the broadened parts add up to the
    full spectrum.

    Raises MemoryError before any heavy work when SAFETY_MARGIN x estimate_peak_bytes exceeds max_memory_bytes (default:
    available_bytes()).

    bar(total, title) is a context manager with update(increment, subtitle=...), as in md/run.py (for example
    lambda total, title: mo.status.progress_bar(total=total, title=title)); it advances 2 + [first order] + [n_q for second order] + 1 times (4 + n_q for the default).
    """
    if not orders or not set(orders) <= {1, 2}:
        raise ValueError(f"orders must be a non-empty subset of (1, 2), got {orders}")
    detectors = _detectors(detectors_csv, bank, expected_detectors)
    edges = np.asarray(energy_edges_mev, dtype=float)
    width = np.diff(edges)
    if not np.allclose(width, width[0]):
        raise ValueError("energy_edges_mev must be uniform")
    n_atoms, n_mesh = len(np.load(fc_path)["symbols"]), len(mp_grid(q_mesh))
    needed, limit = SAFETY_MARGIN * estimate_peak_bytes(n_atoms, n_mesh), available_bytes() if max_memory_bytes is None else max_memory_bytes
    if needed > limit:
        raise MemoryError(f"estimated {needed / 1e9:.2f} GB (with margin) exceeds the {limit / 1e9:.2f} GB available")
    bins = Quantity(edges, "meV")
    centres = (bins[1:] + bins[:-1]) / 2
    angle = np.radians(np.mean([t for t, _ in detectors]))
    final = Quantity(float(np.mean([e for _, e in detectors])), "meV")

    modes = phonon_modes(fc_path, q_mesh)
    n_q = len(modes.qpts)
    steps = 2 + (1 in orders) + n_q * (2 in orders) + 1
    with bar(steps, "INS simulation") as progress:
        progress.update(1, subtitle=f"phonon modes ({n_q} q-points)")
        displacements = Displacements.from_modes(modes, temperature=Quantity(temperature_K, "kelvin"))
        atomic = displacements.to_atomic_displacements()
        progress.update(1, subtitle="displacements")
        parts = []
        if 1 in orders:
            mode_q2 = calculate_indirect_q2(modes.frequencies, angle, final)
            parts.append(calculate_almost_isotropic_incoherent_spectra(modes, displacements, atomic, mode_q2, bins))
            progress.update(1, subtitle="first order")
        if 2 in orders:
            binned_q2 = calculate_indirect_q2(centres, angle, final)
            second = None
            for q in range(n_q):
                part = combination_spectra(_qpoint(modes, q), _qpoint_displacements(displacements, q), atomic, binned_q2, bins)
                if second is None:
                    second = part
                else:
                    second.y_data += part.y_data
                progress.update(1, subtitle=f"second order, q-point {q + 1}/{n_q}")
            parts.append(second)
        with redirect_stdout(io.StringIO()):  # euphonic prints one "Found reference data" line per atom here
            weighted = apply_weights(reduce(add, parts), key="scattering_cross_section")
        energy = centres.to("meV").magnitude
        resolution = Instrument.from_default("TOSCA").get_resolution_function("AbINS_v1")
        broadened = resolution.broaden(points=energy[:, None], data=weighted.sum().y_data.magnitude, mesh=energy)
        progress.update(1, subtitle="resolution broadening")
    return energy, broadened
