import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import openmm as mm
    import pandas as pd
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
def _(positions, topology):
    atoms_table = pd.DataFrame(
        {"element": [a.element.symbol for a in topology.atoms()]}
        | dict(zip(("x (nm)", "y (nm)", "z (nm)"), np.array(positions.value_in_unit(unit.nanometer)).T))
    )
    _xy = alt.Chart(atoms_table).mark_circle(size=12).encode(
        x=alt.X("x (nm):Q", title="x (nm)"), y=alt.Y("y (nm):Q", title="y (nm)"), color=alt.Color("element:N", title="element")
    ).properties(title="Atom positions projected on x-y", width=330, height=330)
    _xz = alt.Chart(atoms_table).mark_circle(size=12).encode(
        x=alt.X("x (nm):Q", title="x (nm)"), y=alt.Y("z (nm):Q", title="z (nm)"), color=alt.Color("element:N", title="element")
    ).properties(title="Atom positions projected on x-z", width=330, height=330)
    positions_fig = (_xy | _xz).properties(title="Thymol 2x2x1 supercell: atoms by element")
    mo.ui.altair_chart(positions_fig)
    return (atoms_table,)


@app.cell
def _(positions, topology):
    # created: ASE structure (nm to angstrom) for the molecular view
    from ase import Atoms

    structure = Atoms(
        symbols=[a.element.symbol for a in topology.atoms()],
        positions=np.array(positions.value_in_unit(unit.nanometer)) * 10.0,
        cell=np.array([v.value_in_unit(unit.nanometer) for v in topology.getPeriodicBoxVectors()]) * 10.0,
        pbc=True,
    )
    return (structure,)


@app.cell
def _(pdb, structure, topology):
    # 3D molecular view (Mol*): the molecules of the 2x2x1 supercell as ball and stick; drag to rotate, scroll to zoom.
    # Outlines: the 450-atom unit cell (orange, conventional hexagonal cell of R-3) and the 2x2x1 supercell (cyan)
    from ipymolstar.molviewspec import MolViewSpec

    from molview import mmcif_text, mvs_json

    _unit_cell = np.array([v.value_in_unit(unit.nanometer) for v in read_pdb(pdb.parent / "thymol_structure3_R-3_unitcell.pdb").topology.getPeriodicBoxVectors()]) * 10.0

    _cif = mmcif_text(
        structure.get_chemical_symbols(), structure.positions, structure.cell.array,
        molecule=[a.residue.index for a in topology.atoms()],
    )
    _panels_off = {  # only the 3D canvas: no left or right panels, sequence, log or remote states
        "layoutIsExpanded": False, "layoutShowControls": False, "layoutShowRemoteState": False,
        "layoutShowSequence": False, "layoutShowLog": False, "layoutShowLeftPanel": False,
    }
    structure_view = mo.ui.anywidget(MolViewSpec(msvj_data=mvs_json(_cif, cells=[(np.zeros(3), _unit_cell, "#ffa500"), (np.zeros(3), structure.cell.array, "#00ffff")]), height="600px", viewer_options=_panels_off))
    structure_view
    return


@app.cell
def _(atoms_table):
    # derived: atoms per element
    _counts = atoms_table.groupby("element").size().rename("atoms").reset_index()
    mo.ui.table(_counts.astype({"element": object}), label="Atoms per element")
    return


@app.cell
def _(system, topology):
    # created: GAFF2 AM1-BCC partial charges of the system
    _nonbonded = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
    charges = np.array([_nonbonded.getParticleParameters(i)[0].value_in_unit(unit.elementary_charge)
                        for i in range(system.getNumParticles())])
    charges_fig = (
        alt.Chart(pd.DataFrame({"charge (e)": charges, "element": [a.element.symbol for a in topology.atoms()]}))
        .mark_bar()
        .encode(x=alt.X("charge (e):Q", bin=alt.Bin(maxbins=60), title="partial charge (e)"),
                y=alt.Y("count():Q", title="atoms"), color=alt.Color("element:N", title="element"))
        .properties(title="GAFF2 AM1-BCC partial charges by element", width=480, height=300)
    )
    mo.ui.altair_chart(charges_fig)
    return


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
