import numpy as np
import openmm as mm
import pytest
from openmm import app, unit

from hessian import finite_difference_hessian, mode_energies_mev, relax

HBAR_MEV_PS = 0.6582119569


def two_particles(force, m1=16.0, m2=1.0):
    system = mm.System()
    system.addParticle(m1)
    system.addParticle(m2)
    system.addForce(force)
    return system, np.array([[0.0, 0.0, 0.0], [0.2, 0.0, 0.0]]), np.array([m1, m2])


def harmonic_bond(k, r0=0.2):
    force = mm.HarmonicBondForce()
    force.addBond(0, 1, r0, k)
    return force


def double_well(c=1e6, k=1000.0, r0=0.2):
    """Energy -k/2 x^2 + c/4 x^4 in x = r - r0: a maximum at r0, wells at +-sqrt(k/c)."""
    force = mm.CustomBondForce("0.25*c*(r-r0)^4 - 0.5*k*(r-r0)^2")
    for name, value in (("c", c), ("k", k), ("r0", r0)):
        force.addGlobalParameter(name, value)
    force.addBond(0, 1, [])
    return force


def fcc_argon(n=3, a=0.53):
    """n^3 fcc cells of argon with a smooth cutoff (smaller than half the box)."""
    system = mm.System()
    nonbonded = mm.NonbondedForce()
    nonbonded.setNonbondedMethod(mm.NonbondedForce.CutoffPeriodic)
    nonbonded.setCutoffDistance(0.75)
    nonbonded.setUseSwitchingFunction(True)
    nonbonded.setSwitchingDistance(0.65)
    basis = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    positions = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for b in basis:
                    positions.append((np.array([i, j, k]) + b) * a)
                    system.addParticle(39.948)
                    nonbonded.addParticle(0.0, 0.34, 1.0)
    system.addForce(nonbonded)
    box = np.eye(3) * n * a
    system.setDefaultPeriodicBoxVectors(*[mm.Vec3(*row) for row in box])
    return system, np.array(positions), np.full(len(positions), 39.948)


def test_dimer_energy_is_hbar_sqrt_k_over_mu():
    k = 5000.0
    system, x, m = two_particles(harmonic_bond(k))
    energies = mode_energies_mev(finite_difference_hessian(system, x), np.repeat(m, 3))
    mu = 16.0 * 1.0 / 17.0
    assert energies[-1] == pytest.approx(HBAR_MEV_PS * np.sqrt(k / mu), abs=1e-3)
    assert np.abs(energies[:-1]).max() < 1e-2  # sqrt turns 1e-5 ps^-2 of noise into ~1e-3 meV


def test_unstable_geometry_gives_negative_energy_not_clipped():
    system, x, m = two_particles(double_well())
    energies = mode_energies_mev(finite_difference_hessian(system, x), np.repeat(m, 3))
    assert energies[0] < -1.0


def test_relax_raises_when_no_cycle_is_allowed_to_escape_a_saddle():
    system, x, _ = two_particles(double_well())
    with pytest.raises(RuntimeError, match="imaginary"):
        relax(system, x, max_cycles=0)


def test_relax_escapes_the_saddle_by_following_the_imaginary_mode():
    system, x, m = two_particles(double_well())
    x_min = relax(system, x, max_cycles=3)
    energies = mode_energies_mev(finite_difference_hessian(system, x_min), np.repeat(m, 3))
    assert energies[0] > -0.5
    assert abs(np.linalg.norm(x_min[1] - x_min[0]) - 0.2) == pytest.approx(np.sqrt(1000 / 1e6), abs=2e-3)


def test_argon_crystal_has_exactly_three_zero_modes():
    system, x, m = fcc_argon()
    x_min = relax(system, x)
    energies = mode_energies_mev(finite_difference_hessian(system, x_min), np.repeat(m, 3))
    assert np.abs(energies[:3]).max() < 0.05
    assert energies[3] > 0.5
