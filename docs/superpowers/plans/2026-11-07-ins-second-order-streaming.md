# INS second order without the dense tensor: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `analysis/ins.simulate_tosca` returns the first- plus second-order TOSCA spectrum of one bank from `md/output/fc_2x2x1.npz` on this machine, with a bounded and measured peak memory and a progress bar.

**Architecture:** abinslib's two-phonon routine allocates dense `(mode1, mode2, atom)` arrays (1350 x 1350 x 450 x 8 B = 6.56 GB each, several at once). The same quantity is a matrix product per atom, so a new module `analysis/second_order.py` evaluates it atom by atom and bins it immediately (memory: one 1350 x 1350 block). First order and the Debye-Waller tensor stay with abinslib (measured: 1.74 GB through first order). The bank is simulated once with its mean geometry.

**Tech Stack:** numpy, euphonic 2.1.1, abinslib 0.3.x, resins, pytest, marimo (environment `ins`; tests in `test-ins`).

**Spec:** file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/specs/2026-11-06-md-dos-design.md (section "INS simulation"; Task 1 of this plan amends it). Superseded plan: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-06-ins-from-gaff2.md (its Task 6 is replaced by Tasks 2 to 4 here).

## Global Constraints

- Energies in meV (eV when large), never wavenumbers (CLAUDE.md).
- TDD: the failing test is written and run (red, for the right reason) before the code; report red and green runs (CLAUDE.md).
- No pixi/conda solve, install, add or lock without a request for that action; `pixi run -e <env>` of existing environments is allowed (CLAUDE.md).
- Log every scientific change in `LOG.md` with the time from `date '+%F %H:%M'` (CLAUDE.md).
- Real data (`data/reduced/`, `data/zeppelin-experimental-data/`) is never committed. The notebook is served by the systemd user unit `marimo-ins` (8 GB, no swap); heavy cells start only on a button.
- Progress follows `md/run.py`: argument `bar=NoBar`, a factory `(total, title)` returning a context manager with `update(increment, title=None, subtitle=None)`.
- Repo documents use neutral present tense with no narrative about how a text was produced (CLAUDE.md).
- Commits only when the user asks; explicit paths.

## Review Focus

1. A Gamma-only mesh contains translational modes at 0 meV: the second-order block must stay finite and equal abinslib's (abinslib zeroes their displacements below 10 cm^-1).
2. q-point weights that differ between points (symmetry-reduced mesh): the weighted sum over q-points must equal abinslib's all-at-once result.
3. Pair frequencies above the last bin edge: they are dropped, as `np.histogram` does in abinslib, with no error and no wraparound.
4. A bank name that is not in the table, or a table with fewer detectors than expected, raises `ValueError` before any heavy work.
5. A larger fixture than the dimer: peak memory stays far below the dense tensor (a regression test that would fail if the dense array came back).

## File structure

- Create `analysis/second_order.py`: one public function, `combination_spectra`.
- Modify `analysis/ins.py`: remove the per-q-point displacement loop and the first-order `share` factor; call `combination_spectra`.
- Modify `analysis/05_ins.py`: the run cell (button kept, `mo.status.progress_bar` lambda).
- Create `tests/integration/analysis/test_second_order.py`; modify `tests/integration/analysis/test_ins.py`.
- Modify the spec, `LOG.md`, `docs/TASKS.md`, `.gitignore`.

### Task 1: Amend the spec

**Files:**
- Modify: `docs/superpowers/specs/2026-11-06-md-dos-design.md` (section "INS simulation", the "Decision (user, 22:40)" paragraph and pipeline step 3)

**Interfaces:**
- Produces: the statements Tasks 2 to 5 implement: bank simulated once with mean geometry; second order computed per atom.

- [ ] **Step 1: Edit the section.** State, in present tense: (a) the reduction sums the detectors of a bank, so the simulation uses one geometry per bank, the mean 2 theta and mean Efixed from the detector table (`data/tosca_detectors_idf2016.csv`), replacing the per-detector decision; the difference between the mean-geometry spectrum and the detector-averaged spectrum is measured in Task 5; (b) the Euphonic model has 450 atoms and 1350 modes per q-point; abinslib's second order needs several 6.56 GB arrays; the second order is evaluated per atom (`I_m(v1, v2) = (tr B_m(v1) tr B_m(v2) + 2 B_m(v1):B_m(v2)) / (15 c)`, c = 2 for v1 = v2, else 1, placed at w1 + w2, then Q^4 and Debye-Waller scaling as in abinslib).
- [ ] **Step 2: Verify.** Run `grep -n "22:40\|per detector" docs/superpowers/specs/2026-11-06-md-dos-design.md`; expected: no remaining statement that asks for per-detector Q^2.

