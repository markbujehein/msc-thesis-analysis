# msc-thesis-analysis

- **TDD is mandatory here.** Write the test first and run it to see it fail (red) for the right reason, then write the minimal code (green), then refactor. Applies to scripts, hooks and fixes. Docs and data files are exempt. Report the red and green runs.
- Run all tests: `uv run --with numpy python -m unittest discover -s tests/unit/thymol_cif && uv run python -m unittest discover -s tests/unit/hooks`
- Log every scientific change in `LOG.md` (see `.claude/skills/log-entry`); take the time from `date '+%F %H:%M'`, never type it by hand.
- Never run pixi/conda commands (solve, install, add, lock) unless the user asks for that specific action.
- Never delete or overwrite anything you did not create in this session without listing it first and asking.
- Before any git command that rewrites history or resets the working tree (`filter-branch`, `filter-repo`, `reset --hard`, `clean`, `checkout -f`, `stash`): copy every file it could change or delete (tracked or not) to a backup outside the repo, afterwards compare `ls` and `git status` with the backup, and restore at once if anything is missing. Local files are never collateral damage.
- Real data (`data/zeppelin-experimental-data/`, `data/reduced/`, `dft/zeppelin-dft-input/`) is unpublished: git-ignored, never committed. `data/` itself is tracked and holds synthetic stand-in data.
- Energies in meV (eV when large), never wavenumbers.

- Files the user must see go inside the repo (git-ignored `.local/`) and are named as absolute `file:///home/mark/Work/msc-thesis-analysis/...` links. Never `/tmp`: the user cannot open it from the terminal. Every reply that names a repo file the user could open (md, svg, png, html, pdf) uses the absolute `file://` URL, never a relative path; the Stop hook `.claude/hooks/check_md_links.py` blocks the reply otherwise.

- Never paste the user's wording into a deliverable (diagram box, README, spec, commit message, comment) unless they quote it or say to. Their message states an intent; the deliverable needs its own content. Before writing, ask: what does the user actually want to know, which concrete things belong here, and what can be verified? Search or read to find those things. If a name or fact is missing and cannot be found, ask for it; never fill the gap with the user's phrase. Self-check before saving: no run of four or more words from the user's message appears unchanged.

- Public repo: documents state facts and decisions in neutral present tense. No meta-commentary about how a text was produced or revised ("Correction.", "the first version...", "checked against..., three points change"), no "the user stated/says/wants", no changelog prose inside a spec or README. Example to avoid: "Correction. The first version of this section repeated a verbal description without checking it." Corrections go in `LOG.md` as dated entries, in the log's own style.
