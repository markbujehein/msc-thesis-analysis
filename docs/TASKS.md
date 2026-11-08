# Task tracker

Open work only (list it with `grep -n '^- \[ \]' docs/TASKS.md`; the Stop hook `check_tasks.sh` blocks when a file is newer than this one); tick a box when it is done and say how it was checked. Last updated 2026-11-07.

- Spec: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/specs/2026-11-06-md-dos-design.md
- Plan: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-06-ins-from-gaff2.md
- History and results: `LOG.md`

- Plan (INS second order, executed 2026-11-07): file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-07-ins-second-order-streaming.md; supersedes Task 6 below.

## Plan tasks (INS from the GAFF2 Hessian)

Code and tests exist for all eight (tests passed when last run, 2026-11-06; not rerun since). What is left per task:

- [ ] 1 Switching function in `md/build.py`: log the DOS comparison (H peaks unchanged within 1 meV). The 2x2x1 MD files predate the switching function; decide whether to rerun them.
- [ ] 2 `md/hessian.py`: ledger line and `LOG.md` entry.
- [x] 3 `md/supercell.py`
- [x] 4 `md/04_hessian.py` -> `md/output/fc_2x2x1.npz` (0 imaginary modes, 936 C-H and 72 O-H modes as expected)
- [x] 5 `analysis/tosca_detectors.py` -> `data/tosca_detectors_idf2016.csv`
- [x] 6 `analysis/ins.py` on `fc_2x2x1.npz` (2026-11-07): back bank, mean geometry, 45 s, peak 1.14 GB under a 5 GB cap; checked by the run log `.local/run_real.log`, `tests/unit` + `tests/integration/analysis` 81 passed (Mantid-only tests NOT RUN); see LOG.md. Plan: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-07-ins-second-order-streaming.md. The notebook cell ran in the live session (2026-11-07, shape (1000,), finite); the bar is the standard `mo.status.progress_bar`.
- [ ] 7 `analysis/compare.py`: check which reduced-CSV bank is the IDF "back" bank, then write `data/simulated/ins_back_2x2x1.csv` and log the fitted scale and peak positions.
- [x] 8 `md/thermo.py`: U, S, F, Cv at 10, 50, 100, 300 K logged (2026-11-07 22:45); the ASE overflow warnings at low T are suppressed (exact limit 1/inf = 0), checked by `test_no_overflow_warning_for_high_energy_bins_at_low_temperature`.

## CRITICAL (user, 2026-11-07)

- [ ] GitHub still serves the old commit and the reduced CSV by commit id (HTTP 200 at 16:0x) although `origin/main` is rewritten: make the repository private, or delete and recreate it, or ask GitHub support to purge cached objects. Needs the user (my attempt was denied).
- [ ] Decide whether values derived from the unpublished data (sample mass, temperatures, scale factors, bin widths in `LOG.md` and the spec) must also leave the history.
- [x] `data/reduced/*.csv`, `data/REDUCTION.md`, `data/tosca_detectors.csv` restored byte-exact (2026-11-07, from the old GitHub commits) after my history rewrite deleted them; checked by line counts and `cmp`.

## Wrap-up

- [ ] Whole-branch review (self-review: no subagent for it in the plan run).
- [x] Systematic commits (2026-11-07): 10 commits `956b5a6`..`494fb16` on master, explicit paths only. Left uncommitted on purpose: `data/zeppelin-experimental-data/` (30 MB raw TOSCA files; user decides), `analysis/.gitignore` and `analysis/.gitattributes` (leftovers of the removed analysis project; the lock-file attribute is not set for the root `pixi.lock`). `md/output/` and `md/__marimo__/session/` are now git-ignored.

## Open decisions (user)

