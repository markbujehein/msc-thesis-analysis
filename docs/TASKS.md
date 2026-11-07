# Task tracker

Open work only (list it with `grep -n '^- \[ \]' docs/TASKS.md`; the Stop hook `check_tasks.sh` blocks when a file is newer than this one); tick a box when it is done and say how it was checked. Last updated 2026-11-07.

- Spec: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/specs/2026-11-06-md-dos-design.md
- Plan: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-06-ins-from-gaff2.md
- History and results: `LOG.md`

## Plan tasks (INS from the GAFF2 Hessian)

Code and tests exist for all eight (tests passed when last run, 2026-11-06; not rerun since). What is left per task:

- [ ] 1 Switching function in `md/build.py`: log the DOS comparison (H peaks unchanged within 1 meV). The 2x2x1 MD files predate the switching function; decide whether to rerun them.
- [ ] 2 `md/hessian.py`: ledger line and `LOG.md` entry.
- [x] 3 `md/supercell.py`
- [x] 4 `md/04_hessian.py` -> `md/output/fc_2x2x1.npz` (0 imaginary modes, 936 C-H and 72 O-H modes as expected)
- [x] 5 `analysis/tosca_detectors.py` -> `data/tosca_detectors_idf2016.csv`
- [ ] 6 `analysis/ins.py`: run on `fc_2x2x1.npz`. One detector first (time and memory were not recorded; the second-order spectra may be too heavy for 5400 modes), then the bank. Ask before grouping detectors.
- [ ] 7 `analysis/compare.py`: check which reduced-CSV bank is the IDF "back" bank, then write `data/simulated/ins_back_2x2x1.csv` and log the fitted scale and peak positions.
- [ ] 8 `md/thermo.py`: `LOG.md` entry with U, S, F, Cv at 10, 50, 100, 300 K (computed, not yet logged). Check the ASE overflow warnings at low T.

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
- [x] Marimo extras `mcp` and `recommended` added (no `lsp`: `ty` is global); explicit optional packages kept. Root `pixi.lock` is older than this change: re-lock needs the user's go-ahead.
- [ ] Narrow `check_tasks.sh`: it also fires on `md/__marimo__/` and `pixi.lock`; proposed to count only `md/ analysis/ thymol_cif/ pdb/ data/ pixi.toml`; awaiting the user's answer.
- [x] One root `pixi.toml` with features and environments (md, ins, mantid) is written but not solved or installed (unverified: it may not solve, Mantid 7 pins in the shared default feature are the risk). Needs the user's go-ahead to run pixi, and to remove `md/pixi.toml`, `analysis/pixi.toml`, their locks and the two old `.pixi` folders (5.2 GB and 3.9 GB). Until then `pixi` in `md/` or `analysis/` still uses the old manifests. Still naming the old per-folder environments: the plan (`docs/superpowers/plans/2026-11-06-ins-from-gaff2.md`), the spec section on the analysis environment, `docs/tutorials/*.html`, and the CLAUDE.md test command. Checked 2026-11-07: user ran pixi install, update, upgrade; `pixi.lock` is committed.

## Later

- [x] AFGA validation wording matches the paper (checked: re-read the 2021 text, 2026-11-07).


- [ ] AFGA (papers read, refs.bib done 2026-11-07): check NCrystal in the environments; run `hfg2ncmat` for thymol (spec `3xCHaro+1xCHali+3xCH3+1xOH`, density from the crystal structure) and compare with the simulated hydrogen DOS.
- [ ] Krzystyniak 2023 read (2026-11-07). Open: verify the recomputed E_kin and omega ratio against the journal page; read arXiv 2506.01860 and 2603.05442 in full; GAFF2 vs MACE Hessian comparison.


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
- [ ] Compare the new lock with the old locks (`pixi upgrade` pins are logged in `LOG.md`, 2026-11-07); the lock is older than the later manifest edits: re-lock needs the user's go-ahead.

- [ ] Run `pixi run -e fix fix` (34 of 40 ruff findings auto-fixable; 22 files would be reformatted): needs the user's go-ahead, it rewrites files.
- [ ] Doctests are configured (`pytest.ini`) but no docstring has an example yet.

- [x] Package-loss guard `check_deps.py` + `.claude/deps.baseline` (8 tests; it caught my own corruption of `pixi.toml` on 2026-11-07).

- [x] Global `tests/unit/` and `tests/integration/` (user request, 2026-11-07; no new tests for now). Done 2026-11-07: tests moved, pixi tasks `test-unit`/`test-integration`; checked by test counts before/after (see `LOG.md`). Integration tests not executed.

- [ ] Bayesian band model (own plan, after the overlay exists). Scope: resolved C-H and O-H groups first.
- [ ] Add Dymkowski 2018 (10.1016/j.physb.2018.02.034) and Cheng 2019 (10.1021/acs.jctc.8b01250) to `refs.bib` (skill `add-reference`).
- [ ] DOS-like conversion of the Mantid spectrum, background and calibration runs, unexplained 30 percent bank intensity ratio (`data/REDUCTION.md`).
- [ ] Supercell Hessian accuracy: PME long-range interactions are folded into a 2x2x1 supercell; no convergence check yet.