### Task 2: Streaming two-phonon spectrum `analysis/second_order.py`

**Files:**
- Create: `analysis/second_order.py`
- Test: `tests/integration/analysis/test_second_order.py`

**Interfaces:**
- Consumes: `euphonic.QpointPhononModes` (one q-point), `abinslib.displacements.Displacements`, `abinslib.isotropic_incoherent.calculate_isotropic_dw_factor`, `abinslib.util.iter_atom_info`, `euphonic.spectra.Spectrum1DCollection`.
- Produces: `combination_spectra(modes, displacements, atomic_displacements, nominal_q2, bins) -> Spectrum1DCollection`. Same arguments and meaning as `abinslib.almost_isotropic_incoherent.mantid_like_combination_spectra`, for any number of q-points; the result is the sum over q-points of w_q x (spectrum of q alone), as that function defines it (`weights` of `modes` used as given).

- [ ] **Step 1: Write the failing tests** in `test_second_order.py`, with a fixture of a few atoms built by hand (random symmetric positive-definite force constants, 3 atoms, two cell origins so q-mesh (2,2,1) has several q-points and unequal weights):
  - `test_matches_abinslib_on_small_fixture`: `combination_spectra(...)` equals `mantid_like_combination_spectra(...)` (`y_data` with `rtol=1e-10`, `atol=1e-12 * max`) for a mesh with unequal weights.
  - `test_gamma_only_with_translational_modes_is_finite_and_matches` (Review Focus 1).
  - `test_pairs_above_last_bin_are_dropped` (Review Focus 3): bins end below 2 x the highest mode; result still equals abinslib.
  - `test_peak_memory_is_far_below_the_dense_tensor` (Review Focus 5): fixture of 40 atoms (120 modes, one q-point); `tracemalloc` peak of `combination_spectra` is below one quarter of `120 * 120 * 40 * 8` bytes times 3 (the three dense arrays abinslib forms). The test first runs against a stand-in that builds the dense tensor to show it would fail (assert the stand-in exceeds the bound).
- [ ] **Step 2: Run them** (`pixi run -e test-ins pytest tests/integration/analysis/test_second_order.py -q`). Expected: FAIL with `ModuleNotFoundError: second_order`.
- [ ] **Step 3: Implement `combination_spectra`** in `analysis/second_order.py`. Algorithm (not determined by the signature): for each q-point, `b = displacements.n_plus_one` in bohr^2 for that point, shape (modes, atoms, 3, 3); the pair frequencies `w1 + w2` and their bin index (`np.digitize` against `bins`, pairs outside dropped) are computed once per q-point; for each atom, `trace = einsum("...ii", b[:, m])`, `contraction = B @ B.T` with `B = b[:, m].reshape(modes, 9)`, `I = (outer(trace, trace) + 2 * contraction) / (15 * c)`, accumulated with `np.bincount(index, weights=I.ravel(), minlength=len(bins) - 1)`. The q-point weight factor is whichever one reproduces abinslib (its per-q spectrum is multiplied by w_q); the equivalence test decides it. Then divide by the bin width, build `Spectrum1DCollection(x_data=bins, y_data=..., metadata={"method": "almost-isotropic incoherent approximation", "line_data": [info | {"quantum_order": 2} for info in iter_atom_info(modes.crystal)]})`, and scale by `(nominal_q2 / 1 A^-2) ** 2` and the transposed `calculate_isotropic_dw_factor(atomic_displacements, nominal_q2)[0]` exactly as abinslib does after binning.
- [ ] **Step 4: Run the tests.** Expected: all PASS. If the equivalence differs by a constant factor, fix the weight rule, not the tolerance.

### Task 3: Use it in `ins.py`

**Files:**
- Modify: `analysis/ins.py` (`simulate_tosca`, helper `_qpoint`, `_simulate`)
- Test: `tests/integration/analysis/test_ins.py`

