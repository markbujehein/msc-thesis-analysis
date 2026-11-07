# INS from the GAFF2 Hessian: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the GAFF2 crystal of thymol into a simulated TOSCA INS spectrum (harmonic, 10 K) that is overlaid on the reduced measurement, plus thermodynamic properties from the MD DOS.

**Architecture:** `md/` (OpenMM) gets a smooth nonbonded potential, a Hessian module and a supercell-unfolding module that write force constants to a file. `analysis/` (environment `ins`: abinslib, resins, euphonic 2) reads that file and a per-detector TOSCA table and simulates the spectrum. Data crosses between the environments only as files.

**Tech Stack:** OpenMM 8 and numpy in `md/`; euphonic 2.1.1, abinslib 0.3.0, resins 0.1.0 in `analysis/` env `ins`; Mantid 7.0.0 in `analysis/` env `default`; ASE `CrystalThermo` in `md/`.

**Spec:** `file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/specs/2026-11-06-md-dos-design.md` (approved by the user 2026-11-06). Not in this plan: the Bayesian band model (own plan, after the overlay of Task 7 exists), force-field scale-factor inference, p-cymene, NPT.

## Global Constraints

- TDD is mandatory (repo `CLAUDE.md`): write the test, run it and see it fail for the right reason, then the minimal code, then green. Report the red and the green run. Docs and data files are exempt.
- Energies in meV (eV only when large), never wavenumbers.
- Force field: GAFF2 `gaff-2.11`, flexible (`constraints=None`), AM1-BCC charges, no hydrogen mass repartitioning. Running the `md` env Python outside pixi needs `PATH=.pixi/envs/md/bin:$PATH` (antechamber).
- Do not hardcode TOSCA final energy or scattering angle: they come per detector from Mantid's `TOSCA_Definition_2016.xml` (user decision, spec "INS simulation").
- Resolution: `resins` `Instrument.from_default('TOSCA')`, model `AbINS_v1` (the same polynomial as the Abins parameters).
- Harmonic temperature 10 K. 1 kJ/mol = 10.364 meV; 1 kJ/mol/nm^2 = 0.10364 meV/A^2.
- Log every scientific step in `LOG.md` (skill `log-entry`; take the time from `date '+%F %H:%M'`). Report anything unverified as unverified.
- No pixi/conda command unless the user asks for that action. (The user ran `pixi install` for `default` and `ins` in `analysis/` on 2026-11-06; nothing else is authorised.)
- Never delete or overwrite what the session did not create without listing it and asking. Commit only when the user asks.
- Replies that mention the spec or this plan link them as absolute `file://` URLs.
- Run commands: md tests `pixi run -e md pytest md/tests/<file> -v`. Analysis tests: `cd analysis && pixi run -e ins python -m unittest tests.<module> -v` (`test_reduce_tosca` and `test_tosca_detectors` need the Mantid environment: `pixi run -e mantid test-reduction`).

## Review Focus

Inputs and conditions the spec implies but the main tests would not catch, most likely first (each is pinned by a test in the named task):

1. A geometry that is not a minimum: `relax` must raise, not return, when imaginary modes remain; mode energies must never be clipped to zero (Task 2).
2. A supercell too small for the interactions, or an atom that does not match any unit-cell atom: the three acoustic modes at Gamma must be near zero and the unmatched atom must raise (Tasks 3 and 4).
3. Zero or negative modes in the thermodynamics: a DOS that contains the 3 translational modes at 0 meV must not produce inf or NaN (Task 8).
4. An incomplete or mixed detector table (not 70 backward and 70 forward): the simulation must refuse it (Tasks 5 and 6).
5. The 1/E factor at the first energy bin (E = 0): the simulated spectrum must be finite (Task 6).

---

### Task 1: Smooth nonbonded cutoff in `build.py`

**Files:**
- Modify: `md/build.py` (function `make_system`)
- Test: `md/tests/test_build.py`

**Interfaces:**
- Consumes: `make_system(path, smiles, cutoff_nm, bar=NoBar) -> (topology, system, positions)` (existing).
- Produces: same signature; the `NonbondedForce` now has `getUseSwitchingFunction() == True`, `getSwitchingDistance() == cutoff_nm - 0.1` nm and `getUseDispersionCorrection() == True`. (The 0.1 nm margin is generalised from the probe that used 0.5 nm for a 0.6 nm cutoff; it is this plan's choice, not the user's.)

