import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    import time
    from pathlib import Path

    import numpy as np
    from openmm import unit

    from build import make_system, read_pdb
    from hessian import finite_difference_hessian, mode_energies_mev, relax
    from supercell import assign_cells, save_force_constants, unfold_hessian

    THYMOL = "Cc1ccc(C(C)C)c(O)c1"
    PDB = Path(__file__).parents[1] / "pdb"


@app.cell
def _():
    unit_pdb = PDB / "thymol_structure3_R-3_unitcell.pdb"  # 450 atoms
    sc_pdb = PDB / "thymol_structure3_R-3_2x2x1.pdb"  # 1800 atoms
    sc_matrix = np.diag([2, 2, 1])
    cutoff_nm = 1.0
    out = Path(__file__).parent / "output" / "fc_2x2x1.npz"
    return cutoff_nm, out, sc_matrix, sc_pdb, unit_pdb


@app.cell
def _(cutoff_nm, sc_pdb):
    topology, system, positions = make_system(sc_pdb, THYMOL, cutoff_nm)
    start = np.array(positions.value_in_unit(unit.nanometer))
    masses = np.repeat([system.getParticleMass(i).value_in_unit(unit.amu) for i in range(system.getNumParticles())], 3)
    # relax on the fast single-precision platform, then the Hessian once on the double-precision one
    t0 = time.time()
    relaxed = relax(system, start, platform="CPU")
    print(f"relaxed in {time.time() - t0:.0f} s")
    return masses, relaxed, start, system


@app.cell
def _(masses, relaxed, system):
    t1 = time.time()
    hessian = finite_difference_hessian(system, relaxed, platform="Reference")
    print(f"Hessian {hessian.shape} in {time.time() - t1:.0f} s")
    energies = mode_energies_mev(hessian, masses)
    print(f"imaginary (< -0.5 meV): {(energies < -0.5).sum()}, below 0.5 meV: {(abs(energies) < 0.5).sum()}")
    for lo, hi in ((0.5, 60), (60, 230), (230, 350), (350, 420), (440, 480)):
        print(f"{lo}-{hi} meV: {((energies >= lo) & (energies < hi)).sum()} modes")
    return (hessian,)


@app.cell
def _(hessian, out, sc_matrix, sc_pdb, start, unit_pdb):
    unit_file = read_pdb(unit_pdb)
    cell = np.array([v.value_in_unit(unit.nanometer) for v in unit_file.topology.getPeriodicBoxVectors()])
    unit_positions = np.array(unit_file.positions.value_in_unit(unit.nanometer))
    atoms = list(unit_file.topology.atoms())
    atom_in_cell, origin = assign_cells(start, unit_positions, cell)  # from the PDB geometry, before relaxation
    origins, fc = unfold_hessian(hessian, atom_in_cell, origin, n_cell_atoms=len(atoms))
    out.parent.mkdir(exist_ok=True)
    save_force_constants(
        out, fc, origins, sc_matrix, cell, unit_positions @ np.linalg.inv(cell),
        np.array([a.element.symbol for a in atoms]), np.array([a.element.mass.value_in_unit(unit.amu) for a in atoms]),
    )
    print(f"{len(origins)} cells, fc {fc.shape}, saved to {out.name}")
    return


if __name__ == "__main__":
    app.run()
