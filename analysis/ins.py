"""Simulated TOSCA spectrum from GAFF2 force constants (run with the `ins` environment).

Force constants come from md/supercell.py (kJ/mol/nm^2); detector angle and final energy per detector
from data/tosca_detectors.csv, so nothing about the geometry is hardcoded.
"""
import csv
from pathlib import Path

import numpy as np
from abinslib.almost_isotropic_incoherent import (
    calculate_almost_isotropic_incoherent_spectra,
    mantid_like_combination_spectra,
)
from abinslib.displacements import Displacements
from abinslib.util import apply_weights, calculate_indirect_q2
from euphonic import Crystal, ForceConstants, QpointPhononModes, Quantity
from euphonic.util import mp_grid
from resins import Instrument

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


def simulate_tosca(fc_path, detectors_csv, energy_edges_mev, bank="back", temperature_K=10.0, q_mesh=(2, 2, 1),
                   expected_detectors=70):
    """Energy-bin centres (meV) and the TOSCA-broadened intensity per meV, averaged over the bank's detectors.

    energy_edges_mev must be uniform. Orders 1 and 2 of the almost-isotropic incoherent approximation (abinslib),
    neutron cross sections applied, resolution `AbINS_v1` from resins. The scale is arbitrary.
    """
    detectors = _detectors(detectors_csv, bank, expected_detectors)
    edges = np.asarray(energy_edges_mev, dtype=float)
    width = np.diff(edges)
    if not np.allclose(width, width[0]):
        raise ValueError("energy_edges_mev must be uniform")
    bins = Quantity(edges, "meV")
    centres = (bins[1:] + bins[:-1]) / 2

    modes = phonon_modes(fc_path, q_mesh)
    displacements = Displacements.from_modes(modes, temperature=Quantity(temperature_K, "kelvin"))
    atomic = displacements.to_atomic_displacements()

    per_bin = np.zeros(len(centres))
    for two_theta_deg, efixed_mev in detectors:
        angle, final_energy = np.radians(two_theta_deg), Quantity(efixed_mev, "meV")
        mode_q2 = calculate_indirect_q2(modes.frequencies, angle, final_energy)
        binned_q2 = calculate_indirect_q2(centres, angle, final_energy)
        first = calculate_almost_isotropic_incoherent_spectra(modes, displacements, atomic, mode_q2, bins)
        second = mantid_like_combination_spectra(modes, displacements, atomic, binned_q2, bins)
        weighted = apply_weights(first + second, key="scattering_cross_section")
        per_bin += weighted.sum().y_data.magnitude
    per_bin /= len(detectors)

    energy = centres.to("meV").magnitude
    resolution = Instrument.from_default("TOSCA").get_resolution_function("AbINS_v1")
    return energy, resolution.broaden(points=energy[:, None], data=per_bin, mesh=energy)
