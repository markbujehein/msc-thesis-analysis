import marimo

__generated_with = "0.25.2"
app = marimo.App()

with app.setup:
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.signal import find_peaks

    from build import read_pdb
    from dos import dos, resolution_mev

    CELLS = {"1x1x1": "unitcell", "2x2x1": "2x2x1"}  # PDB names, as in 02_run.py


@app.cell
def _():
    out_dir = Path(__file__).parent / "output"
    dt_fs = 0.5
    every = 4  # a frame every 2 fs
    measured = None  # slot: DataFrame with columns "energy (meV)", "g(E)" to overlay later
    return dt_fs, every, measured, out_dir


@app.cell
def _(dt_fs, every, out_dir):
    spectra = {}  # cell -> (energy_meV, total g, hydrogen g)
    for _cell, _name in CELLS.items():
        _path = out_dir / f"velocities_{_cell}.f32"
        if not _path.exists():
            continue
        _topology = read_pdb(Path(__file__).parents[1] / "pdb" / f"thymol_structure3_R-3_{_name}.pdb").topology
        _hydrogen = [a.element.symbol == "H" for a in _topology.atoms()]
        _velocities = np.fromfile(_path, dtype=np.float32).reshape(-1, len(_hydrogen), 3)
        _energy, _g = dos(_velocities, dt_fs * every)
        _, _g_h = dos(_velocities[:, _hydrogen], dt_fs * every)
        spectra[_cell] = (_energy, _g, _g_h)
        _peaks, _ = find_peaks(_g_h, prominence=_g_h.max() * 0.02)
        print(
            f"{_cell}: {len(_velocities)} frames, resolution {resolution_mev(len(_velocities), dt_fs * every):.2f} meV; "
            f"H peaks (meV): {np.round(_energy[_peaks], 1)}"
        )
    return (spectra,)


@app.cell
def _(measured, spectra):
    _cell = "2x2x1" if "2x2x1" in spectra else next(iter(spectra))
    energy_meV, g, g_h = spectra[_cell]
    table = pd.concat(
        [
            pd.DataFrame({"energy (meV)": energy_meV, "g(E)": g, "which": "total"}),
            pd.DataFrame({"energy (meV)": energy_meV, "g(E)": g_h, "which": "hydrogen"}),
        ]
        + ([measured.assign(which="measured")] if measured is not None else [])
    )
    mo.ui.altair_chart(
        alt.Chart(table[table["energy (meV)"] <= 600]).mark_line().encode(x="energy (meV)", y="g(E)", color="which")
    )
    return


@app.cell
def _(spectra):
    # convergence: the lattice region below about 30 meV depends on the cell size
    low = pd.concat(
        [
            pd.DataFrame({"energy (meV)": _e, "g(E)": _g, "cell": _c})
            for _c, (_e, _g, _) in spectra.items()
        ]
    )
    mo.ui.altair_chart(
        alt.Chart(low[low["energy (meV)"] <= 30]).mark_line().encode(x="energy (meV)", y="g(E)", color="cell")
    )
    return


if __name__ == "__main__":
    app.run()
