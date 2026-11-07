import numpy as np
from ase.thermochemistry import CrystalThermo
from scipy.integrate import trapezoid

KB_MEV = 0.08617333262  # meV/K
MIN_MEV = 0.5  # bins at or below this energy hold the translational modes and are dropped


def thermo_from_dos(energy_mev, g, n_modes, temperatures_K):
    """Harmonic quantum thermodynamics of a DOS, per cell: U, F (meV), S, Cv (meV/K) against temperature.

    Bins at or below 0.5 meV are dropped and g is rescaled to integrate to n_modes (the modes that remain).
    U, S and F come from ase.thermochemistry.CrystalThermo (eV there); ASE has no heat capacity, so Cv is
    the harmonic sum k_B x^2 e^x / (e^x - 1)^2 with x = E / k_B T over the same bins.
    """
    energy = np.asarray(energy_mev, dtype=float)
    keep = energy > MIN_MEV
    energy, g = energy[keep], np.asarray(g, dtype=float)[keep]
    g = g * n_modes / trapezoid(g, energy)
    thermo = CrystalThermo(phonon_DOS=g * 1000.0, phonon_energies=energy / 1000.0)  # ASE integrates over eV: g per eV
    temperatures = np.asarray(temperatures_K, dtype=float)
    x = energy[None, :] / (KB_MEV * temperatures[:, None])
    heat_capacity = KB_MEV * trapezoid(g * x**2 * np.exp(-x) / (-np.expm1(-x)) ** 2, energy, axis=1)
    return {
        "U_meV": np.array([1000 * thermo.get_internal_energy(t, verbose=False) for t in temperatures]),
        "S_meV_per_K": np.array([1000 * thermo.get_entropy(t, verbose=False) for t in temperatures]),
        "F_meV": np.array([1000 * thermo.get_helmholtz_energy(t, verbose=False) for t in temperatures]),
        "Cv_meV_per_K": heat_capacity,
    }
