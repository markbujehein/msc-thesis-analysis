![Vibrational spectra of molecular crystals](docs/figures/banner.svg?v=bc01f05)

# Thymol: from a crystal structure to a simulated neutron spectrum

Workspace for simulation and analysis. The aim is to predict the **inelastic neutron scattering (INS) spectrum of crystalline thymol** (C10H14O) from a classical force field, and to compare it with a measured spectrum from the TOSCA spectrometer (ISIS). Everything is reproducible from one `pixi.toml`; every scientific step is written down in [`LOG.md`](LOG.md).

All energies are in **meV**. Status labels used below: **DONE** (works and is tested), **WIP** (in progress), **PLANNED** (not started).

## How the pieces fit

![Pipeline: simulation path, TOSCA measurement path and planned branches, each box labelled DONE, WIP or PLANNED](docs/figures/pipeline.svg?v=75c9a7d)

Solid green is DONE, dashed amber is WIP, dotted grey is PLANNED. Dotted arrows are planned links.

**WIP detail:** the INS code is written and tested on a small fixture. Its run on the real force constants and the comparison with the measured spectrum come next.

## Status

| Step | Status | Notes |
|---|---|---|
| Structure choice and PDB cells | **DONE** | Structure 3 of Salager et al. (R-3, best NMR match); unit cell and 2x2x1 supercell |
| Classical MD and velocity DOS | **DONE** | 1x1x1 DOS: C-H stretch bands at about 376-396 meV, O-H at about 462-467 meV |
| Hessian of the 2x2x1 supercell, unfolded to force constants | **DONE** | no imaginary modes; 936 C-H and 72 O-H stretch modes |
| TOSCA reduction of the two thymol runs | **DONE** | method in `data/REDUCTION.md` (git-ignored, see Data) |
| Harmonic thermodynamics from the DOS (U, S, F, Cv) | **WIP** | code and tests done; values not yet logged |
| INS spectrum on the real force constants, overlay | **WIP** | |
| Pixi test, fix and lint tasks | **WIP** | defined in `pixi.toml` |
| Synthetic stand-in data in `data/` | **PLANNED** | lets a fresh clone run without the unpublished measurements |
| Bayesian band model | **PLANNED** | own plan, after the comparison |
| Better force fields: MACE, ANI-2x, AIMNet2, UMA, AMOEBA | **PLANNED** | candidates for higher accuracy than GAFF2, replacing it in the MD and Hessian steps; MACE, ANI-2x, AIMNet2 and UMA are machine-learned (UMA is trained on the OMol25 molecular data and the OMC25 molecular-crystal data), AMOEBA is a classical polarizable field |
| FTIR and Raman cross-checks | **PLANNED** | band positions in meV against TOSCA and the simulation; low priority |
| VESUVIO: neutron Compton scattering | **PLANNED** | foil-cycling reduction, fit per atomic mass, hydrogen momentum width and kinetic energy, compared with the simulated hydrogen dynamics |
| VESUVIO: cross-section and low energy | **PLANNED** | transmission and cross-section of the sample; the region below 25 meV as a complement to TOSCA |
| VESUVIO: diffraction | **PLANNED** | check of the crystal structure against the predicted one |
| QENS check on the TOSCA data | **PLANNED** | exploratory: first find out whether the data show any quasi-elastic signal; it may find nothing. The supervisor has used the method before |
| Measured crystal structure (CSD THYMOL) | **PLANNED** | download needs a CCDC login; until then the structure is a prediction |

Model: GAFF2 with AM1-BCC charges, not fitted. Open work is tracked in [`docs/TASKS.md`](docs/TASKS.md).

## Data

The measurements (TOSCA, FTIR, Raman, VESUVIO) and the DFT inputs are **unpublished and git-ignored**: `data/zeppelin-experimental-data/`, `data/reduced/`, `data/REDUCTION.md`, `dft/zeppelin-dft-input/`. `data/` itself is tracked and will hold synthetic stand-in data with the same layout, so that a fresh clone can run the code and the tests.

## Environments

One manifest, one lock file. Mantid 7 pins Python 3.13 and euphonic below 2, while abinslib needs euphonic 2 or later, so the science tools cannot share an environment. Features are combined into environments in [`pixi.toml`](pixi.toml).

| Environment | Used for | Main packages |
|---|---|---|
| `md` | simulation, DOS, notebooks | OpenMM, openmmforcefields (GAFF2), AmberTools, RDKit, MDANSE, MDAnalysis, ASE, marimo |
| `ins` | INS simulation and fitting | abinslib, resins, euphonic 2, dynesty, MDAnalysis, ASE, marimo |
| `mantid` | TOSCA data reduction | Mantid 7 and workbench, dynesty |
| `test-md`, `test-ins`, `test-mantid` | tests, same package versions as their parent | pytest on top of the parent |
| `fix` | lint, format, docstring style | ruff |

## Run it

```bash
pixi install --all                  # builds all environments (several GB)
pixi run test-unit-all              # unit tests and doctests, no simulation
pixi run test-integration-all       # slow: runs OpenMM, Mantid, AmberTools
pixi run -e fix lint                # check style (rules in ruff.toml)
pixi run -e fix fix                 # apply fixes and format

cd md
pixi run -e md marimo edit 03_dos.py              # notebooks: 01_system, 02_run, 03_dos, 04_hessian
pixi run -e md python 02_run.py -- --cell 1x1x1   # or run one as a script
```

## Repository map

| Path | Contents |
|---|---|
| `thymol_cif/` | the 23 predicted structures (CIF) and the scripts that build and check the PDB files |
| `pdb/` | thymol unit cell (450 atoms) and 2x2x1 supercell (1800 atoms) |
| `md/` | system build, MD run, DOS, Hessian, supercell unfolding, thermodynamics; marimo notebooks `01` to `04` |
| `analysis/` | TOSCA reduction (Mantid), per-detector INS simulation (abinslib), comparison with data |
| `data/` | detector table; synthetic stand-in data (planned); real data is git-ignored |
| `dft/` | future DFT vibrational calculations (real inputs are git-ignored) |
| `tests/` | `unit/` (no simulation) and `integration/` (runs the engines), one folder per area |
| `docs/` | design specs, implementation plan, tutorials, task tracker; `figures/` holds the README banner and pipeline (SVG) and the scripts that draw them |
| `LOG.md`, `refs.bib` | dated research log; bibliography |
