import math
from pathlib import Path

import openmm as mm
from openmm import app, unit

from build import bonds_from_geometry, make_system, oh_energy_mev, read_pdb

PDB = Path(__file__).parents[3] / "pdb" / "thymol_structure3_R-3_2x2x1.pdb"
THYMOL = "Cc1ccc(C(C)C)c(O)c1"


def test_read_pdb_counts():
    pdb = read_pdb(PDB)
    assert pdb.topology.getNumAtoms() == 1800
    assert pdb.topology.getNumResidues() == 72


def test_every_molecule_has_25_bonds():
    molecules = bonds_from_geometry(PDB, THYMOL)
    assert len(molecules) == 72
    assert all(m.n_bonds == 25 for m in molecules)


def test_system_flexible_and_finite_energy():
    topology, system, positions = make_system(PDB, THYMOL, 1.0)
    assert system.getNumParticles() == 1800
    assert system.getNumConstraints() == 0
    sim = app.Simulation(topology, system, mm.VerletIntegrator(0.5 * unit.femtosecond))
    sim.context.setPositions(positions)
    sim.minimizeEnergy(maxIterations=50)
    energy = sim.context.getState(getEnergy=True).getPotentialEnergy()
    assert math.isfinite(energy.value_in_unit(unit.kilojoule_per_mole))


def test_oh_energy_in_expected_range_mev():
    topology, system, _ = make_system(PDB, THYMOL, 1.0)
    assert 400 < oh_energy_mev(topology, system) < 520


def test_bond_assignment_reports_progress_per_molecule():
    unitcell = PDB.with_name("thymol_structure3_R-3_unitcell.pdb")
    calls = []

    class Bar:
        def __init__(self, total, title):
            calls.append(["init", total, title])

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def update(self, increment=1):
            calls.append(["update", increment])

    molecules = bonds_from_geometry(unitcell, THYMOL, bar=Bar)
    assert calls[0] == ["init", len(molecules), "assigning bond orders"]
    assert sum(c[1] for c in calls[1:]) == len(molecules)


UNIT = Path(__file__).parents[3] / "pdb" / "thymol_structure3_R-3_unitcell.pdb"


def test_nonbonded_cutoff_is_switched():
    _, system, _ = make_system(UNIT, THYMOL, 0.6)
    nb = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
    assert nb.getUseSwitchingFunction()
    assert abs(nb.getSwitchingDistance().value_in_unit(unit.nanometer) - 0.5) < 1e-9
    assert nb.getUseDispersionCorrection()
