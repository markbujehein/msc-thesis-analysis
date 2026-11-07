import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    # Minimal working example: thymol unit cell (450 atoms) -> flexible GAFF2 MD at ~10 K -> DOS in meV.
    # Start with the md environment's bin on PATH (antechamber lives there). Not run, not tested yet.
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import openmm as mm
    import openmm.app as app_
    import openmm.unit as u
    import pandas as pd
    from openff.toolkit import Molecule, Topology
    from openmmforcefields.generators import SystemGenerator
    from rdkit import Chem, RDLogger
    from rdkit.Chem import AllChem
    from scipy.signal import find_peaks

    THYMOL = "Cc1ccc(C(C)C)c(O)c1"
    PDB = Path(__file__).parents[1] / "pdb" / "thymol_structure3_R-3_unitcell.pdb"
    H_MEV_FS = 4135.667696


@app.function
def build(pdb, smiles, cutoff_nm):
    """Flexible periodic OpenMM system from a crystal PDB of identical molecules.

    Parameters
    ----------
    pdb : path
        PDB with a CRYST1 box.
    smiles : str
        The molecule, for bond orders and charges.
    cutoff_nm : float
        Nonbonded cutoff in nm.

    Returns
    -------
    topology, system, positions
    """
    pdb_file = app_.PDBFile(str(pdb))

    # RDKit finds the bonds from the geometry, the SMILES template fixes the bond orders
    geometry = Chem.MolFromPDBFile(str(pdb), removeHs=False, proximityBonding=True)
    template = Chem.AddHs(Chem.MolFromSmiles(smiles))
    RDLogger.DisableLog("rdApp.warning")  # symmetric molecules: harmless "more than one match" warning
    molecules = []
    for fragment in Chem.GetMolFrags(geometry, asMols=True):
        fixed = AllChem.AssignBondOrdersFromTemplate(template, fragment)
        molecules.append(Molecule.from_rdkit(fixed, allow_undefined_stereo=True))
    RDLogger.EnableLog("rdApp.warning")

    topology = Topology.from_molecules(molecules).to_openmm()
    topology.setPeriodicBoxVectors(pdb_file.topology.getPeriodicBoxVectors())

    generator = SystemGenerator(
        forcefields=[],
        small_molecule_forcefield="gaff-2.11",
        molecules=[molecules[0]],  # identical molecules: one template is enough
        forcefield_kwargs={"constraints": None, "rigidWater": False},  # no constraints
        periodic_forcefield_kwargs={
            "nonbondedMethod": app_.PME,
            "nonbondedCutoff": cutoff_nm * u.nanometer,
        },
    )
    return topology, generator.create_system(topology), pdb_file.positions


@app.function
def simulate(topology, system, positions, temperature_K, equil_steps, prod_steps, every, dt_fs=0.5):
    """Minimise, equilibrate with a thermostat, then run without one.

    Returns the velocities in nm/ps, saved every `every` steps: (n_frames, n_atoms, 3).
    """
    dt = dt_fs * u.femtosecond
    temperature = temperature_K * u.kelvin

    thermostat = mm.LangevinMiddleIntegrator(temperature, 1 / u.picosecond, dt)
    equil = app_.Simulation(topology, system, thermostat)
    equil.context.setPositions(positions)
    equil.minimizeEnergy()
    equil.context.setVelocitiesToTemperature(temperature)
    equil.step(equil_steps)

    production = app_.Simulation(topology, system, mm.VerletIntegrator(dt))
    production.context.setState(equil.context.getState(getPositions=True, getVelocities=True))
    frames = []
    for _ in range(prod_steps // every):
        production.step(every)
        velocities = production.context.getState(getVelocities=True).getVelocities(asNumpy=True)
        frames.append(velocities.value_in_unit(u.nanometer / u.picosecond))
    return np.array(frames)


@app.function
def dos(velocities, dt_fs):
    """Power spectrum of the velocities (Fourier transform of the VACF).

    velocities: (n_frames, n_atoms, 3). Returns the energy in meV and g(E) with area 1.
    """
    n_frames = len(velocities)
    signal = velocities.reshape(n_frames, -1)
    signal = signal - signal.mean(axis=0)
    signal = signal * np.hanning(n_frames)[:, None]
    power = (np.abs(np.fft.rfft(signal, axis=0)) ** 2).sum(axis=1)
    energy_meV = np.fft.rfftfreq(n_frames, d=dt_fs) * H_MEV_FS
    return energy_meV, power / np.trapezoid(power, energy_meV)


@app.cell
def _():
    # parameters: 0.6 nm cutoff because the hex cell is only 1.47 nm wide; frames every 2 fs (Nyquist about 1030 meV)
    cutoff_nm = 0.6
    temperature_K = 10
    dt_fs = 0.5
    every = 4
    equil_steps = 2000
    prod_steps = 20000
    return cutoff_nm, dt_fs, equil_steps, every, prod_steps, temperature_K


@app.cell
def _(cutoff_nm):
    topology, system, positions = build(PDB, THYMOL, cutoff_nm)
    print(
        f"{system.getNumParticles()} atoms in {topology.getNumResidues()} molecules, "
        f"{system.getNumConstraints()} constraints, cutoff {cutoff_nm} nm"
    )
    return positions, system, topology


@app.cell
def _(
    dt_fs,
    equil_steps,
    every,
    positions,
    prod_steps,
    system,
    temperature_K,
    topology,
):
    velocities = simulate(topology, system, positions, temperature_K, equil_steps, prod_steps, every, dt_fs)
    print(f"{len(velocities)} frames, resolution {H_MEV_FS / (len(velocities) * dt_fs * every):.2f} meV")
    return (velocities,)


@app.cell
def _(dt_fs, every, velocities):
    e, g = dos(velocities, dt_fs * every)
    peaks, _ = find_peaks(g, prominence=g.max() * 0.02)
    print("DOS peaks (meV):", np.round(e[peaks], 1))

    spectrum = pd.DataFrame({"energy (meV)": e, "g(E)": g})
    chart = alt.Chart(spectrum[spectrum["energy (meV)"] <= 600]).mark_line().encode(
        x="energy (meV)",
        y="g(E)",
    )
    mo.ui.altair_chart(chart)
    return


if __name__ == "__main__":
    app.run()
