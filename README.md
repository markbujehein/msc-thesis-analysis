# Thymol: from a crystal structure to a simulated neutron spectrum

MSc thesis workspace. The aim is to predict the **inelastic neutron scattering (INS) spectrum of crystalline thymol** (C10H14O) from a classical force field, and to compare it with a measured spectrum from the TOSCA spectrometer (ISIS). Everything is reproducible from one `pixi.toml`; every scientific step is written down in [`LOG.md`](LOG.md).

All energies are in **meV**. Status labels used below: **DONE** (works and is tested), **WIP** (in progress), **PLANNED** (not started), **BLOCKED** (waiting on something outside the repo).

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
    U --> V["Bayesian band model<br/>dynesty<br/><b>PLANNED</b>"]
    classDef done fill:#e3f1e8,stroke:#2f6b4f,color:#14281e
    classDef wip fill:#fff1c9,stroke:#a06b00,color:#2b1d00,stroke-dasharray:5 4
    classDef planned fill:#ececec,stroke:#777,color:#222,stroke-dasharray:2 4
    class A,B,C,D,E,R,S,T done
    class F,U wip
    class V planned
```

**WIP detail:** the INS code is written and tested on a small fixture. Its run on the real force constants and the overlay with TSC25990 come next.

## Status

| Step | Status | Notes |
|---|---|---|
| Structure choice and PDB cells | **DONE** | Structure 3 of Salager et al. (R-3, best NMR match); unit cell and 2x2x1 supercell |
| Classical MD and velocity DOS | **DONE** | 1x1x1 DOS: C-H stretch bands at about 376-396 meV, O-H at about 462-467 meV |
| Hessian of the 2x2x1 supercell, unfolded to force constants | **DONE** | no imaginary modes; 936 C-H and 72 O-H stretch modes |
| TOSCA reduction of the two thymol runs | **DONE** | method in [`data/REDUCTION.md`](data/REDUCTION.md) |
| Harmonic thermodynamics from the DOS (U, S, F, Cv) | **WIP** | code and tests done; values not yet logged |
| INS spectrum on the real force constants, overlay with TSC25990 | **WIP** | |
| Pixi test, fix and lint tasks | **WIP** | defined in `pixi.toml` |
| Bayesian band model | **PLANNED** | own plan, after the overlay |
| Measured crystal structure (CSD THYMOL) | **BLOCKED** | download needs a CCDC login; until then the structure is a prediction |

Model: GAFF2 with AM1-BCC charges, not fitted. Open work is tracked in [`docs/TASKS.md`](docs/TASKS.md).

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
| `data/` | reduced TOSCA spectra, detector table, reduction notes (raw files are not in git) |
| `tests/` | `unit/` (no simulation) and `integration/` (runs the engines), one folder per area |
| `docs/` | design spec, implementation plan, tutorials, task tracker |
| `LOG.md`, `refs.bib` | dated research log; bibliography |

## Working rules

- **Test first.** Code is written after a failing test; unit tests never run a simulation.
- **Log every scientific change** in `LOG.md`, with the time taken from the shell.
- **Sources are cited** in `refs.bib`.
- **Guard rails** (Claude Code hooks in `.claude/`): a log check, a task-tracker check and a guard that blocks silently dropped packages from `pixi.toml`.
