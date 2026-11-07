import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import openmm as mm
    from openmm import app as omm_app
    from openmm import unit

    from build import bonds_from_geometry, make_system, oh_energy_mev, read_pdb

    THYMOL = "Cc1ccc(C(C)C)c(O)c1"


@app.cell
def _():
    pdb = Path(__file__).parents[1] / "pdb" / "thymol_structure3_R-3_2x2x1.pdb"  # 1800 atoms
    cutoff_nm = 1.0
    return cutoff_nm, pdb


@app.cell
def _(pdb):
    pdb_file = read_pdb(pdb)
    box = pdb_file.topology.getPeriodicBoxVectors()
    print(
        f"{pdb_file.topology.getNumAtoms()} atoms in {pdb_file.topology.getNumResidues()} molecules, "
        f"box {[round(box[i][i].value_in_unit(unit.nanometer), 3) for i in range(3)]} nm"
    )
    molecules = bonds_from_geometry(pdb, THYMOL)
    print(f"bonds per molecule: {sorted({m.n_bonds for m in molecules})} (expected [25])")
    return


@app.cell
def _(cutoff_nm, pdb):
    topology, system, positions = make_system(pdb, THYMOL, cutoff_nm)
    print(f"{system.getNumParticles()} particles, {system.getNumConstraints()} constraints (expected 0)")
    return positions, system, topology


@app.cell
def _(positions, system, topology):
    simulation = omm_app.Simulation(topology, system, mm.VerletIntegrator(0.5 * unit.femtosecond))
    simulation.context.setPositions(positions)
    before = simulation.context.getState(getEnergy=True).getPotentialEnergy()
    simulation.minimizeEnergy()
    after = simulation.context.getState(getEnergy=True).getPotentialEnergy()
    print(f"potential energy {before} -> {after} after minimisation")
    return


@app.cell
def _(system, topology):
    print(f"O-H harmonic energy {oh_energy_mev(topology, system):.1f} meV")
    return


if __name__ == "__main__":
    app.run()
