import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import sys
    from pathlib import Path

    import altair as alt
    import numpy as np
    import pandas as pd

    ROOT = Path("/home/mark/Work/msc-thesis-analysis")
    sys.path.insert(0, str(ROOT / "md"))
    sys.path.insert(0, str(ROOT / "analysis"))
    from compare import bin_integral, edges_from_centres, fit_scale
    from dos import dos
    from thermo import thermo_from_dos

    return (
        ROOT,
        alt,
        bin_integral,
        dos,
        edges_from_centres,
        fit_scale,
        np,
        pd,
        thermo_from_dos,
    )


@app.cell
def _(ROOT, dos, np):
    # loaded: 1x1x1 NVE velocities (450 atoms, a frame every 2 fs); derived: classical DOS (md/dos.py)
    _velocities = np.fromfile(ROOT / "md/output/velocities_1x1x1.f32", dtype=np.float32).reshape(-1, 450, 3)
    energy_mev, g = dos(_velocities, 2.0)
    return energy_mev, g


@app.cell
def _(alt, energy_mev, g, mo, pd):
    dos_table = pd.DataFrame({"energy (meV)": energy_mev, "g(E)": g})
    dos_fig = (
        alt.Chart(dos_table[dos_table["energy (meV)"] <= 600])
        .mark_line()
        .encode(x=alt.X("energy (meV):Q", title="energy (meV)"), y=alt.Y("g(E):Q", title="g(E) (1/meV, area 1)"))
        .properties(title="Classical vibrational DOS, 1x1x1 cell (450 atoms), MD at 10 K", height=300, width=700)
    )
    mo.ui.altair_chart(dos_fig)
    return


@app.cell
def _(alt, energy_mev, g, mo, np, pd, thermo_from_dos):
    # derived: harmonic thermodynamics per cell from the classical DOS (md/thermo.py), 1347 modes
    temperatures = np.linspace(5.0, 300.0, 60)
    curves = thermo_from_dos(energy_mev, g, n_modes=3 * 450 - 3, temperatures_K=temperatures)
    thermo_table = pd.DataFrame({"T (K)": temperatures} | curves)
    _labels = {"U_meV": "internal energy U (meV)", "S_meV_per_K": "entropy S (meV/K)",
               "F_meV": "free energy F (meV)", "Cv_meV_per_K": "heat capacity Cv (meV/K)"}
    thermo_fig = alt.vconcat(*[
        alt.Chart(thermo_table).mark_line()
        .encode(x=alt.X("T (K):Q", title="temperature (K)"), y=alt.Y(f"{_name}:Q", title=_title, scale=alt.Scale(zero=False)))
        .properties(title=_title.split(" (")[0] + " per cell", height=110, width=600)
        for _name, _title in _labels.items()
    ]).properties(title="Harmonic thermodynamics per cell from the classical DOS")
    mo.ui.altair_chart(thermo_fig)
    return


@app.cell
def _(ROOT, mo, np):
    # Task 6, step 5: back bank of the 2x2x1 force constants, mean detector geometry; orders 1 and 2 as separate runs
    from ins import simulate_tosca

    _args = (ROOT / "md/output/fc_2x2x1.npz", ROOT / "data/tosca_detectors_idf2016.csv", np.arange(0.0, 500.5, 0.5))
    _bar = lambda total, title: mo.status.progress_bar(total=total, title=title)
    ins_energy, first_order = simulate_tosca(*_args, bank="back", bar=_bar, orders=(1,))
    _, second_order = simulate_tosca(*_args, bank="back", bar=_bar, orders=(2,))
    total_intensity = first_order + second_order
    return first_order, ins_energy, second_order, total_intensity


@app.cell
def _(ROOT, mo):
    # loaded: reduced TOSCA runs (git-ignored real data); chosen interactively
    reduced = {_p.stem.split("_")[0]: _p for _p in sorted((ROOT / "data/reduced").glob("TSC*_thymol.csv"))}
    run_choice = mo.ui.dropdown(reduced, value=next(iter(reduced)), label="measured run") if reduced else None
    bank_choice = mo.ui.dropdown(["bank1", "bank2"], value="bank1", label="measured bank (assignment to the back bank unverified)")
    axis_choice = mo.ui.dropdown(["linear", "log"], value="linear", label="energy axis")
    window = mo.ui.range_slider(start=0, stop=1000, step=5, value=(5, 500), label="energy window (meV)", full_width=True)
    mo.vstack([mo.hstack([_c for _c in (run_choice, bank_choice, axis_choice) if _c is not None]), window])
    return axis_choice, bank_choice, run_choice, window


@app.cell
def _(
    alt,
    axis_choice,
    bank_choice,
    bin_integral,
    edges_from_centres,
    first_order,
    fit_scale,
    ins_energy,
    mo,
    pd,
    run_choice,
    second_order,
    total_intensity,
    window,
):
    # derived: simulated orders and total on the simulation grid; the measurement and a fitted scale when data exist
    _table = pd.DataFrame({"energy (meV)": ins_energy, "first order": first_order, "second order": second_order,
                           "total": total_intensity})
    _scale, _note = 1.0, "No measured data found: intensities in arbitrary units."
    if run_choice is not None:
        _m = pd.read_csv(run_choice.value)
        _n = bank_choice.value[-1]
        _centres = _m["energy_meV"].to_numpy()
        _model = bin_integral(ins_energy, total_intensity, edges_from_centres(_centres))
        _use = (_centres > 20) & (_centres < 500)  # outside the elastic line and inside the simulated range
        _scale = fit_scale(_model[_use], _m[f"bank{_n}"].to_numpy()[_use], _m[f"error{_n}"].to_numpy()[_use])
        _note = f"Fitted scale of the total (20 to 500 meV, weighted least squares): {_scale:.4g}."
    _table = _table.assign(**{_c: _table[_c] * _scale for _c in ("first order", "second order", "total")})
    _long = _table.melt("energy (meV)", var_name="curve", value_name="intensity")
    if run_choice is not None:
        _long = pd.concat([_long, pd.DataFrame({"energy (meV)": _centres, "curve": "measured", "intensity": _m[f"bank{_n}"]})])
    _low, _high = window.value
    _long = _long[(_long["energy (meV)"] >= max(_low, 1.0 if axis_choice.value == "log" else 0.0))
                  & (_long["energy (meV)"] <= _high)]
    spectrum_fig = (
        alt.Chart(_long)
        .mark_line()
        .encode(
            x=alt.X("energy (meV):Q", title="energy transfer (meV)", scale=alt.Scale(type=axis_choice.value)),
            y=alt.Y("intensity:Q", title="intensity (arbitrary units, simulation x fitted scale)" if run_choice is not None else "intensity (arbitrary units)"),
            color=alt.Color("curve:N", title="curve"),
        )
        .properties(title="TOSCA back bank: simulated INS (GAFF2, 10 K, orders 1 and 2)"
                          + (f" and measured {run_choice.selected_key}, {bank_choice.value}" if run_choice is not None else ""),
                    height=380, width=700)
    )
    mo.vstack([mo.md(_note), mo.ui.altair_chart(spectrum_fig)])
    return


if __name__ == "__main__":
    app.run()
