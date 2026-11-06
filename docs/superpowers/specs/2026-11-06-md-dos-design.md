# MD to DOS pipeline for crystalline thymol: design

Status: **draft for the user's review.** No code exists for this yet except the unpopulated notebook stubs.

## Goal

Get the vibrational density of states (DOS) of crystalline thymol from classical MD, to compare with measured INS (TOSCA) and DINS (VESUVIO) spectra. Energies in meV.

## Decisions taken (from the user's answers)

| Question | Decision |
|---|---|
| Target temperature | about 10 K (TOSCA) |
| Where it runs | local testing first; cluster later, unspecified |
| Force field, first pass | simplest and best supported: GAFF2 (`gaff-2.11`) through openmmforcefields and AmberTools, flexible (`constraints=None`), no hydrogen mass repartitioning |
| Starting cell | predicted Structure 3 (`thymol_cif/4101955.cif`, PDBs in `pdb/`) |
| Structure of the code | plain tested modules in `md/` (option 1) plus a minimal set of marimo notebooks that call them |
| Method | TDD (test first, watch it fail), see `CLAUDE.md` |

Approximations accepted by the user for the experiment: harmonic approximation, powder average. Incoherent approximation follows (hydrogen dominates), so the target is the H-weighted DOS.

## Modules (plain Python, tested with pytest)

| File | Functions (planned) | First tests (written before the code) |
|---|---|---|
| `md/dos.py` | `dos(velocities, dt_fs)` returns energy in meV and g(E); `resolution_mev(n_frames, dt_fs)` | a synthetic oscillator of known energy gives a peak within 2 bins; resolution equals h/(N dt); a flat input does not produce a spurious peak |
| `md/build.py` | `read_pdb(path)`; `bonds_from_geometry(atoms)`; `make_system(pdb, smiles, cutoff_nm)` | 2x2x1 PDB: 1800 atoms, 72 residues; every molecule has 25 bonds; system has 0 constraints and 1800 particles; finite energy after minimisation |
| `md/run.py` | `VelocityReporter(path, every)`; `run(system, ...)` | reporter writes (n_frames, n_atoms, 3) float32 at the right interval on a 25-atom test molecule; a 100-step run ends with finite energies |

Note: `dos.py` needs only numpy. `build.py` and `run.py` need the installed environment (OpenMM, openmmforcefields, ambertools).

## Notebooks (marimo, minimal set, created empty)

Each notebook only calls the modules above and shows results. Logic stays in the modules so pytest covers it. Notebooks are plain `.py` files, so `python md/01_system.py` runs one headless.

| Notebook | What it should do |
|---|---|
| `md/01_system.py` | load the PDB, show cell and molecule counts, run the bond check, build the GAFF2 system, show the checks (constraints = 0, energy after minimisation), report the O-H force constant and its harmonic energy in meV |
| `md/02_run.py` | set parameters (T = 10 K, dt = 0.5 fs, write interval, lengths), minimise, equilibrate with a thermostat, then run production without one (NVE), plot temperature and energy, write the velocity file |
| `md/03_dos.py` | load the velocity file, compute total and H-projected DOS in meV, show the resolution, compare 1x1x1 against 2x2x1 below about 30 meV (convergence), leave a slot to overlay the measured spectrum later |

## Settings that matter (and why)

- **Time step 0.5 fs, no constraints.** OpenMM docs: unconstrained runs are typically limited to about 1 fs; constraints would remove the O-H and C-H stretches from the spectrum.
- **Write velocities every 4 steps (2 fs).** The Nyquist limit is h/(2 x 2 fs) = about 1030 meV, above the O-H stretch (my estimate about 460 meV for GAFF2). Size: 1800 atoms x 3 x 4 bytes = 21.6 kB per frame, about 1.1 GB for 100 ps. Writing every 2 steps doubles that.
- **Resolution** is h/(N dt): 100 ps gives about 0.04 meV, far finer than TOSCA, so the production length is set by statistics, not resolution.
- **No hydrogen mass repartitioning, no HBonds constraints**, even though the openmmforcefields docs use both in their example. They change the H vibrations.
- **Production without a thermostat (NVE)** after equilibration, so the dynamics are not disturbed. At 10 K the system is near-harmonic.
- **Cell size.** 2x2x1 (1800 atoms) because the cell must be wider than twice the cutoff (12.7 A perpendicular width, so 1 nm works). It samples 12 q-points of the primitive Brillouin zone; the intramolecular part is insensitive to this, the lattice region below about 30 meV is not, so `03_dos.py` includes the convergence comparison. This is reasoning from general knowledge, not yet tested.

## Known limits (stated, not hidden)

- GAFF2 has a fixed O-H force constant, so there is no hydrogen-bond softening: expect the O-H stretch too high (my estimate: 464 meV against about 400-420 meV expected in the crystal; unverified).
- Methyl rotation and torsion modes at 10 K are quantum; classical MD describes them poorly.
- VESUVIO (DINS) measures the proton momentum distribution; at 10 K it is mostly zero-point, so MD gives it only through a harmonic quantum formula applied to the MD DOS. Not part of this first design.
- Structure 3 is predicted, not measured; its cell may differ from the experimental one by a few percent (unverified for the pure compound).

## Not now

NPT cell relaxation, neutron-weighting and Debye-Waller corrections, a second force field (OpenFF Sage), machine-learned potentials, cluster scripts.

## Open questions for the user

1. Production length for the first run (suggest 100 ps, then judge the noise)?
2. OK to write only velocities (not positions) to keep files small?
3. Should `md/` tests run on the 25-atom test molecule only, or also on the full 1800-atom system (slower)?