- [ ] 0.1 nm switching-distance margin (my choice, unconfirmed).
- [ ] NaN workaround in `ins.py` (zero-frequency modes lifted to abinslib's 10 cm^-1 threshold); float equality at the threshold unverified.
- [ ] 2x2x1 MD rerun with the switching function: cost not measured.

## Environments

- [ ] Marimo's optional dependencies (altair, nbformat, openai, duckdb, sqlglot) were removed by mistake and restored on 2026-11-07 (checked by comparing all names and pins of the old and new manifests; see `LOG.md` correction). Never remove packages the user installed.
- [x] Root `pixi.lock` solved by the user on 2026-11-07 (`pixi install`/`update`/`upgrade`, 15:06); my parse of it: sqlglot conda 30.29.0 in two environments, no `sqlglotc`. Package guard `check_deps.py` finds nothing missing.
- [x] Marimo extras `mcp` and `recommended` added (no `lsp`: `ty` is global); explicit optional packages kept. Root `pixi.lock` is older than this change: re-lock needs approval.
- [ ] Narrow `check_tasks.sh`: it also fires on `md/__marimo__/` and `pixi.lock`; proposed to count only `md/ analysis/ thymol_cif/ pdb/ data/ pixi.toml`; awaiting the user's answer.
- [x] One root `pixi.toml` with features and environments (md, ins, mantid) is written but not solved or installed (unverified: it may not solve, Mantid 7 pins in the shared default feature are the risk). Needs the user's go-ahead to run pixi, and to remove `md/pixi.toml`, `analysis/pixi.toml`, their locks and the two old `.pixi` folders (5.2 GB and 3.9 GB). Until then `pixi` in `md/` or `analysis/` still uses the old manifests. Still naming the old per-folder environments: the plan (`docs/superpowers/plans/2026-11-06-ins-from-gaff2.md`), the spec section on the analysis environment, `docs/tutorials/*.html`, and the CLAUDE.md test command. Checked 2026-11-07: user ran pixi install, update, upgrade; `pixi.lock` is committed.

## Later

- [x] AFGA validation wording matches the paper (checked: re-read the 2021 text, 2026-11-07).


- [ ] AFGA (papers read, refs.bib done 2026-11-07): check NCrystal in the environments; run `hfg2ncmat` for thymol (spec `3xCHaro+1xCHali+3xCH3+1xOH`, density from the crystal structure) and compare with the simulated hydrogen DOS.
- [ ] Krzystyniak 2023 read (2026-11-07). Open: verify the recomputed E_kin and omega ratio against the journal page; read arXiv 2506.01860 and 2603.05442 in full; GAFF2 vs MACE Hessian comparison.
- [ ] ML-method survey recorded (2026-11-07). OMC25, OMol25, UMA read (see log). Open: read arXiv 2506.01860, the Armstrong paper and the npj Comput. Mater. phonon paper; decide whether to add Petrov 2026 and DM21.
- [ ] Investigate UMA (papers read 2026-11-07): read the weights licence on Hugging Face; check fairchem install in its own environment (UMA needs it, not tested); compare GAFF2 and UMA Hessians on the same cell (imaginary modes first), then the spectrum. Settled from the papers: C, H, O covered, crystal task is PBE-D3, OMol task is wB97M-V (VV10).
- [ ] Check the number of molecules in the asymmetric unit (Z-prime) of the thymol structure from the CIF; OMC25 covers Z-prime of at most 1.
- [x] Diagram: UMA added and box renamed "Potentials to try" (2026-11-07). Checked: regenerated `docs/figures/pipeline.svg`, grep finds the title and UMA in the SVG, README `?v=` hash updated, first render (three-line box) viewed; the renamed-title render is saved but not viewed.
- [x] Names aligned: README row and spec section 3 heading now "Potentials to try" (checked by grep, 2026-11-07).
- [ ] Confirm the eSEN baseline names and licence (fallback to UMA); not yet in the README or diagram.


- [ ] Public repo: remove mentions of the user and revision narrative from older documents (TASKS, plan, older spec, LOG); decide how to treat LOG.md history.


- [ ] VESUVIO: get the reference or scripts for the instrument scientists' validation (bootstrap, jackknife, Monte Carlo); decide whether the Bayesian fit stage can replace Mantid's, using the test plan in the spec.


- [ ] After any change to a README figure, update its `?v=` value (`git hash-object <file> | cut -c1-7`).


- [x] README has no Working rules section (checked: grep count 0, 2026-11-07).


- [x] Shortened force-field box fits (checked: Chromium render viewed, 2026-11-07).


- [x] Force-field box lists researched candidates (checked: web search, Chromium render, 2026-11-07).
- [ ] Force fields: read the AMOEBA and ML-potential papers, add to `refs.bib`; check C, H, O coverage and that thymol can be parametrized for AMOEBA; pick the MACE model.
- [x] Pipeline: force-field box text and FTIR box position (checked: Chromium render, 2026-11-07).


- [x] Hook tests green again after the root fallback fix (checked: 38 tests OK, 2026-11-07).


- [x] Link hook registered and widened to figures (checked: 17 tests in test_check_md_links pass, 2026-11-07).


- [x] Pipeline restored to the f30adc1 version (checked: git diff against f30adc1 is empty for pipeline.svg and make_pipeline.py; README differs only in the banner alt text, 2026-11-07).


- [x] Pipeline: Improved potentials box feeds MD and Hessian (checked: Chromium render, 2026-11-07; label overflow found and shortened).


- [x] Banner title and subtitle in plain academic terms (checked: Chromium render, 4 banner tests, 2026-11-07).


- [x] Pipeline: planned force-field box above GAFF2 MD (checked: Chromium render, 2026-11-07).


- [x] Banner curve spectrum-like and seeded (checked: unit tests and Chromium render, 2026-11-07).


- [x] Banner and README intro carry no unverified thesis context (checked: grep for MSc in banner.svg, README intro).


- [ ] QENS: look at the reduced TOSCA spectra for any quasi-elastic signal before planning anything; ask the supervisor for their earlier analyses.

- [ ] Remove the symlink `/home/mark/Work/msc-thesis/.claude` after restarting Claude in `msc-thesis-analysis` (user).
- [ ] Check the VESUVIO hydrogen kinetic-energy link and the MACE model choice against the literature before writing plans.
- [ ] VESUVIO: check the sub-25 meV region against sources (which detectors and analysis give it, how precise); the ISIS page read so far covers only 1 to 100 eV for NCS.

- [ ] Replace `data/tosca_detectors_idf2016.csv` (temporary, from the 2016 Mantid definition) when an updated TOSCA definition is available; then rerun the INS comparison.

- [ ] README figures: pipeline.svg is hand-placed; update `docs/figures/make_pipeline.py` whenever a step changes status. Figures regenerated 2026-11-07 (banner generic, pipeline with MACE, VESUVIO chain, QENS check): rendered in Chromium and read.

- [ ] Refine the rough spec `docs/superpowers/specs/2026-11-07-extended-data-design.md` (open questions at its end: VESUVIO data location and format, synthetic-data realism, IR/Raman calibration, earlier QENS analyses), then write plans per work stream.
- [ ] Synthetic stand-in data in `data/` (generator script + test), so a fresh clone runs without the unpublished data.

- [x] README uses status labels DONE / WIP / PLANNED (2026-11-07); keep them in step with this tracker.

- [ ] Re-lock after the sqlglot-from-PyPI and unpinned-python edits (2026-11-07); check the `sqlglot[c]` warning is gone and which Python md/ins get.

- [x] `README.md` written 2026-11-07 (checked against `pixi.toml` and `LOG.md`; not yet checked: that `pixi run test-unit-all` works).

- [x] `sqlglot[c]` warning: conda `sqlglotc` added to `notebook` (2026-11-07). The warning itself will probably stay; needs a re-lock to see. Checked: manifest parses, guard finds nothing missing.
- [ ] Compare the new lock with the old locks (`pixi upgrade` pins are logged in `LOG.md`, 2026-11-07); the lock is older than the later manifest edits: re-lock needs approval.

- [ ] Run `pixi run -e fix fix` (34 of 40 ruff findings auto-fixable; 22 files would be reformatted): needs approval, it rewrites files.
- [ ] Doctests are configured (`pytest.ini`) but no docstring has an example yet.

- [x] Package-loss guard `check_deps.py` + `.claude/deps.baseline` (8 tests; it caught my own corruption of `pixi.toml` on 2026-11-07).

- [x] Global `tests/unit/` and `tests/integration/` (user request, 2026-11-07; no new tests for now). Done 2026-11-07: tests moved, pixi tasks `test-unit`/`test-integration`; checked by test counts before/after (see `LOG.md`). Integration tests not executed.

- [ ] Bayesian band model (own plan, after the overlay exists). Scope: resolved C-H and O-H groups first.
- [ ] Add Dymkowski 2018 (10.1016/j.physb.2018.02.034) and Cheng 2019 (10.1021/acs.jctc.8b01250) to `refs.bib` (skill `add-reference`).
- [ ] DOS-like conversion of the Mantid spectrum, background and calibration runs, unexplained 30 percent bank intensity ratio (`data/REDUCTION.md`).
- [ ] Supercell Hessian accuracy: PME long-range interactions are folded into a 2x2x1 supercell; no convergence check yet.

- [x] Environment `test-ins` is built (2026-11-07 22:44); `test-mantid` is not: `tests/integration/analysis/test_tosca_detectors.py` and `test_reduce_tosca.py` need it and have not been run. Done 2026-11-08: all environments installed; `pixi run -e test-mantid pytest tests/integration/analysis/test_tosca_detectors.py tests/integration/analysis/test_reduce_tosca.py` gave 7 passed.
- [ ] `analysis/05_ins.py` and `analysis/__marimo__/` are untracked; decide whether to keep the notebook and ignore `__marimo__/`.

- [ ] Plan 2026-11-07-ins-second-order-streaming: final whole-branch review. Tasks 1 to 6 done (Task 5: 7-detector subsample, area ratio 1.0007, same peaks, max difference 0.29 percent; LOG.md) (ledger `.superpowers/sdd/`).



- [x] Visualisation in all five notebooks (altair, titled; LOG.md). Run check still open: `md/03_dos.py` and `md/04_hessian.py` compiled only; render all charts once in marimo.
- [ ] Task 7: verify that reduced-CSV bank 1 is the IDF back bank before reading the overlay quantitatively (`analysis/05_ins.py` currently labels it unverified).
- [ ] `pixi.toml` `test-integration-ins` omits `test_second_order.py` (manifest edit needs approval).

- [x] `md/dos.py`: `dos()` transforms the columns in blocks (`block=300`) because the 2x2x1 DOS was OOM-killed at a 6 GB cap (kernel OOM log, 2026-11-08). Checked: `tests/unit/md` 11 passed, including block equivalence and a tracemalloc bound; red run first (`unexpected keyword argument 'block'`).
- [x] `md/03_dos.py`: not yet re-run after the `dos()` change; run it once in marimo under the memory cap and check peak memory and the charts. Same for `md/04_hessian.py` (recomputes the Hessian) and `md/02_run.py` (its first cell re-runs the MD). Done: ran in marimo 2026-11-08 under the 8 GB cap; peak 3.5 to 4.5 GB, no cell errors (systemd memory status).
- [ ] Notebook servers: run one at a time (one at a time). `marimo-md` serves `md/01_system.py` on port 2718; `marimo-ins` (05_ins.py) is stopped. The server on port 2719 is a leftover from `~/Work/msc-thesis/md` (not started in this session): decide whether to stop it.
- [ ] `md/01_system.py` charts verified by `marimo export html` (9 vega outputs) and by a live run; the other four notebooks' charts are not yet viewed in a browser.

- [x] `md/01_system.py`: molecular sphere view (ASE `plot_atoms`, CPK colours, rotation sliders). Checked: cells ran without errors in the live session; static render of the 1800-atom supercell looked at (`.local/01_spheres.png`). Sliders not yet tried in a browser.
- [x] Decide on a true 3D molecule widget (nglview or weas-widget): needs a `pixi.toml` change and install, which needs approval. Until then the view is a 2D projection with overlapping atoms. Done: MolViewSpec widget in the md environment (no new install); checked in a browser screenshot 2026-11-08.

- [x] `md/01_system.py` IPyMolStar (Mol*) cell replaces the nglview cell (nglview rendered nothing in marimo, browser check; removed): confirm in the browser that the 3D view renders in marimo (ipywidgets support is the risk). If it does not, fall back to py3Dmol (HTML) or an anywidget wrapper; then update `docs/TASKS.md` and `LOG.md`. Superseded by the MolViewSpec cell; checked in a browser screenshot.
- [x] nglview added to `pixi.toml` (`feature.md`) and installed in `md` (`pixi install -e md`; `import nglview` gave 4.0.1). Side effect: ipywidgets/ipython moved from PyPI to conda in the lock.
- [x] nglview removed and ipymolstar (PyPI) added to `feature.md` in `pixi.toml`, `pixi install -e md`; checked: `import ipymolstar` ok, nglview not importable, notebook 01 cells idle without errors.
- [x] `md/01_system.py` "Atoms per element" table: confirm in the browser that it renders after the dtype change (it showed "Something went wrong"); if not, read the browser console error. Same pattern in the 04 band table (compiled only). Done: browser screenshot shows C 720, H 1,008, O 72.
- [x] `md/01_system.py`: 2D `plot_atoms` cell, rotation sliders and unused imports removed; checked: all cells idle without errors in the live session, grep finds no `plot_atoms`/`jmol`/`rotation_` in the file.
- [x] `md/molview.py` mmCIF writer for the Mol* cell (test first: 2 passed in `tests/unit/md/test_molview.py`).
- [x] `md/01_system.py` Mol* cell with mmCIF and `theme="dark"`: confirm in the browser that it draws and the text is readable; if the page is switched to light mode the dark theme may need to follow it. Superseded by MolViewSpec (grey canvas, ball-and-stick); browser screenshot checked.
- [x] `md/01_system.py` Mol* view: carbon and hydrogen look alike (light grey, white); try `ball-and-stick` or a carbon colour, then inspect again. Verified in a browser: render, grey background with visible icons, unit-cell outline, "Atoms per element" table. Done: dark carbon, white hydrogen, red oxygen visible in the browser screenshot.
- [x] `md/01_system.py` Mol* view: `visual_style` has no visible effect. Checked in a browser 2026-11-08: setting the trait live (ball-and-stick) changed nothing, and a widget created with `visual_style="point"` and preset `unitcell` rendered as spacefill. The JS has a `change:visual_style` handler (`visual.update`), cause unknown. The cell now has `ball-and-stick` and `default_preset="default"` (unit-cell outline lost); render not yet seen. No buttons or dropdowns (one at a time): a dropdown cell was tried and removed. Superseded: the MolViewSpec widget replaces PDBeMolstar.
- [ ] Close the Chrome DevTools browser still connected to the notebook as a reader; only `marimo-md` (01_system.py, port 2718) runs.
- [ ] Charge-histogram legend in `md/01_system.py` was clipped; width reduced to 480, not re-inspected.
- [x] `md/01_system.py` 3D view on `MolViewSpec` (ball-and-stick per element, grey canvas, no cell outline, no dropdown); confirmed in a browser. Supersedes the open Mol* `visual_style`, carbon/hydrogen and contrast items above. Panels-off `viewer_options` applied last; my own screenshot of that final state not taken.
- [x] `md/01_system.py` 3D view with unit-cell (orange) and supercell (cyan) outlines (`tube` primitives); checked in a browser, no MVS validation error, 19 md unit tests pass.
- [ ] Decide whether to draw the rhombohedral primitive cell (6 molecules) and whether to wrap molecules into the cell; the PDB molecules are not wrapped (x -13.9 to 28.6 angstrom).
- [x] `md/01_system.py`: comment "loaded: atom positions of the relaxed-geometry PDB, by element" removed; checked: the cell ran without errors in the live session and a search of the file finds no copy.
- [x] Next: serve `md/03_dos.py` alone (stop `marimo-md` first, one notebook at a time) and check its charts after the block-wise `dos()` change; then 02, 04, 05. Done: 03 was served and viewed in a browser (tables, stretch-band labels); the 03 chart labels after the last edit were not re-inspected.
- [x] `md/02_run.py` served alone and viewed in a browser (cells that read the existing log only; the MD cells were not run): titled temperature and total-energy charts and the statistics table render, no cell errors, 1 GB. Chart width reduced from 600 to 520 (right edge of the time axis was clipped); not re-inspected. Not yet committed.
- [ ] Next notebooks to serve one at a time: `md/04_hessian.py` (recomputes the Hessian: run only selected cells) and `analysis/05_ins.py`.
- [x] `md/02_run.py` charts: target and equilibration marks, production energy deviation, temperature histogram; checked in the browser (no chart error). Open: temperature chart not re-seen after the selection fix; statistics table shows too many digits. Not committed.

- [x] Branch `notebook-visualisation` committed in nine commits and merged into `main` (merge commit 9c4aa4d); checked with `git log` and an empty `git status`. Not pushed.
- [ ] Push `main` to origin (not done; needs approval).
- [ ] `md/02_run.py`: round the statistics table digits; re-inspect the temperature chart after the selection fix.