- [ ] **Step 1: Write the failing test** `test_nonbonded_cutoff_is_switched` in `md/tests/test_build.py`: build the unit-cell system (`pdb/thymol_structure3_R-3_unitcell.pdb`, cutoff 0.6), find the `NonbondedForce`, assert the three properties above (`switching distance` equals `0.5 nm` within 1e-9).
- [ ] **Step 2: Run it** (`pytest md/tests/test_build.py::test_nonbonded_cutoff_is_switched`). Expected: FAIL on `getUseSwitchingFunction()` being False.
- [ ] **Step 3: Implement** in `make_system`: after `create_system`, call `setUseSwitchingFunction(True)`, `setSwitchingDistance(cutoff_nm - 0.1)` (nm, as an openmm quantity) and `setUseDispersionCorrection(True)` on the `NonbondedForce`.
- [ ] **Step 4: Run the whole `md/tests/test_build.py`.** Expected: all PASS (the existing four plus the new one).
- [ ] **Step 5: Rerun the 1x1x1 MD** to see what the smoother potential changes: `cd md && pixi run -e md python 02_run.py -- --cell 1x1x1` writes `md/output/velocities_1x1x1.f32`, which overwrites the existing file the session created earlier. First copy the old `velocities_1x1x1.f32` and `log_1x1x1.csv` to `md/output/before_switching/`. Then run `03_dos.py` and compare the O-H and C-H peak positions against the old values in `LOG.md` (376 to 396 and 462 to 468 meV). The 2x2x1 rerun is not part of this task (cost not measured; ask the user).
- [ ] **Step 6: Log** in `LOG.md`: the test result, the peak comparison, and that the 2x2x1 MD files predate the switching function.

### Task 2: Hessian module `md/hessian.py`

**Files:**
- Create: `md/hessian.py`
- Test: `md/tests/test_hessian.py`

**Interfaces:**
- Consumes: an `openmm.System` and positions in nm as `np.ndarray (n, 3)`.
- Produces:
  - `finite_difference_hessian(system, positions_nm, h_nm=1e-5, platform="Reference") -> np.ndarray` shape (3n, 3n), kJ/mol/nm^2, symmetrised.
  - `mode_energies_mev(hessian, masses_amu) -> np.ndarray` length 3n, sorted ascending, meV, **negative** for imaginary modes (energy = -hbar sqrt(|w^2|)), never clipped. hbar = 0.6582119569 meV ps; 1 kJ/mol = 1 amu nm^2/ps^2.
  - `relax(system, positions_nm, platform="Reference", max_cycles=5, step_nm=0.02) -> np.ndarray` (n, 3) nm: minimise (tolerance 1e-3, 10000 iterations); while a mode has w^2 < -1 ps^-2, displace by `step_nm` (largest component) along those modes in both signs, minimise again and keep the lower energy; raise `RuntimeError` naming the number of imaginary modes if `max_cycles` is exhausted.

- [ ] **Step 1: Write the failing tests** in `md/tests/test_hessian.py`:
  - `test_dimer_energy_is_hbar_sqrt_k_over_mu`: two particles (masses 16 and 1 amu) joined by a `HarmonicBondForce` with k = 5000 kJ/mol/nm^2, no box; the highest of the 6 energies equals `0.6582119569 * sqrt(k/mu)` within 1e-3 meV and the other five are within 1e-3 meV of 0.
  - `test_unstable_geometry_gives_negative_energy`: a bond with k = -1000 (inverted) returns a minimum energy below -1 meV.
  - `test_relax_raises_when_still_unstable`: the inverted-bond system with `max_cycles=1` raises `RuntimeError`.
  - `test_argon_box_has_three_zero_modes`: `argon_box()` from `md/tests/test_run.py` (import its helper or copy it into a shared `md/tests/conftest.py`), relaxed, gives exactly 3 modes with |E| < 0.5 meV.
- [ ] **Step 2: Run them.** Expected: FAIL with `ModuleNotFoundError: hessian`.
- [ ] **Step 3: Implement the three functions** as specified; central differences of forces on `mm.Context` with a `VerletIntegrator`, one DOF at a time; relaxation as above. Reference: the throwaway probe logic summarised in the spec section "INS simulation".
- [ ] **Step 4: Run the tests.** Expected: all PASS. If `test_argon_box_has_three_zero_modes` fails because the simple-cubic argon box is not a stable minimum, change the fixture to an fcc box and say so in the log; do not loosen the assertion.
- [ ] **Step 5: Log** the red and green runs in `LOG.md`.

