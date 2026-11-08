import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    # Pick the cell on the command line: python 02_run.py -- --cell 1x1x1
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    from build import make_system
    from run import run

    THYMOL = "Cc1ccc(C(C)C)c(O)c1"
    CELLS = {"1x1x1": ("unitcell", 0.6), "2x2x1": ("2x2x1", 1.0)}


@app.cell
def _():
    cell = mo.cli_args().get("cell", "2x2x1")
    pdb = Path(__file__).parents[1] / "pdb" / f"thymol_structure3_R-3_{CELLS[cell][0]}.pdb"
    cutoff_nm = CELLS[cell][1]
    out_dir = Path(__file__).parent / "output"
    temperature_K = 10
    dt_fs = 0.5
    every = 4  # a frame every 2 fs
    equil_steps = 10000  # 5 ps
    prod_steps = 200000  # 100 ps
    return (
        cell,
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
    topology, system, positions = make_system(pdb, THYMOL, cutoff_nm)
    print(f"{system.getNumParticles()} particles, {system.getNumConstraints()} constraints")
    return positions, system, topology


@app.cell
def _(
    cell,
    dt_fs,
    equil_steps,
    every,
    out_dir,
    positions,
    prod_steps,
    system,
    temperature_K,
    topology,
):
    out_dir.mkdir(exist_ok=True)
    run(
        topology, system, positions, temperature_K, dt_fs, equil_steps, prod_steps, every,
        out_dir / f"velocities_{cell}.f32", out_dir / f"log_{cell}.csv",
        bar=lambda total, title: mo.status.progress_bar(total=total, title=title),
    )
    print(f"{prod_steps // every} frames written to velocities_{cell}.f32")
    return


@app.cell
def _(cell, out_dir):
    log = pd.read_csv(out_dir / f"log_{cell}.csv")
    log.columns = ["step", "time (ps)", "potential (kJ/mol)", "kinetic (kJ/mol)", "total (kJ/mol)", "T (K)"]
    temperature_chart = alt.Chart(log).mark_line().encode(
        x=alt.X("time (ps):Q", title="time (ps)"), y=alt.Y("T (K):Q", title="temperature (K)")
    ).properties(title="Temperature during the run", height=200, width=600)
    energy_chart = alt.Chart(log).mark_line().encode(
        x=alt.X("time (ps):Q", title="time (ps)"),
        y=alt.Y("total (kJ/mol):Q", title="total energy (kJ/mol)", scale=alt.Scale(zero=False)),
    ).properties(title="Total energy during the run", height=200, width=600)
    run_fig = (temperature_chart & energy_chart).properties(title=f"MD run, {cell} cell")
    mo.ui.altair_chart(run_fig)
    return


@app.cell
def _(cell, out_dir):
    # derived: temperature and energy drift of the production part (second half of the log), as a table
    _log = pd.read_csv(out_dir / f"log_{cell}.csv")
    _log.columns = ["step", "time (ps)", "potential (kJ/mol)", "kinetic (kJ/mol)", "total (kJ/mol)", "T (K)"]
    _half = _log[_log["time (ps)"] >= _log["time (ps)"].max() / 2]
    _drift = float(np.polyfit(_half["time (ps)"], _half["total (kJ/mol)"], 1)[0])
    mo.ui.table(pd.DataFrame({
        "mean T (K)": [_half["T (K)"].mean()], "std T (K)": [_half["T (K)"].std()],
        "total energy drift (kJ/mol/ps)": [_drift],
    }), label=f"Second half of the log, {cell} cell")
    return


if __name__ == "__main__":
    app.run()