**Interfaces:**
- Consumes: `combination_spectra` (Task 2); `NoBar` from `md/progress.py`.
- Produces: unchanged signature `simulate_tosca(fc_path, detectors_csv, energy_edges_mev, bank="back", temperature_K=10.0, q_mesh=(2, 2, 1), expected_detectors=70, bar=NoBar) -> (energy_meV, intensity)`; the bar has `4 + n_q` steps (modes, displacements and Debye-Waller, first order, one per q-point for second order, broadening).

- [ ] **Step 1: Update the tests first.** `test_bar_has_one_step_per_stage` expects `4 + n_q`; `test_one_qpoint_at_a_time_equals_all_qpoints_at_once` is renamed `test_equals_abinslib_all_at_once` and keeps its abinslib reference (dense, dimer). Add `test_unknown_bank_raises` (Review Focus 4). Run: bar test and the new test FAIL (step count; no such error yet), the equivalence test still PASSES.
- [ ] **Step 2: Implement.** Compute `Displacements.from_modes(modes)` once for all q-points (0.8 GB for 4 q-points, computed), `atomic = displacements.to_atomic_displacements()`, first order from abinslib on all modes at once (this removes `_qpoint` for first order and the `share` factor), second order as the sum over q-points of `combination_spectra` on single-q chunks built with `_qpoint` (kept for this use only). Merge `_simulate` back into `simulate_tosca` (the split exists only for the `with`). Keep the mean-geometry code.
- [ ] **Step 3: Run** `pixi run -e test-ins pytest tests/integration/analysis tests/unit -q`. Expected: all PASS.

### Task 4: Notebook run and measurement

**Files:**
- Modify: `analysis/05_ins.py`

**Interfaces:**
- Consumes: `simulate_tosca` (Task 3).

- [ ] **Step 1: Verify the notebook cell** uses `bar=lambda total, title: mo.status.progress_bar(total=total, title=title)` and starts on the button (no code change expected after the earlier edit; confirm with `grep -n progress_bar analysis/05_ins.py`).
- [ ] **Step 2: Run it** from the browser tab of `marimo-ins` (http://localhost:2718). Expected: finishes inside the 8 GB cap; record wall time and the peak memory from `systemctl --user status marimo-ins` (shows `Memory: ... (peak: ...)`). If the unit is killed, stop and report the last progress text; do not raise the cap.
- [ ] **Step 3: Log** wall time, peak memory and the energies of the strongest peaks above 20 meV in `LOG.md` (`date '+%F %H:%M'`), and tick Task 6 in `docs/TASKS.md` with how it was checked.

### Task 5: Mean geometry versus detector average

**Files:**
- Modify: `LOG.md` only (a measurement, no repo code)

**Interfaces:**
- Consumes: `simulate_tosca`, `data/tosca_detectors_idf2016.csv`.

- [ ] **Step 1: Measure** on the dimer fixture and on the real force constants with the number of q-points reduced to the smallest mesh that runs quickly: the relative difference of the area and of the peak positions between the mean-geometry spectrum and the average of the spectra of every 10th back-bank detector (7 detectors, a stated subsample).
- [ ] **Step 2: Log** the two numbers and the sample; no assertion, no code change. The decision on whether the mean is adequate stays open until the numbers are read.

### Task 6: Housekeeping

**Files:**
- Modify: `.gitignore`, `docs/TASKS.md`

- [ ] **Step 1:** Add `analysis/__marimo__/` to `.gitignore`; run `git status --short`; expected: `analysis/__marimo__/` no longer listed.
- [ ] **Step 2:** In `docs/TASKS.md` tick or update the items for Tasks 6 and 8 of the superseded plan with how each was checked; add the open item for Task 7 (overlay) as the next step.
- [ ] **Step 3:** Ask the user whether to commit; if yes, commit explicit paths in logical groups (`md/thermo.py` + its test; `analysis/` + tests; docs).

## Self-review

- Spec coverage: bank collapse (Tasks 1, 3, 5), memory bound (Tasks 2, 4), progress convention (Task 3), logging (Tasks 4, 5).
- Not decided by this plan: whether the mean geometry is an adequate stand-in for the detector sum (Task 5 measures it); the energy range and bin width of the production run (the notebook uses 0 to 500 meV in 0.5 meV bins, unchanged).
- Types: `combination_spectra` mirrors `mantid_like_combination_spectra`; `simulate_tosca` signature unchanged from the working tree.
