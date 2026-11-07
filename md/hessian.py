import numpy as np
import openmm as mm
from openmm import unit

HBAR_MEV_PS = 0.6582119569  # meV ps
FORCE = unit.kilojoule_per_mole / unit.nanometer


def _context(system, platform):
    return mm.Context(system, mm.VerletIntegrator(0.001), mm.Platform.getPlatformByName(platform))


def _forces(context, positions_nm):
    context.setPositions(positions_nm)
    return context.getState(getForces=True).getForces(asNumpy=True).value_in_unit(FORCE).ravel()


def finite_difference_hessian(system, positions_nm, h_nm=1e-5, platform="Reference"):
    """Hessian (3n, 3n) in kJ/mol/nm^2 from central differences of the forces, symmetrised."""
    context = _context(system, platform)
    x = np.asarray(positions_nm, dtype=float)
    hessian = np.zeros((x.size, x.size))
    for k in range(x.size):
        plus, minus = x.copy().ravel(), x.copy().ravel()
        plus[k] += h_nm
        minus[k] -= h_nm
        hessian[k] = -(_forces(context, plus.reshape(x.shape)) - _forces(context, minus.reshape(x.shape))) / (2 * h_nm)
    return (hessian + hessian.T) / 2


def mode_energies_mev(hessian, masses_amu):
    """Sorted mode energies in meV; imaginary modes come out negative, never clipped.

    masses_amu has one entry per degree of freedom (each atom's mass three times).
    1 kJ/mol = 1 amu nm^2/ps^2, so the eigenvalues of the mass-weighted Hessian are w^2 in ps^-2.
    """
    w2 = np.linalg.eigvalsh(hessian / np.sqrt(np.outer(masses_amu, masses_amu)))
    return np.sort(HBAR_MEV_PS * np.sign(w2) * np.sqrt(np.abs(w2)))


def _minimise(context, positions_nm):
    context.setPositions(positions_nm)
    mm.LocalEnergyMinimizer.minimize(context, 1e-3, 10000)
    state = context.getState(getPositions=True, getEnergy=True)
    energy = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
    return state.getPositions(asNumpy=True).value_in_unit(unit.nanometer), energy


def relax(system, positions_nm, platform="Reference", max_cycles=5, step_nm=0.02):
    """Minimum-energy positions (n, 3) in nm; raises RuntimeError if imaginary modes remain.

    After each minimisation, a geometry with imaginary modes (w^2 < -1 ps^-2) is displaced along them
    in both directions and minimised again; the lower energy is kept.
    """
    context = _context(system, platform)
    masses = np.repeat([system.getParticleMass(i).value_in_unit(unit.amu) for i in range(system.getNumParticles())], 3)
    x, _ = _minimise(context, np.asarray(positions_nm, dtype=float))
    for cycle in range(max_cycles + 1):
        w2, modes = np.linalg.eigh(_mass_weighted(finite_difference_hessian(system, x, platform=platform), masses))
        imaginary = np.where(w2 < -1.0)[0]
        if len(imaginary) == 0:
            return x
        if cycle == max_cycles:
            raise RuntimeError(f"{len(imaginary)} imaginary modes remain after {max_cycles} cycles")
        direction = modes[:, imaginary].sum(axis=1) / np.sqrt(masses)
        direction *= step_nm / np.abs(direction).max()
        trials = [_minimise(context, x + sign * direction.reshape(x.shape)) for sign in (1, -1)]
        x = min(trials, key=lambda trial: trial[1])[0]


def _mass_weighted(hessian, masses_amu):
    return hessian / np.sqrt(np.outer(masses_amu, masses_amu))
