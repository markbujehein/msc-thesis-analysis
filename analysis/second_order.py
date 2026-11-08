"""Two-phonon (second-order) INS spectrum, one atom at a time (run with the `ins` environment).

abinslib's `mantid_like_combination_spectra` forms dense arrays indexed by (mode 1, mode 2, atom), several at once.
For 1350 modes and 450 atoms each is 6.56 GB. The same quantity per atom is a matrix product over mode pairs, so
only a (modes x modes) block exists at any time. Formulas as in abinslib.almost_isotropic_incoherent:
I_m(v1, v2) = (tr B_m(v1) tr B_m(v2) + 2 B_m(v1):B_m(v2)) / (15 c), c = 2 for v1 = v2 and 1 otherwise, placed at the
energy w1 + w2, then scaled by Q^4 and the Debye-Waller factor after binning.
"""
import numpy as np
from abinslib.isotropic_incoherent import calculate_isotropic_dw_factor
from abinslib.util import iter_atom_info
from euphonic import QpointPhononModes, Quantity
from euphonic.spectra import Spectrum1DCollection

from abinslib.displacements import Displacements


def combination_spectra(
    modes: QpointPhononModes, displacements: Displacements, atomic_displacements: Quantity, nominal_q2: Quantity,
    bins: Quantity,
) -> Spectrum1DCollection:
    """Same arguments and result as abinslib's `mantid_like_combination_spectra`, without the dense arrays.

    Each q-point is treated on its own and weighted by its entry in `modes.weights`. `bins` must be uniform.
    The result has one spectrum per atom, order 2.
    """
    edges = bins.magnitude
    n_bins = len(edges) - 1
    bin_width = bins[1] - bins[0]
    q4 = Quantity(1.0, "angstrom^-2").to("bohr^-2").magnitude ** 2  # nominal Q = 1 per angstrom, as in abinslib
    b = displacements.n_plus_one.to("bohr^2").magnitude  # (q, modes, atoms, 3, 3)
    frequencies = modes.frequencies.to(bins.units).magnitude
    n_modes = frequencies.shape[1]
    inverse_c = 1.0 / (15.0 * (1.0 + np.eye(n_modes)))

    y = np.zeros((modes.crystal.n_atoms, n_bins))
    for q, weight in enumerate(modes.weights):
        pair = (frequencies[q][:, None] + frequencies[q][None, :]).ravel()
        index = np.searchsorted(edges, pair, side="right") - 1
        index[pair == edges[-1]] = n_bins - 1  # np.histogram closes the last bin
        index[(index < 0) | (index >= n_bins)] = n_bins  # overflow slot for pairs outside the bins
        for atom in range(modes.crystal.n_atoms):
            tensor = b[q][:, atom].reshape(n_modes, 9)
            trace = tensor[:, 0] + tensor[:, 4] + tensor[:, 8]
            intensity = (np.outer(trace, trace) + 2.0 * (tensor @ tensor.T)) * inverse_c * q4
            y[atom] += weight * np.bincount(index, weights=intensity.ravel(), minlength=n_bins + 1)[:n_bins]

    y *= 0.5  # 1/n! for the two-phonon process, as in abinslib
    spectra = Spectrum1DCollection(
        x_data=bins, y_data=Quantity(y, "dimensionless") / bin_width,
        metadata={
            "method": "almost-isotropic incoherent approximation",
            "line_data": [info | {"quantum_order": 2} for info in iter_atom_info(modes.crystal)],
        },
    )
    q4_scale = nominal_q2**2 / Quantity(1, "angstrom^-4")
    dw = calculate_isotropic_dw_factor(atomic_displacements=atomic_displacements, q2=nominal_q2)
    spectra.y_data = spectra.y_data * q4_scale * np.swapaxes(dw, -1, -2)[0]
    return spectra
