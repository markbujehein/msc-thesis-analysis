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
def _(cell, dt_fs, equil_steps, out_dir, temperature_K):
    log = pd.read_csv(out_dir / f"log_{cell}.csv")
    log.columns = ["step", "time (ps)", "potential (kJ/mol)", "kinetic (kJ/mol)", "total (kJ/mol)", "T (K)"]
    equil_ps = equil_steps * dt_fs / 1000
    _production = log[log["time (ps)"] > equil_ps].assign(**{"total minus mean (kJ/mol)": lambda d: d["total (kJ/mol)"] - d["total (kJ/mol)"].mean()})
    _equil_band = alt.Chart(pd.DataFrame({"start": [0.0], "end": [equil_ps], "phase": ["equilibration"]})).mark_rect(opacity=0.2, color="orange").encode(
        x=alt.X("start:Q", title="time (ps)"), x2="end:Q"
    )
    _target = alt.Chart(pd.DataFrame({"T (K)": [temperature_K]})).mark_rule(color="red", strokeDash=[6, 4]).encode(y="T (K):Q")
    _temperature = (
        alt.Chart(log).mark_line().encode(x=alt.X("time (ps):Q", title="time (ps)"), y=alt.Y("T (K):Q", title="temperature (K)"))
        + _target + _equil_band
    ).properties(title=f"Temperature (red: {temperature_K} K target; orange: equilibration)", height=180, width=520)
    _energy = (
        alt.Chart(log).mark_line().encode(
            x=alt.X("time (ps):Q", title="time (ps)"), y=alt.Y("total (kJ/mol):Q", title="total energy (kJ/mol)", scale=alt.Scale(zero=False))
        ) + _equil_band
    ).properties(title="Total energy (orange: equilibration)", height=180, width=520)
    _energy_zoom = alt.Chart(_production).mark_line().encode(
        x=alt.X("time (ps):Q", title="time (ps)"), y=alt.Y("total minus mean (kJ/mol):Q", title="total energy minus its mean (kJ/mol)")
    ).properties(title="Total energy during production, deviation from its mean", height=180, width=520)
    _histogram = alt.Chart(_production).mark_bar().encode(
        x=alt.X("T (K):Q", bin=alt.Bin(maxbins=40), title="temperature (K)"), y=alt.Y("count():Q", title="frames")
    ).properties(title="Temperature distribution during production", height=180, width=520)
    run_fig = alt.vconcat(_temperature, _energy, _energy_zoom, _histogram).properties(title=f"MD run, {cell} cell")
    mo.ui.altair_chart(run_fig, chart_selection=False, legend_selection=False)
    return (log,)


@app.cell
def _(cell, log):
    # derived: temperature and energy drift of the production part (second half of the log), as a table
    _half = log[log["time (ps)"] >= log["time (ps)"].max() / 2]
    _drift = float(np.polyfit(_half["time (ps)"], _half["total (kJ/mol)"], 1)[0])
    mo.ui.table(pd.DataFrame({
        "mean T (K)": [_half["T (K)"].mean()], "std T (K)": [_half["T (K)"].std()],
        "total energy drift (kJ/mol/ps)": [_drift],
    }), label=f"Second half of the log, {cell} cell")
    return


if __name__ == "__main__":
    app.run()