### Task 3: Supercell unfolding and the force-constant file `md/supercell.py`

**Files:**
- Create: `md/supercell.py`
- Test: `md/tests/test_supercell.py`

**Interfaces:**
- Consumes: supercell Hessian (3N, 3N) from Task 2; PDB positions of the supercell and of the unit cell, both in nm.
- Produces:
  - `assign_cells(sc_positions_nm, unit_positions_nm, unit_cell_nm, tol_nm=1e-3) -> tuple[np.ndarray, np.ndarray]`: `atom_in_cell (N,)` int and `cell_origin (N, 3)` int, such that `sc_position = unit_position[atom_in_cell] + cell_origin @ unit_cell_nm` modulo the supercell. Raises `ValueError` listing the unmatched atom index if any atom has no match within `tol_nm`.
  - `unfold_hessian(hessian, atom_in_cell, cell_origin, n_cell_atoms) -> tuple[np.ndarray, np.ndarray]`: `origins (n_cells, 3)` int and `fc (n_cells, 3n, 3n)` with `fc[c, i, j] = hessian[ref_i, atom j of cell c]` where `ref_i` is atom i in the origin cell.
  - `save_force_constants(path, fc, origins, sc_matrix, unit_cell_nm, frac_positions, symbols, masses_amu)` and `load_force_constants(path) -> dict` with the same keys, as `.npz`; `fc` stored in kJ/mol/nm^2.

- [ ] **Step 1: Write the failing tests** in `md/tests/test_supercell.py`:
  - `test_unfolded_fc_reproduces_supercell_frequencies`: a 1-atom simple-cubic LJ box as unit cell (a = 0.6 nm), 3x3x3 supercell with cutoff below half the supercell edge; for all 27 commensurate q (n/3), build D(q) = sum_c fc[c] exp(-2 pi i q.origin_c) / sqrt(m m), and assert the sorted union of its eigenvalues equals the sorted eigenvalues of the mass-weighted supercell Hessian to 1e-6 relative.
  - `test_assign_cells_raises_on_unmatched_atom`: move one supercell atom by 0.05 nm; expect `ValueError` naming its index.
  - `test_force_constants_round_trip`: save then load, arrays equal.
- [ ] **Step 2: Run them.** Expected: FAIL with `ModuleNotFoundError: supercell`.
- [ ] **Step 3: Implement** the four functions. Match atoms via fractional coordinates of the unit cell (wrap to [0, 1), compare with tolerance).
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Log** the red and green runs.

### Task 4: Run the supercell Hessian on the real system

**Files:**
- Create: `md/04_hessian.py` (marimo notebook; it only calls `build`, `hessian`, `supercell`, like `01_system.py`)
- Output (new): `md/output/fc_2x2x1.npz`

**Interfaces:**
- Consumes: `make_system`, `relax`, `finite_difference_hessian`, `mode_energies_mev`, `assign_cells`, `unfold_hessian`, `save_force_constants`; PDBs `pdb/thymol_structure3_R-3_unitcell.pdb` (450 atoms, cutoff 0.6 nm) and `pdb/thymol_structure3_R-3_2x2x1.pdb` (1800 atoms, cutoff 1.0 nm); `sc_matrix = diag(2, 2, 1)`.
- Produces: `md/output/fc_2x2x1.npz` and printed checks.

- [ ] **Step 1: Write the notebook** that relaxes the 1800-atom system, computes its Hessian, prints the number of modes with energy below -0.5 meV, the number below 0.5 meV, the maximum force after relaxation, and the groups: modes below 60 meV, 60 to 230 meV, 230 to 350 meV, 350 to 420 meV, 440 to 480 meV. Then unfolds and saves. Its Hessian time is unmeasured (estimate: minutes on the Reference platform; unverified); if it exceeds one hour, stop and ask.
- [ ] **Step 2: Run it headless** (`python md/04_hessian.py`). Expected: 0 imaginary modes; exactly 3 modes below 0.5 meV (if more, the supercell or cutoff is too small: record it and stop); 4 x 234 = 936 modes in 350 to 420 meV and 4 x 18 = 72 in 440 to 480 meV; none between 230 and 350 meV (the unit-cell Gamma values from the spec are 234 and 18 per cell).
- [ ] **Step 3: Log** the printed numbers, including the Hessian wall time, and any deviation from the expected counts. No test file: this is a run of tested modules (the notebooks only call them).

