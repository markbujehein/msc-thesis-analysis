# Thymol: from a crystal structure to a simulated neutron spectrum

MSc thesis workspace. The aim is to predict the **inelastic neutron scattering (INS) spectrum of crystalline thymol** (C10H14O) from a classical force field, and to compare it with a measured spectrum from the TOSCA spectrometer (ISIS). Everything is reproducible from one `pixi.toml`; every scientific step is written down in [`LOG.md`](LOG.md).

All energies are in **meV**. Status labels used below: **DONE** (works and is tested), **WIP** (in progress), **PLANNED** (not started).

## How the pieces fit

```mermaid
flowchart LR
    A["Predicted crystal structures<br/>Salager 2010, COD 4101953-71<br/><b>DONE</b>"] --> B["PDB supercells<br/>thymol_cif/ and pdb/<br/><b>DONE</b>"]
    B --> C["Flexible GAFF2 MD, 10 K<br/>OpenMM, md/<br/><b>DONE</b>"]
    C --> D["Vibrational DOS<br/>from velocities<br/><b>DONE</b>"]
    C --> E["Relaxed cell, Hessian,<br/>supercell unfolding<br/><b>DONE</b>"]
    E --> F["INS per TOSCA detector<br/>abinslib, analysis/<br/><b>WIP</b>"]
    R["Raw TOSCA runs<br/>TSC25989, TSC25990"] --> S["Reduction with Mantid<br/><b>DONE</b>"]
    S --> T["Reduced spectra<br/>data/reduced/<br/><b>DONE</b>"]
    F --> U["Overlay and scale fit<br/><b>WIP</b>"]
    T --> U
    U --> W["Bayesian band model<br/>dynesty<br/><b>PLANNED</b>"]
    IR["FTIR and Raman<br/>band positions in meV<br/><b>PLANNED</b>"] --> U
    VR["VESUVIO runs"] --> VM["Mantid reduction: transmission,<br/>forward, back, virtual diffraction, gamma<br/><b>PLANNED</b>"]
    VM --> VF["Neutron Compton scattering fit<br/>composition, cross-section, below 25 meV<br/><b>PLANNED</b>"]
    VF --> U
    R --> Q["QENS on TOSCA data<br/>last step<br/><b>PLANNED</b>"]
    SYN["Synthetic stand-in data<br/>data/<br/><b>PLANNED</b>"] -.-> T
    classDef done fill:#e3f1e8,stroke:#2f6b4f,color:#14281e
    classDef wip fill:#fff1c9,stroke:#a06b00,color:#2b1d00,stroke-dasharray:5 4
    classDef planned fill:#ececec,stroke:#777,color:#222,stroke-dasharray:2 4
    class A,B,C,D,E,R,S,T done
    class F,U wip
    class W,IR,VM,VF,Q,SYN planned
```

**WIP detail:** the INS code is written and tested on a small fixture. Its run on the real force constants and the overlay with TSC25990 come next. The planned branches are specified in [`docs/superpowers/specs/2026-11-07-extended-data-design.md`](docs/superpowers/specs/2026-11-07-extended-data-design.md).

## Status

| Step | Status | Notes |
|---|---|---|
| Structure choice and PDB cells | **DONE** | Structure 3 of Salager et al. (R-3, best NMR match); unit cell and 2x2x1 supercell |
| Classical MD and velocity DOS | **DONE** | 1x1x1 DOS: C-H stretch bands at about 376-396 meV, O-H at about 462-467 meV |
| Hessian of the 2x2x1 supercell, unfolded to force constants | **DONE** | no imaginary modes; 936 C-H and 72 O-H stretch modes |
| TOSCA reduction of the two thymol runs | **DONE** | method in `data/REDUCTION.md` (git-ignored, see Data) |
| Harmonic thermodynamics from the DOS (U, S, F, Cv) | **WIP** | code and tests done; values not yet logged |
| INS spectrum on the real force constants, overlay with TSC25990 | **WIP** | |
| Pixi test, fix and lint tasks | **WIP** | defined in `pixi.toml` |
| Synthetic stand-in data in `data/` | **PLANNED** | lets a fresh clone run without the unpublished measurements |
| Bayesian band model | **PLANNED** | own plan, after the overlay |
| FTIR and Raman cross-checks | **PLANNED** | band positions in meV against TOSCA and the simulation; Raman at 290 K and 6 K; low priority |
| VESUVIO: reduction and neutron Compton scattering fit | **PLANNED** | transmission, forward, back, virtual diffraction, gamma; composition, cross-section, sub-25 meV information |
| QENS on TOSCA data | **PLANNED** | last step, after everything above works |
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
| `docs/` | design specs, implementation plan, tutorials, task tracker |
| `LOG.md`, `refs.bib` | dated research log; bibliography |

## Working rules

- **Test first.** Code is written after a failing test; unit tests never run a simulation.
- **Log every scientific change** in `LOG.md`, with the time taken from the shell.
- **Sources are cited** in `refs.bib`.
- **Unpublished data never enters git.**
- **Guard rails** (Claude Code hooks in `.claude/`): a log check, a task-tracker check and a guard that blocks silently dropped packages from `pixi.toml`.
