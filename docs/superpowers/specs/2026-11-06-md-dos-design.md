# MD to DOS pipeline for crystalline thymol: design

Status: **draft for the user's review, amended 2026-11-06 22:15** (sections "Measured data", "Analysis environment", "Thermodynamics" and "Bayesian band model" are new and not yet approved). The `md/` modules and notebooks in the sections below exist and were run (see `LOG.md`); the new sections are design only.

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

## Measured data (new)

`data/zeppelin-experimental-data/` holds ten TOSCA files, two of them thymol: TSC25990 (T < 18 K, the comparison for the 10 K MD) and TSC25989 (T < 220 K). The rest are p-cymene and are out of scope here. Each file holds all detectors and has to be reduced with Mantid. Method, code and results so far: `data/REDUCTION.md`, `analysis/reduce_tosca.py`, output `data/reduced/*.csv` (two bank spectra on a meV axis).

Open points that decide how the measured and simulated spectra can be compared (none resolved): background and calibration runs are not in the folder; the Mantid output is an energy-transfer spectrum, not a DOS, and the conversion (and what to do with Q along the TOSCA trajectory, Debye-Waller, multiple scattering) needs a decision; the 30 percent intensity difference between the two banks is unexplained.

## Analysis environment (new)

> Update 2026-11-07: `md/pixi.toml` and `analysis/pixi.toml` are merged into one root `pixi.toml` with environments `md`, `ins` and `mantid`; the per-folder manifests named below are the earlier layout.

Analysis tools are kept apart from simulation tools because their dependencies can clash. `md/` (OpenMM, openmmforcefields, MDANSE) is unchanged. `analysis/` has its own pixi environment: Mantid 7.0.0 and, newly, `dynesty` (unpinned; not yet installed, the lock file is stale). Data crosses between the two as files only: `md/output/*.f32` or a DOS CSV in, `data/reduced/*.csv` in. The DOS code in `md/dos.py` stays where it is; the new analysis code reads its output.

## INS simulation (new)

Purpose of the whole project, as stated by the user: the DOS is a step towards simulating INS spectra; the measured TOSCA spectrum is a reference for the simulation, not the subject of an analysis.

AbINS (Mantid) and its standalone successor `abinslib` do not accept a DOS: they need frequencies and atomic displacements (eigenvectors) of a harmonic model (checked in Mantid 7.0.0, `scripts/abins/input/`). Route chosen by the user: **GAFF2 Hessian to abinslib.**

Pipeline (design only, nothing built; each stage as a tested function):
1. OpenMM Hessian (force constants) of the GAFF2 system at the minimised structure, by central differences of forces. **Cost measured** (throwaway probe, 450-atom cell, Gamma point only): 2.3 s on the OpenMM CPU platform (0.8 ms per force evaluation), 17 s on the double-precision Reference platform. **Not solved: a true minimum.** `LocalEnergyMinimizer` stalls with a maximum force of 49 kJ/mol/nm on both platforms and the Hessian there has imaginary modes (CPU: 20, smallest w^2 = -126 ps^-2; Reference: 7, about 37 meV imaginary at worst). Following the imaginary modes and re-minimising (5 cycles) lowered the energy by 11 kJ/mol (-2709.9 to -2721.2) but left 3 imaginary modes (worst about 22 meV) and a maximum force of 19 to 50 kJ/mol/nm. Untested guesses for the cause: the nonbonded cutoff without a switching function makes the energy non-smooth; soft methyl/isopropyl rotor modes; the predicted structure is not a GAFF2 minimum. **Resolved (22:50): the cause was the cutoff.** Adding a switching function (starts at 0.5 nm, cutoff 0.6 nm) and the dispersion correction to the `NonbondedForce` made the minimiser converge in one cycle: maximum force 1.68 kJ/mol/nm, no imaginary modes, 3 modes below 0.5 meV (the translations), lowest internal modes 2.1 to 2.2 meV. Mode groups at Gamma (Reference platform, double precision, 450 atoms, 1350 modes): 351 modes below 60 meV, 747 between 60 and 230 meV, none between 221 and 374 meV, 234 C-H modes at 374.4 to 395.1 meV (13 per molecule times 18), 18 O-H modes at 459.9 to 465.4 meV (mean 463.0). This agrees in structure with the MD DOS peaks (376 to 396 and 462 to 467 meV, gap 221 to 376 meV). **Consequence to decide:** `md/build.py` does not set a switching function, so the MD runs already done use a slightly different, non-smooth potential than this Hessian. Whether to add the switching function to `build.py` (test first) and rerun the MD is open. The probe script was throwaway, so the Hessian code and its tests still have to be written.

