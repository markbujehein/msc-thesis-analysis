# Thymol solid-state structures: working log

Shared log (user + Claude). Append new entries at the bottom, never rewrite old ones. Format: see `.claude/skills/log-entry/SKILL.md`. References: `refs.bib` (BibLaTeX).

Goal: find a suitable unit cell of solid thymol (C10H14O, 25 atoms/molecule), lowest temperature possible, to build a PDB for MD.

## 2026-11-06 12:15-12:35 - Initial research and first PDB (Claude)
- Searched COD (`result?formula=C10+H14+O`): 27 hits. Downloaded all and checked headers. **None of the experimental ones are thymol**: 1576118 (SPOCQ paper), 2101879/80 (carvone), 2212550 (cyclobutane), 4038650 (JOC), 4502150 (butylphenol), 4510488/89 (2-adamantanone). Deleted. COD text search "thymol" gave 2206853 (2-formyl thymol oxime, C11H15NO2) and 7240211 (acridine thymol cocrystal): not pure thymol, deleted.
- COD 4101953-4101971 (19 files) are thymol, but **computed (crystal structure prediction), no temperature**. Verified by bond geometry: OH at ring position 1, iPr at 2, Me at 5, 25 atoms each (script not kept; was run via `uv run --with numpy`).
- User supplied `~/Downloads/ja909449k_si_002.cif` (23 predicted structures; COD lacks 4 of them). Extracted the 4 missing as `SI_spacegroup_148_frame_{7,8,9,10}.cif`. Their thymol connectivity was NOT checked (only cell, space group, 25 atoms).
- User supplied the paper and SI PDF. Source: `salager2010`. Findings from the paper/SI:
  - 23 predicted structures within 10 kJ/mol of the lowest; 10 are R-3 (same space group as the observed structure), others P2_1/c, P2_12_12_1, C2/c.
  - ^1H shift rms error and PSD fit pick **Structure 3** (third-lowest energy, +3 kJ/mol): 0.06 ppm (^1H), chi2 = 34.5. Authors state it is the natural structure; hexamer O-H...O motif.
  - SI structure numbers = order of data blocks in the SI CIF. Space groups checked against the SI table for all 23: consistent. Structure 3 = COD 4101955 = `spacegroup_148_frame_3`. Copied to `thymol_BEST_MATCH_structure3_R-3.cif`.
  - Structure 3: R-3, a=b=14.6614, c=22.7128 A, gamma=120, V=4228.2 A^3, Z=18 (150 atoms in the primitive cell).
- Experimental structure: Thozet & Perrin 1980 (`thozet1980`, CSD refcode THYMOL). **Not obtained** (CCDC download needs a login). Its cell, space group and temperature are unverified. A web-search snippet claimed thymol is P2_1/c with a=12.917, b=5.684, c=15.291 A, beta=109.63; unsourced, conflicts with the paper (observed = R-3), do not use.
- No temperature: the predicted structures are static model structures. There is no low-temperature measured cell yet.
- PDB generation: `scripts/make_pdb.py` (symmetry expansion of the CIF, whole molecules kept, residue THY). Outputs:
  - `thymol_structure3_R-3_unitcell.pdb`: 450 atoms, 18 molecules, CRYST1 hexagonal cell, space group written as P 1.
  - `thymol_structure3_R-3_2x2x1.pdb`: 1800 atoms, 72 molecules, 29.32 x 29.32 x 22.71 A.
  - Checks on both (own validation script, not kept): 25 bonds per molecule (0 bad molecules), density 1.062 g/cm3, minimum intermolecular distance 1.64 A (H-bond H...O), shortest O...O 2.57 A (short for an O-H...O bond; comes from the predicted structure, not checked against experiment).
- Next:
  - Get the CSD THYMOL CIF (CCDC login) and compare its cell with Structure 3.
  - Look for any low-temperature thymol redetermination.
  - Choose the supercell size for the MD cutoff (perpendicular widths of the 2x2x1 box: 25.4 A and 22.7 A).
  - Protonation/force field and hydrogen positions have not been examined.
