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

    CELLS = {"1x1x1": "unitcell", "2x2x1": "2x2x1"}


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
    summary = []  # one row per cell for the table below
    h_peaks = {}  # cell -> energies (meV) of the peaks of the hydrogen DOS
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
        h_peaks[_cell] = _energy[_peaks]
        summary.append({
            "cell": _cell, "frames": len(_velocities), "frame spacing (fs)": dt_fs * every,
            "resolution (meV)": round(resolution_mev(len(_velocities), dt_fs * every), 3), "hydrogen peaks": len(_peaks),
        })
    return h_peaks, spectra, summary


@app.cell
def _(summary):
    # derived: trajectory length and energy resolution of each DOS
    mo.ui.table(pd.DataFrame(summary).astype({"cell": object}), label="Velocity trajectories and DOS resolution", selection=None)
    return


@app.cell
def _(h_peaks, spectra):
    # derived: the C-H and O-H stretch bands of the hydrogen DOS, from its peaks
    stretch_bands = {"C-H stretch": (350, 420), "O-H stretch": (440, 480)}
    _rows = []
    for _cell, (_energy, _, _g_h) in spectra.items():
        for _band, (_lo, _hi) in stretch_bands.items():
            _in = (_energy >= _lo) & (_energy < _hi)
            _peak_energy = h_peaks[_cell][(h_peaks[_cell] >= _lo) & (h_peaks[_cell] < _hi)]
            _rows.append({
                "cell": _cell, "band": _band, "peaks": len(_peak_energy),
                "lowest (meV)": round(float(_peak_energy.min()), 1), "highest (meV)": round(float(_peak_energy.max()), 1),
                "strongest (meV)": round(float(_energy[_in][np.argmax(_g_h[_in])]), 1),
            })
    mo.ui.table(pd.DataFrame(_rows).astype({"cell": object, "band": object}), label="Stretch bands of the hydrogen DOS (C-H: 350-420 meV, O-H: 440-480 meV)", selection=None)
    return (stretch_bands,)


@app.cell
def _(measured, spectra, stretch_bands):
    _cell = "2x2x1" if "2x2x1" in spectra else next(iter(spectra))
    energy_meV, g, g_h = spectra[_cell]
    table = pd.concat(
        [
            pd.DataFrame({"energy (meV)": energy_meV, "g(E)": g, "which": "total"}),
            pd.DataFrame({"energy (meV)": energy_meV, "g(E)": g_h, "which": "hydrogen"}),
        ]
        + ([measured.assign(which="measured")] if measured is not None else [])
    )
    dos_fig = (
        alt.Chart(table[table["energy (meV)"] <= 600])
        .mark_line()
        .encode(
            x=alt.X("energy (meV):Q", title="energy (meV)"),
            y=alt.Y("g(E):Q", title="g(E) (1/meV, area 1)"),
            color=alt.Color("which:N", title="curve"),
        )
        .properties(title=f"Vibrational DOS from MD velocities, {_cell} cell, up to 600 meV", width=560, height=300)
    )
    _energy, _, _g_h = spectra[_cell]
    _marks = []
    for _band, (_lo, _hi) in stretch_bands.items():
        _in = (_energy >= _lo) & (_energy < _hi)
        _i = np.flatnonzero(_in)[np.argmax(_g_h[_in])]
        _marks.append({"energy (meV)": float(_energy[_i]), "g(E)": float(_g_h[_i]), "label": f"{_energy[_i]:.1f} meV"})
    _labels = alt.Chart(pd.DataFrame(_marks)).mark_text(dy=-10, fontWeight="bold").encode(x="energy (meV):Q", y="g(E):Q", text="label:N")
    mo.ui.altair_chart(dos_fig + _labels)
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
    low_fig = (
        alt.Chart(low[low["energy (meV)"] <= 30])
        .mark_line()
        .encode(
            x=alt.X("energy (meV):Q", title="energy (meV)"),
            y=alt.Y("g(E):Q", title="g(E) (1/meV, area 1)"),
            color=alt.Color("cell:N", title="cell"),
        )
        .properties(title="Lattice region of the DOS by cell size (convergence)", width=560, height=300)
    )
    mo.ui.altair_chart(low_fig)
    return


if __name__ == "__main__":
    app.run()
