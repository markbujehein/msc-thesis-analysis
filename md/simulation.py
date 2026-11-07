import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    # Full simulation: 2x2x1 supercell, same functions as mwe.py.
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.signal import find_peaks

    from mwe import build, dos, simulate

    THYMOL = "Cc1ccc(C(C)C)c(O)c1"


@app.cell
def _():
    pdb = Path(__file__).parents[1] / "pdb" / "thymol_structure3_R-3_2x2x1.pdb"  # 1800 atoms
    out_dir = Path(__file__).parent / "output"
    cutoff_nm = 1.0
    temperature_K = 10
    dt_fs = 0.5
    every = 4  # a frame every 2 fs
    equil_steps = 10000  # 5 ps
    prod_steps = 40000  # 20 ps
    return (
        cutoff_nm,
        dt_fs,
        equil_steps,
        every,
        out_dir,
        pdb,
        prod_steps,
        temperature_K,
    )


@app.cell
def _(cutoff_nm, pdb):
    topology, system, positions = build(pdb, THYMOL, cutoff_nm)
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
    print(f"{len(velocities)} frames")
    return (velocities,)


@app.cell
def _(out_dir, velocities):
    out_dir.mkdir(exist_ok=True)
    np.save(out_dir / "velocities.npy", velocities.astype(np.float32))
    return


@app.cell
def _(dt_fs, every, out_dir, velocities):
    energy_meV, g = dos(velocities, dt_fs * every)
    np.savetxt(out_dir / "dos.csv", np.c_[energy_meV, g], delimiter=",", header="energy_meV,g")
    peaks, _ = find_peaks(g, prominence=g.max() * 0.02)
    print(f"resolution {energy_meV[1]:.2f} meV; peaks (meV):", np.round(energy_meV[peaks], 1))
    return energy_meV, g


@app.cell
def _(energy_meV, g):
    spectrum = pd.DataFrame({"energy (meV)": energy_meV, "g(E)": g})
    chart = alt.Chart(spectrum[spectrum["energy (meV)"] <= 600]).mark_line().encode(
        x="energy (meV)",
        y="g(E)",
    )
    mo.ui.altair_chart(chart)
    return


if __name__ == "__main__":
    app.run()
