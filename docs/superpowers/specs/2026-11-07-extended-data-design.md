# Extended data analysis: IR, Raman, VESUVIO, QENS (rough spec)

Date: 2026-11-07. Status: **rough**, to be refined before any plan is written. Work continues in later sessions.

Parent spec: file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/specs/2026-11-06-md-dos-design.md
Plan in progress (TOSCA INS from GAFF2): file:///home/mark/Work/msc-thesis-analysis/docs/superpowers/plans/2026-11-06-ins-from-gaff2.md

## Aim

The main line stays: simulated TOSCA INS spectrum of thymol versus the measured TOSCA spectrum. This spec adds independent measurements as cross-checks and extra analysis, in priority order. None of it blocks the main line.

## Rules for all data

- The real data is unpublished. It is git-ignored and never committed: `data/zeppelin-experimental-data/`, `data/reduced/`, `data/REDUCTION.md`, `dft/zeppelin-dft-input/`.
- `data/` itself is tracked. It will hold **synthetic stand-in data** with the same file layout and columns as the real data, so that anyone who downloads the repo can run the code and the tests. The generator is code in the repo; the output carries no real values.
- Energies in meV. Wavenumbers (cm^-1) from IR and Raman are converted at the reader, never plotted or stored as cm^-1.

## What exists on disk (real, ignored)

| Technique | Files in `data/zeppelin-experimental-data/` | Notes |
|---|---|---|
| TOSCA INS | `tosca/TSC25987` to `TSC25996.nxs` | thymol is TSC25989 and TSC25990; reduced already |
| FTIR (ATR) | `IR/thymol_4cm-1_128scans_ATR.dat`, `IR/pcymene_64scans_FTIR_2.dat` | thymol and p-cymene |
| Raman | `Raman/thymol_532nm_LR.dat`, `Raman/Thymol_785nm_..._290K.txt`, `..._6K.txt`, `Raman/p-cymene_test_532nm.dat` | thymol at 290 K and 6 K, 0 to 4000 cm^-1 |
| VESUVIO | not in the repo yet | location and format to be given by the user |
| DFT inputs | `dft/zeppelin-dft-input/Thymol_vib.com`, `p_cymene.com` | Gaussian inputs for vibrational calculations; `dft/` is for future work |

## Work streams, in priority order

### 0. Synthetic stand-in data (supports everything)

- **Goal:** the repo runs end to end without the real data.
- **Output:** `data/synthetic/` (or the same names as the real tree) with generated TOSCA-like, IR-like and Raman-like files, produced by one script plus a test that checks shape and columns.
- **Open:** how close to the real spectra the synthetic ones should look (band positions from the simulation are a natural source).

### 1. IR and Raman cross-checks (low priority)

- **Goal:** compare vibrational band positions with the TOSCA data and with the simulated DOS and INS spectrum.
- **Inputs:** the IR and Raman files above. The Raman 6 K and 290 K pair gives a temperature check on the low-energy lattice modes.
- **Method (rough):** read, convert to meV, normalise, pick bands, overlay on the INS spectrum. Selection rules differ (IR and Raman see only some modes; INS sees all, weighted by hydrogen displacement), so the comparison is of positions, not intensities.
- **Limit:** a classical force field gives no IR or Raman intensities. Intensities would need the DFT work in `dft/`.
- **Environment:** `ins` (numpy and pandas are already shared); no new heavy dependency expected.

### 2. VESUVIO (after TOSCA works)

- **What the user states VESUVIO offers:** energy range from about 10 meV to several eV; the exact atomic composition of the sample; a fairly precise cross-section; extra information below 25 meV, less precise than TOSCA.
- **Measurements to parse (user's list):** transmission, forward scattering, backscattering, virtual diffraction, gamma scattering. Combined, they allow neutron Compton scattering (NCS), which relies on thorough fitting and sampling.
- **Method (rough):** reduce each measurement type with Mantid, then combine in a fit; sample the posterior with dynesty (feature `bayes` already exists).
- **Unverified:** that Mantid provides each of these steps as described. Check the Mantid VESUVIO documentation before planning.
- **Environment:** `mantid` for reduction; fitting probably `ins` (to be decided, because Mantid and abinslib cannot share an environment; data crosses as files).
- **Open:** where the VESUVIO runs are, which sample and temperatures, whether calibration and empty-can runs exist.

### 3. QENS on TOSCA data (very last)

- **Goal:** quasi-elastic analysis of the TOSCA data, as the supervisor has done on several occasions.
- **Prerequisite:** everything above works. TOSCA is an indirect-geometry instrument, so what can be extracted from the quasi-elastic region has to be checked against the supervisor's earlier work.
- **Open:** which runs, which model, which software. Ask the supervisor for the earlier analyses.

## Order and dependencies

TOSCA INS simulation and overlay (main line, in progress) then synthetic data, then IR and Raman, then VESUVIO, then QENS. The Bayesian band model of the parent spec can use any of these as additional data.

## Success criteria (rough)

- Synthetic data: a fresh clone passes `pixi run test-unit-all` and the notebooks run on the synthetic files.
- IR and Raman: a table of band positions in meV next to the INS peaks, with each band assigned to a simulated mode group or marked unassigned.
- VESUVIO: reduced spectra for each measurement type, a fit result with sampled uncertainties, and the composition and cross-section it implies.
- QENS: agreed with the supervisor before starting.

## Open questions

1. Where is the VESUVIO data, and in what format?
2. Should synthetic data mimic the real spectra or only the file layout?
3. Do the IR and Raman files have a documented calibration and background treatment?
4. Which earlier QENS analyses can be reused?