### Task 5: Per-detector TOSCA table `analysis/tosca_detectors.py`

**Files:**
- Create: `analysis/tosca_detectors.py`
- Test: `analysis/tests/test_tosca_detectors.py`
- Output (new): `data/tosca_detectors_idf2016.csv`

**Interfaces:**
- Produces: `read_detectors(idf_path) -> list[dict]` each `{"bank": "back"|"front", "two_theta_deg": float, "efixed_mev": float}`, in file order; raises `ValueError` unless exactly 70 back and 70 front are found. `write_csv(detectors, path)` with columns `bank,two_theta_deg,efixed_mev`. Uses only the standard library.

- [ ] **Step 1: Write the failing tests**: `test_counts_and_ranges` on `.pixi/envs/mantid/instrument/TOSCA_Definition_2016.xml` asserts 70 back with efixed min 2.690 and max 4.297 (tolerance 1e-3), 2 theta 127.0 to 140.8 deg; 70 front with efixed 2.688 to 4.294 and 2 theta 38.9 to 53.1 deg. `test_incomplete_table_raises`: an XML string with only 69 back detectors raises `ValueError`.
- [ ] **Step 2: Run them.** Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** with `re` over the `<type name="back">` and `<type name="front">` blocks (the `location ... t="..."` attribute is the angle, `Efixed` the parameter).
- [ ] **Step 4: Run the tests; then write** `data/tosca_detectors_idf2016.csv` once (new file).
- [ ] **Step 5: Log.**

### Task 6: INS simulation `analysis/ins.py`

**Files:**
- Create: `analysis/ins.py`
- Test: `analysis/tests/test_ins.py`

**Interfaces:**
- Consumes: `md/output/fc_2x2x1.npz` (Task 3 format), `data/tosca_detectors_idf2016.csv` (Task 5).
- Produces: `simulate_tosca(fc_path, detectors_csv, bank="back", temperature_K=10.0, q_mesh=(2, 2, 2), energy_edges_mev) -> tuple[np.ndarray, np.ndarray]`: energy bin centres (meV) and intensity with the TOSCA resolution applied. Steps (the abinslib/euphonic 2 API was only inspected by signature, not run: read the installed code first): build `euphonic.ForceConstants` from the file (kJ/mol/nm^2 times 0.10364 = meV/A^2), `calculate_qpoint_phonon_modes` on `mp_grid(q_mesh)`, `Displacements.from_modes(modes, temperature=...)`, per detector `calculate_indirect_q2(bins, angle, final_energy)` with that detector's values, `calculate_almost_isotropic_incoherent_spectra` and `mantid_like_combination_spectra`, `apply_weights(..., key='scattering_cross_section')`, average over the bank's detectors, then `resins` `AbINS_v1` broadening. Raises `ValueError` if the table does not have 70 detectors in the chosen bank.

- [ ] **Step 1: Write the failing tests** in `analysis/tests/test_ins.py` (build a 2-atom fixture `.npz` by hand with a known bond force constant, no md env needed):
  - `test_gamma_frequency_of_dimer_matches_analytic`: Euphonic Gamma frequency of the fixture equals hbar sqrt(k/mu) within 0.02 meV.
  - `test_each_detector_uses_its_own_angle_and_efixed`: for a two-detector table, the result equals the mean of the two single-detector runs (within 1e-9 relative).
  - `test_intensity_is_finite_at_zero_energy`: bin edges starting at 0 meV give no NaN or inf (Review Focus 5).
  - `test_wrong_detector_count_raises`.
- [ ] **Step 2: Run them with the ins env.** Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement `simulate_tosca`** as above. If abinslib's `calculate_indirect_q2` only takes scalars, loop over detectors; if the loop of 70 is too slow for the 2x2x1 force constants, report the time and ask before grouping detectors.
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Log** red and green; then run once on `md/output/fc_2x2x1.npz` and log the wall time and the energies of the strongest peaks above 20 meV (not compared with anything yet).

### Task 7: Overlay with the reduced measurement `analysis/compare.py`

**Files:**
- Create: `analysis/compare.py`
- Test: `analysis/tests/test_compare.py`
- Output (new): `data/simulated/ins_back_2x2x1.csv`