A Gamma-only cell gives no dispersion: a q-mesh needs a supercell Hessian (2x2x1, 1800 atoms, 5400 degrees of freedom, not run) and unfolding.
2. Convert to Euphonic `ForceConstants` (the workshop reads phonopy `phonopy.yml` plus `force_constants.hdf5`). **Checked at Gamma:** building `Crystal` and `ForceConstants` directly from the OpenMM Hessian (units: 1 kJ/mol/nm^2 = 0.10364 meV/A^2) and calling `calculate_qpoint_phonon_modes` in the `analysis` env (Euphonic 1.6.2) reproduces my own eigenfrequencies of the top 400 modes to within 0.012 meV, and returns eigenvectors of shape (1, 1350, 450, 3). That Hessian had imaginary modes, so this checks the conversion only.
3. Euphonic: frequencies and eigenvectors on a q-mesh; `abinslib`: temperature-dependent displacements (10 K), almost-isotropic powder-averaged incoherent approximation with the TOSCA geometry (135 degree backward bank, final energy 3.97 meV, orders 1 and 2).
4. `resins` (TOSCA, `AbINS_v1`) for the resolution, then resample onto the log-bin energy axis of the reduced data and overlay. The `resins` TOSCA model `AbINS_v1` is the same polynomial as the Abins parameter quoted under "Bayesian band model": sigma = 0.30996 + 0.005 E + 8.0655e-7 E^2 meV, which is a = 1e-7, b = 0.005, c = 2.5 in cm^-1 converted at 8.0655 cm^-1 per meV (checked by arithmetic from the `resins` 0.1.0 wheel, read from a scratch download, not installed). Its citations: Dymkowski et al., Physica B 551 (2018) 443, doi 10.1016/j.physb.2018.02.034, and Cheng et al., J. Chem. Theory Comput. 15 (2019) 1974, doi 10.1021/acs.jctc.8b01250 (not yet in `refs.bib`). `resins` also has a physical "book" model (Mitchell et al., 2005) whose backward-bank average final energy is 3.32 meV, against 3.97 meV in Abins and the workshop.

**Decision (user, 22:40): do not hardcode the final energy (or the scattering angle). They depend on the detector (time of flight geometry).** Checked in Mantid's `TOSCA_Definition_2016.xml`: every detector has its own `Efixed` and angle. Backward bank: 70 detectors, Efixed 2.690 to 4.297 meV (mean 3.372), 2 theta 127.0 to 140.8 degrees. Forward bank: 70 detectors, Efixed 2.688 to 4.294 meV (mean 3.394), 2 theta 38.9 to 53.1 degrees. So 3.97 meV and 135 degrees (Abins, workshop) and 3.32 meV (book) are all single-value approximations. Design consequence: read Efixed and 2 theta per detector from the instrument definition and compute the Q^2(E) per detector (or per group), instead of one constant. Whether `abinslib`'s Q^2 helper accepts per-detector values is unchecked.
5. The MD DOS from `md/` is kept as a validation: does the harmonic Hessian DOS match the 10 K MD DOS?

