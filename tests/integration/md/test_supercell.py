import itertools

import numpy as np
import openmm as mm
import pytest

from hessian import finite_difference_hessian
from supercell import assign_cells, load_force_constants, save_force_constants, unfold_hessian

MASS = 39.948


def cubic_lj_supercell(n=3, a=0.6):
    """n^3 one-atom cubic cells of LJ atoms; the cutoff is below half the supercell edge."""
    system = mm.System()
    nonbonded = mm.NonbondedForce()
    nonbonded.setNonbondedMethod(mm.NonbondedForce.CutoffPeriodic)
    nonbonded.setCutoffDistance(0.8)
    nonbonded.setUseSwitchingFunction(True)
    nonbonded.setSwitchingDistance(0.7)
    positions = np.array(list(itertools.product(range(n), repeat=3)), dtype=float) * a
    for _ in positions:
        system.addParticle(MASS)
        nonbonded.addParticle(0.0, 0.34, 1.0)
    system.addForce(nonbonded)
    system.setDefaultPeriodicBoxVectors(*[mm.Vec3(*row) for row in np.eye(3) * n * a])
    return system, positions


def test_unfolded_fc_reproduces_supercell_frequencies():
    n, a = 3, 0.6
    system, positions = cubic_lj_supercell(n, a)
    hessian = finite_difference_hessian(system, positions)
    unit_cell = np.eye(3) * a
    atom_in_cell, origin = assign_cells(positions, np.zeros((1, 3)), unit_cell)
    origins, fc = unfold_hessian(hessian, atom_in_cell, origin, n_cell_atoms=1)
    assert fc.shape == (n**3, 3, 3)
    from_supercell = np.sort(np.linalg.eigvalsh(hessian / MASS))
    from_unfolded = []
    for q in itertools.product(range(n), repeat=3):
        phase = np.exp(-2j * np.pi * (origins @ np.array(q)) / n)
        dynamical = np.tensordot(phase, fc, axes=(0, 0)) / MASS
        from_unfolded.extend(np.linalg.eigvalsh(dynamical))
    np.testing.assert_allclose(np.sort(from_unfolded), from_supercell, atol=1e-6 * np.abs(from_supercell).max())


def test_assign_cells_raises_on_unmatched_atom():
    _, positions = cubic_lj_supercell()
    positions[5] += [0.05, 0.0, 0.0]
    with pytest.raises(ValueError, match="atom 5"):
        assign_cells(positions, np.zeros((1, 3)), np.eye(3) * 0.6)


def test_force_constants_round_trip(tmp_path):
    kwargs = dict(
        fc=np.arange(2 * 6 * 6, dtype=float).reshape(2, 6, 6),
        origins=np.array([[0, 0, 0], [1, 0, 0]]),
        sc_matrix=np.diag([2, 1, 1]),
        unit_cell_nm=np.eye(3),
        frac_positions=np.array([[0.0, 0, 0], [0.5, 0.5, 0.5]]),
        symbols=np.array(["O", "H"]),
        masses_amu=np.array([16.0, 1.0]),
    )
    save_force_constants(tmp_path / "fc.npz", **kwargs)
    loaded = load_force_constants(tmp_path / "fc.npz")
    assert set(loaded) == set(kwargs)
    for key, value in kwargs.items():
        np.testing.assert_array_equal(loaded[key], value)
