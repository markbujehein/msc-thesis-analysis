# msc-thesis-analysis

- **TDD is mandatory here.** Write the test first and run it to see it fail (red) for the right reason, then write the minimal code (green), then refactor. Applies to scripts, hooks and fixes. Docs and data files are exempt. Report the red and green runs.
- Run all tests: `uv run --with numpy python -m unittest discover -s tests/unit/thymol_cif && uv run python -m unittest discover -s tests/unit/hooks`
- Log every scientific change in `LOG.md` (see `.claude/skills/log-entry`); take the time from `date '+%F %H:%M'`, never type it by hand.
- Never run pixi/conda commands (solve, install, add, lock) unless the user asks for that specific action.
- Never delete or overwrite anything you did not create in this session without listing it first and asking.
- Before any git command that rewrites history or resets the working tree (`filter-branch`, `filter-repo`, `reset --hard`, `clean`, `checkout -f`, `stash`): copy every file it could change or delete (tracked or not) to a backup outside the repo, afterwards compare `ls` and `git status` with the backup, and restore at once if anything is missing. Local files are never collateral damage.
- Real data (`data/zeppelin-experimental-data/`, `data/reduced/`, `dft/zeppelin-dft-input/`) is unpublished: git-ignored, never committed. `data/` itself is tracked and holds synthetic stand-in data.
- Energies in meV (eV when large), never wavenumbers.
