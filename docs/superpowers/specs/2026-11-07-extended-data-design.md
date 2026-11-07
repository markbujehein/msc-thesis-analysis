# Extended analysis: IR, Raman, VESUVIO, MACE, quasi-elastic (rough spec)

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

**Correction.** The first version of this section repeated a verbal description without checking it. Checked against the ISIS instrument page and the Mantid 7.0.0 source, three points change:

- VESUVIO is an inverse-geometry time-of-flight instrument. Its main technique is neutron Compton scattering (NCS, also called deep inelastic neutron scattering). The ISIS page gives a dynamic range of 1 to 100 eV, an analysing energy of 4906 meV (gold) and a Q range of 30 to 200 per angstrom. The user states that VESUVIO also gives information below 25 meV, less precise than TOSCA, and that this region matters. The ISIS page lists the NCS range as 1 to 100 eV and says nothing about the region below 25 meV, so the low-energy claim is **not confirmed by the sources read** and needs a dedicated check (which detectors, which analysis). TOSCA remains the main instrument for the vibrational spectrum.
- "Gamma scattering" and "virtual diffraction" are not extra measurement types in Mantid's loader. In `VesuvioCorrections` the gamma background and multiple scattering are corrections applied to the fit. Diffraction is a separate capability of the instrument (ISIS page: 130 to 166 degrees, d-spacing 0.5 to 8 angstrom); Mantid's `VesuvioDiffractionReduction` is deprecated (April 2017).
- Composition and cross-section: the user states that VESUVIO gives the exact atomic composition and a precise cross-section; that is accepted as correct. The ISIS page lists transmission, resonant capture and prompt gamma analysis on the instrument as the techniques that provide such information. Which Mantid steps deliver it is open (`VesuvioTransmission` and `VesuvioThickness` are candidates).

**Real pipeline (verified against the Mantid source unless marked):**

1. Raw runs are measured with a gold foil cycled in and out of the scattered beam. `LoadVesuvio` forms the difference: single difference (foil in minus foil out) for forward scattering; single, double or thick difference for back scattering.
2. Transmission and sample thickness: `VesuvioTransmission`, `VesuvioThickness`. Instrument resolution: `VesuvioResolution`.
3. Fit the neutron Compton profile of each atomic mass in the sample (H, C, O): `VesuvioPreFit`, `VesuvioTOFFit`, with `VesuvioCorrections` for gamma background and multiple scattering. Result: the momentum distribution n(p) of each nucleus.
4. For hydrogen, the width and the mean kinetic energy of n(p) follow. These are quantum quantities.

**Relevance to this project** (my reasoning, not a source claim): thymol is hydrogen-rich, with an O-H group in a hydrogen bond and methyl and isopropyl C-H groups. A classical MD run cannot give the hydrogen kinetic energy, because the classical value is (3/2)kT regardless of the potential. A harmonic model can: with the hydrogen-projected vibrational density of states, the mean kinetic energy is a thermal sum over the modes. That gives a number from the simulation to compare with the fitted hydrogen width, and a way to test GAFF2 against MACE. This needs checking against the literature before any plan.

**Diffraction** on the same instrument can confirm that the sample has the predicted crystal structure.

**Environment:** `mantid` for steps 1 to 3 (Mantid pins Python 3.13); the harmonic comparison runs in `ins` or `md`; data cross as files.
**Open:** where the VESUVIO runs are, which sample and temperatures, whether empty-can and calibration runs exist, which Mantid VESUVIO fitting workflow the facility recommends (the `scripts/Inelastic/vesuvio` package or the algorithms above).
**Sources:** ISIS VESUVIO page (https://www.isis.stfc.ac.uk/Pages/vesuvio.aspx); Mantid LoadVesuvio documentation (https://docs.mantidproject.org/nightly/algorithms/LoadVesuvio-v1.html); Mantid 7.0.0 source, `plugins/python/algorithms/Vesuvio*.py`.

### 3. MACE force field (after the GAFF2 comparison)

- **Goal:** a machine-learned interatomic potential (MACE) as a second force field for the same MD and Hessian steps, to see how much the spectrum depends on the potential. GAFF2 is a fixed-form classical field with unfitted charges.
- **Unverified:** which pretrained MACE model fits an organic molecular crystal, whether it runs through ASE in this repo's environments, and the cost of a 1800-atom Hessian with it. Check before planning.

### 4. QENS check on the TOSCA data (exploratory, may lead nowhere)

- **What:** QENS is a method, not a result. It is not known whether the TOSCA data contain any quasi-elastic signal, so the first step is to look, and the outcome may be that there is nothing to analyse.
- **Precedent:** the thesis supervisor has applied the method to TOSCA data on several occasions. Their analyses show what is feasible and where the limits are.
- **Needs:** the reduced spectra. A comparison with simulation would need MD at matching temperatures, which does not exist yet.
- **Open:** which runs, whether any broadening is visible, which model and software.

## Order and dependencies

TOSCA INS simulation and comparison (main line, in progress), then synthetic data, then IR and Raman, then MACE and VESUVIO, and last an exploratory QENS check that may find nothing. The Bayesian band model of the parent spec can use any of these as additional data.

## Success criteria (rough)

- Synthetic data: a fresh clone passes `pixi run test-unit-all` and the notebooks run on the synthetic files.
- IR and Raman: a table of band positions in meV next to the INS peaks, with each band assigned to a simulated mode group or marked unassigned.
- VESUVIO: fitted hydrogen momentum width and kinetic energy with uncertainties, next to the simulated value.
- QENS check: a yes or no on whether the data show a quasi-elastic signal, agreed with the supervisor before any fitting.

## Open questions

1. Where is the VESUVIO data, and in what format?
2. Should synthetic data mimic the real spectra or only the file layout?
3. Do the IR and Raman files have a documented calibration and background treatment?
4. Which earlier QENS analyses by the supervisor can be reused?