**Interfaces:**
- Consumes: `simulate_tosca` (Task 6), `data/reduced/TSC25990_thymol.csv` (columns `energy_meV,bank1,bank2,error1,error2`).
- Produces:
  - `edges_from_centres(centres_mev) -> np.ndarray`: bin edges halfway between neighbouring centres, ends extrapolated by half a step.
  - `bin_integral(energy_mev, y, edges_mev) -> np.ndarray`: the integral of the model over each bin (trapezoid on the model grid, linear interpolation at the edges), divided by bin width.
  - `fit_scale(model, data, error) -> float`: weighted least-squares scale factor, one number, reported not hidden.
  - `write_overlay(path, energy_mev, model, data, error)`: CSV `energy_meV,model,data,error`.

- [ ] **Step 1: Write the failing tests**: `test_bin_integral_of_constant` (constant 3 gives 3 in every bin, including the log-spaced edges `[0.1, 0.2, 0.4]`); `test_bin_integral_of_line` (y = E gives the bin midpoint); `test_fit_scale_recovers_known_factor` (data = 2.5 x model with noise-free errors returns 2.5 within 1e-9); `test_edges_from_centres_log_bins` (centres 1, 2, 4 give edges 0.5, 1.5, 3, 5).
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** the four functions.
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Produce the overlay** for the backward bank (`bank1`; the reduced CSV's bank order is the one in `data/REDUCTION.md`: bank 1 is detectors 1 to 70, which the IDF calls "back" - verify this against `.pixi/envs/mantid/instrument/TOSCA_Definition_2016.xml` before use and log the check). Log the fitted scale and the energies of the main simulated and measured peaks; do not judge the force field in this task.

### Task 8: Thermodynamics from the MD DOS `md/thermo.py`

**Files:**
- Create: `md/thermo.py`
- Test: `md/tests/test_thermo.py`

**Interfaces:**
- Consumes: `dos(velocities, dt_fs)` output (energy in meV, g(E)); `ase.thermochemistry.CrystalThermo(phonon_DOS, phonon_energies, formula_units=None, potentialenergy=0.0)` has `get_internal_energy`, `get_entropy`, `get_helmholtz_energy` but **no heat capacity** (checked in ASE 3.29).
- Produces: `thermo_from_dos(energy_mev, g, n_modes, temperatures_K) -> dict[str, np.ndarray]` with keys `U_meV`, `S_meV_per_K`, `F_meV`, `Cv_meV_per_K`, per cell. `g` is renormalised to integrate to `n_modes` after dropping bins at energy <= 0.5 meV (the translational modes). U, S, F from `CrystalThermo` (eV converted to meV); Cv from the harmonic formula summed over the DOS bins.

- [ ] **Step 1: Write the failing tests**: `test_einstein_zero_point_and_low_t_limit` (all weight at 30 meV, n_modes = 3: U at 10 K within 1e-3 of 3 x 15 meV); `test_einstein_high_t_heat_capacity` (weight at 1 meV, n_modes = 3: Cv at 300 K within 1 percent of 3 k_B = 0.2585 meV/K); `test_zero_modes_are_dropped_not_nan` (a DOS with weight at 0 meV and at 30 meV returns finite values).
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** `thermo_from_dos`.
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Apply** to the 1x1x1 DOS from `md/output/velocities_1x1x1.f32` (per cell: n_modes = 3 x 450 - 3) and log U, S, F, Cv at 10, 50, 100, 300 K, stating that the DOS is classical and that the harmonic quantum formulas applied to it are an approximation (spec "Thermodynamics").

---

## Self-review

- Spec coverage: measured data and binning (Task 7 uses the existing reduction; the 0.5 percent rebin is kept as the working binning), analysis environment (done by the user's install; Tasks 5 to 7 live in it), thermodynamics (Task 8), INS simulation (Tasks 1 to 7), force field switching (Task 1), per-detector E_f and angle (Tasks 5 and 6), `resins` resolution (Task 6). Not covered on purpose: Bayesian band model (own plan), TOSCA references in `refs.bib` (separate bookkeeping step with the `add-reference` skill when the papers are cited), Q weighting beyond what abinslib provides.
- Open decisions inside tasks (stated there, not hidden): the 0.1 nm switching margin, which supercell Hessian runtime is acceptable, grouping of detectors if the per-detector loop is slow, the bank-to-detector mapping check in Task 7.
- Types are consistent between tasks: `save_force_constants` keys (Task 3) are what `simulate_tosca` reads (Task 6); `fc` units kJ/mol/nm^2 throughout, converted once in Task 6.