Reference: the workshop notebooks `/home/mark/Projects/mdanse2026_workshop/05_ins_simulations/` (MACE via `janus-core` is the workshop's force-constant source; here an alternative, not planned now).

Environments: `abinslib`, `resins` (PyPI) are in neither `md/pixi.toml` nor `analysis/pixi.toml`. Euphonic 1.6.2 is already in `analysis/`. The OpenMM Hessian runs in `md/`, `abinslib` and `resins` would go into `analysis/`, with force constants crossing as files. **Conflict found:** `abinslib` 0.3.0 requires `euphonic>=2.0.0,<3` (and `resins==0.1.0`, Python >=3.11, PyPI metadata), while the Mantid 7.0.0 package in `analysis/` requires `euphonic >=1.6.0,<2.0` (from `analysis/pixi.lock`) and Python 3.13. They cannot share one environment, which is why the workshop keeps Mantid apart. Solution (user's suggestion, 22:40): one `analysis/pixi.toml` with two environments through a pixi feature: `default` (Mantid, reduction) and `ins` (`abinslib`, `resins`, `dynesty`; simulation and fitting). The `ins` feature and `[environments]` table were added to the manifest by editing the text only. **Untested:** no pixi command was run, so the manifest has not been parsed or solved and `pixi.lock` does not contain `ins`. Data crosses between the two as files (`data/reduced/*.csv`).

## Thermodynamics (new)

`ase.thermochemistry.CrystalThermo` (ASE is in the `md` environment) takes a DOS and returns zero-point energy, internal energy, entropy, free energy and heat capacity from the quantum harmonic formulas. Plan: normalise g(E) to 3N modes per cell (1x1x1 is the per-cell reference; 2x2x1 divided by 4 is the cross-check and its difference gives a scale for the error), then tabulate against T. Lives in a new small module (name open), with tests first. Caveats to state with the numbers: the MD DOS is classical and anharmonic, the harmonic quantum formulas applied to it are an approximation, and the force-field limits below apply.

## Bayesian band model (new)

Method taken from the workshop notebook `/home/mark/Projects/mdanse2026_workshop/07_benzene_qens/3_bayesian_model_selection.ipynb`: nested sampling (`dynesty`), evidence for model selection, posterior samples as a by-product, posterior samples drawn against the data as the fit check. **Scope (user, 22:25 to 22:40): the TOSCA data are a reference for the simulation, not the subject of analysis.** The primary comparison is the simulated INS spectrum from "INS simulation" overlaid on the measurement. The Bayesian band fit is a secondary, narrower tool: it gives band positions and widths with credible intervals for the resolved bands, as numbers to judge the simulation by. Recommended scope, not yet confirmed by the user: resolved groups only (C-H and O-H regions, a few isolated low-energy peaks), no whole-range fit.

**The data are the measured TOSCA spectra** (TSC25990, 18 K; TSC25989 later for temperature), not synthetic data and not the MD DOS. The first question: how many bands does the measured spectrum support? The MD DOS is then compared with the fitted bands (and could later inform priors; not decided). Model: a sum of K bands (Gaussian or damped oscillator: amplitude, centre, width) plus a smooth term for the dense lattice region; K chosen by log evidence.

Decisions and open points:
- Binning: the fit must not use coarser bins than the reduction needs. Measured on TSC25990 (Mantid, no rebin): the native TOF channels give 9975 energy bins, 0.09 percent of E wide at 5 meV, 0.15 percent at 36 meV, 0.23 percent at 100 meV and 0.48 percent at 460 meV. The `REBIN` string in `reduce_tosca.py` (0.5 percent steps) is 1 to 5 times coarser than that up to about 400 meV. Merging channels adds counts and is harmless while the bins stay well below the instrument resolution, and the resolution check is in the next bullet. Plan: keep the 0.5 percent rebin as the working binning (at least 3 bins per resolution FWHM everywhere), compare one fit at native binning as a check, and evaluate the model as a bin integral.
- Instrument resolution (found in Mantid, `scripts/abins/parameters.py` of the analysis env, used by `abins/instruments/toscainstrument.py`): a Gaussian with sigma = a w^2 + b w + c, w in cm^-1, a = 1e-7, b = 0.005, c = 2.5 (sigma in cm^-1; 8.0655 cm^-1 per meV). This is Abins's empirical fit; I did not trace its original source, so it needs a reference before the thesis uses it. In meV: FWHM 0.79 at 5 meV (15.8 percent of E), 0.97 at 20, 1.16 at 36, 1.93 at 100, 3.16 at 200, 5.74 at 400, 6.55 at 460 meV (1.4 percent). Against the native channels the FWHM is 168 / 41 / 22 / 8 / 5 / 3 / 3 times wider (same energies); against my rebin 32 / 10 / 6 / 4 / 3 / 3 / 3 times wider. So the 0.5 percent rebin loses no resolution-limited information; the native binning is heavily oversampled below 100 meV, and only helps the bin-integral treatment. The intrinsic band widths are only meaningful with this resolution convolved into the model.
- Other TOSCA values in the same Mantid files: final neutron energy 32 cm^-1 (3.97 meV, settles the Efixed question in `data/REDUCTION.md`), detector angles 45 degrees (forward) and 134.99 degrees (backward); the Q^2 trajectory follows from these.
- Open: how Q varies along the TOSCA trajectory and what intensity weighting (neutron cross-section, Debye-Waller) is applied to the model bands.
- Noise: the reduced errors from Mantid (counts per meV with propagated errors) replace the workshop's "5 percent of the data" (it breaks at zero). Whether those errors and a Gaussian likelihood are adequate at low counts (high E) is untested; Poisson on counts is the alternative.
- Simulated side: the MD DOS gets block-averaged errors (e.g. 10 blocks of 10 ps) only for the comparison with the fitted bands.
- Open: fit the whole 0 to 500 meV range with a lattice term, or only the resolved high-energy groups (C-H near 376 to 396 meV, O-H near 462 to 468 meV in our runs) first?
- Force-field scale factors as a second tier (Hessian forward model, evidence for "GAFF2 as is" against "scaled") are chosen as a later step, not part of the first plan.

## Force field (note)

GAFF2 (`gaff-2.11`) with fixed bonded terms and fixed charges. Charges are AM1-BCC: the system build asks for them and fails without `antechamber` on `PATH` (observed when I ran the env's Python directly, outside pixi). Its O-H stretch (464 meV in our runs) is expected to sit above the crystal value because hydrogen-bond softening is missing; this is the first thing the TOSCA comparison can test.

## Not now

NPT cell relaxation, neutron-weighting and Debye-Waller corrections (needed before a quantitative comparison with TOSCA, see "Measured data"), a second force field (OpenFF Sage), machine-learned potentials, cluster scripts, force-field inference by sampling, p-cymene.

## Open questions for the user

1. Production length for the first run (suggest 100 ps, then judge the noise)?
2. OK to write only velocities (not positions) to keep files small?
3. Should `md/` tests run on the 25-atom test molecule only, or also on the full 1800-atom system (slower)?
