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
| VESUVIO | not in the repo yet | location and format not yet known |
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

**Instrument.** VESUVIO is an inverse-geometry time-of-flight spectrometer at ISIS. Its main technique is neutron Compton scattering (NCS, also called deep inelastic neutron scattering). The ISIS instrument page gives a dynamic range of 1 to 100 eV, an analysing energy of 4906 meV (gold) and a Q range of 30 to 200 per angstrom. It also lists diffraction (130 to 166 degrees, d-spacing 0.5 to 8 angstrom), transmission, resonant capture and prompt gamma analysis.

- **Below 25 meV:** this region is expected to complement TOSCA at lower precision. The sources read do not cover it; to be checked.
- **Gamma background and multiple scattering** are corrections applied during the fit (`VesuvioCorrections`), not separate measurement types. Mantid's `VesuvioDiffractionReduction` is deprecated (April 2017).
- **Composition and cross-section** follow from the transmission and capture techniques. Which Mantid steps deliver them is open (`VesuvioTransmission` and `VesuvioThickness` are candidates).

**Real pipeline (verified against the Mantid source unless marked):**

1. Raw runs are measured with a gold foil cycled in and out of the scattered beam. `LoadVesuvio` forms the difference: single difference (foil in minus foil out) for forward scattering; single, double or thick difference for back scattering.
2. Transmission and sample thickness: `VesuvioTransmission`, `VesuvioThickness`. Instrument resolution: `VesuvioResolution`.
3. Fit the neutron Compton profile of each atomic mass in the sample (H, C, O): `VesuvioPreFit`, `VesuvioTOFFit`, with `VesuvioCorrections` for gamma background and multiple scattering. Result: the momentum distribution n(p) of each nucleus.
4. For hydrogen, the width and the mean kinetic energy of n(p) follow. These are quantum quantities.

**Mantid VESUVIO algorithms (7.0.0; 14 with "Vesuvio" in the name; read from the package source and the Mantid documentation):**

| Step | Algorithm | What it does |
|---|---|---|
| Load | `LoadVesuvio`, `LoadEmptyVesuvio` | raw runs with foil-difference modes; empty instrument geometry |
| Sample | `VesuvioTransmission`, `VesuvioThickness` | transmission spectrum; sample density from transmission |
| Resolution | `VesuvioResolution`, `VesuvioL1ThetaResolution` | resolution function; Monte Carlo of final flight path and angle spread per detector (1 000 000 events by default) |
| Prior estimate | `VesuvioPeakPrediction` | peak widths from a Debye or Einstein model |
| Fit | `VesuvioPreFit`, `VesuvioTOFFit` | smoothing and masking; Compton profile fit per bank or per detector (Levenberg-Marquardt by default) |
| Corrections | `VesuvioCorrections`, `VesuvioCalculateGammaBackground`, `VesuvioCalculateMS` | gamma background (forward banks only, from a simulation over the foils); multiple scattering by a seeded Monte Carlo after Mayers et al. (10 runs of 50 000 events by default) |
| Whole workflow | `VesuvioAnalysis` | iterates fit and corrections in time of flight, then fits hydrogen in y-space; forward scattering only |
| Deprecated | `VesuvioDiffractionReduction` | since April 2017 |

**How the fitting is done in Mantid** (source read): in `VesuvioAnalysis` each detector spectrum is fitted separately by least squares (SLSQP, chi-squared of the Compton profile model); widths and intensities are then averaged over detectors after discarding values more than one standard deviation from the mean; hydrogen is finally fitted in y-space with a simplex minimizer. The quoted uncertainty is the scatter over detectors. A search of the Mantid VESUVIO sources found no bootstrap, jackknife or MCMC code. The Monte Carlo in Mantid is forward simulation of corrections and resolution, not statistical inference.

**Unverified:** that instrument scientists validate fits by bootstrap or jackknife resampling with Monte Carlo inference. Neither the Mantid sources nor the literature search supports or contradicts it. A reference or the scientists' scripts are needed.

**Is the old-style workflow required?** My reasoning, to be tested:

- The forward-model pieces cannot be skipped or cheaply re-implemented: foil differencing, instrument parameters and resolution, transmission, and the gamma and multiple-scattering corrections. Use the Mantid implementations.
- The fitting stage is a different matter. Mantid uses plain least squares and detector scatter, so a Bayesian fit (dynesty, already a dependency) can replace it: one joint fit over all detectors with a width and an intensity per mass shared across detectors, using the model function in `Inelastic.vesuvio.analysisHelpers` (`calculate_ncp`, plain numpy) on Mantid-corrected data.
- Catch: the corrections depend on the fitted parameters, which is why Mantid iterates. A Bayesian fit on corrected data is conditional on the converged corrections and ignores their uncertainty unless the loop is repeated.
- Test of validity: run `VesuvioAnalysis` as the reference on one run, fit the same corrected spectra with the Bayesian model, and compare widths and intensities per mass against the detector scatter. Add a leave-one-detector-out (jackknife) and a bootstrap over detectors on top of our fit, which is cheap because the fits are already per detector. Agreement validates the fit stage; the correction stage stays Mantid's.

**Prior or cross-check from the Average Functional Group Approximation (AFGA).** Sources: Romanelli et al. 2021 (`romanelli2021`, the method) and Romanelli et al. 2023 (`romanelli2023`, a worked example with NCrystal); implemented in NCrystal as `ncrystal_hfg2ncmat` (https://github.com/mctools/ncrystal/blob/main/ncrystal_python/src/NCrystal/hfg2ncmat.py). Both papers were read.

*What it is.*
- **Basis:** transmission measurements of the 20 proteinogenic amino acids on VESUVIO (1 meV to 10 keV, 300 K) interpreted with the multi-phonon expansion in the incoherent approximation and Gaussian (Sjolander) approximation, using hydrogen-projected vibrational densities of states from first-principles phonon calculations (Quantum ESPRESSO, density functional perturbation theory). Above 3 eV the impulse approximation takes over.
- **Approximation:** the atom-projected hydrogen density of states g_j(w) is averaged over all hydrogens of the same functional group and over all molecules containing it, giving nine functions: CHali, CHaro, CH2, CH3, NH3, NH2, NH, OH, SH. The cross section of a new compound is the stoichiometric sum over its groups, neglecting correlations between groups. The average of cross sections equals the cross section of the average density of states for CH, CH2 and CH3 within numerical accuracy, so the nine average densities of states suffice and allow other temperatures.
- **Other atoms:** applying the expansion only to hydrogen and using free scattering cross sections for C, N, O, S (model 2) reproduces the data almost as well as treating all atoms; the heavier atoms contribute in proportion to free cross section and stoichiometry. In `hfg2ncmat` they receive a Debye model (400 K by default) only because NCrystal needs a dynamics for each element.
- **Limits of the cross section:** low temperature and meV energies give the sum of bound cross sections; above a few eV the free cross section, about a quarter of the bound value for hydrogen; between them the cross section depends on the density of states and the temperature.

*Validation reported.*
- The functions are defined from the amino acids; 13 of them are then predicted from the group functions and agree well with the data (the paper does not say which 7 define the functions; six appear in its first comparison figure). Differences appear below a few meV, up to about 5 percent at 1 meV (lysine).
- Triphenylmethane (aromatic CH only, measured on VESUVIO) agrees very well. PMMA agrees well and better than direct DFT below about 100 meV, attributed to its disorder.
- The 2023 paper treats polymers and mixtures as linear combinations and appeals to a central-limit argument for hydrogen dynamics in large molecules.
- The authors state that high accuracy is not expected for small crystalline systems. Crystal-specific features such as Bragg edges are not part of the model. Validation targets total cross sections; no kinetic energies or Compton profile widths are compared.

*Assessment for thymol* (reasoning, not source claims).
- **Group coverage:** all thymol hydrogens fall in groups represented in the training set. Spec: `3xCHaro+1xCHali+3xCH3+1xOH`, 14 hydrogens, matching C10H14O. The OH average mixes alcohol, carboxylic and phenolic environments in strongly hydrogen-bonded amino-acid crystals.
- **Small crystal:** the least favourable case named by the authors. The expected failure region is the low-energy part (methyl rotation and lattice modes, which are crystal specific), exactly where the sub-25 meV information lies.
- **Cross section prior or cross-check:** well matched to the purpose of the method; use with a generous width, and compare with the sample transmission.
- **Hydrogen width prior:** not what the method was validated for. The width follows from the kinetic energy, which weights the stretching modes (high energy), while cross-section tests mostly probe the low-energy shape. The prior is possible through the average density of states but is a weaker guess than the cross-section use.
- **Open decision:** prior or cross-check; if the VESUVIO fit is meant to test the simulated hydrogen dynamics, the prior must not be taken from the simulation. An AFGA-based prior is independent of the simulation and is acceptable on that count.
- **Unverified:** script behaviour for thymol (not run); NCrystal availability in the project environments; density input (from the crystal structure).

**Relevance to this project** (my reasoning, not a source claim): thymol is hydrogen-rich, with an O-H group in a hydrogen bond and methyl and isopropyl C-H groups. A classical MD run cannot give the hydrogen kinetic energy, because the classical value is (3/2)kT regardless of the potential. A harmonic model can: with the hydrogen-projected vibrational density of states, the mean kinetic energy is a thermal sum over the modes. That gives a number from the simulation to compare with the fitted hydrogen width, and a way to test GAFF2 against MACE. This needs checking against the literature before any plan.

**Diffraction** on the same instrument can confirm that the sample has the predicted crystal structure.

**Environment:** `mantid` for steps 1 to 3 (Mantid pins Python 3.13); the harmonic comparison runs in `ins` or `md`; data cross as files.
**Open:** where the VESUVIO runs are, which sample and temperatures, whether empty-can and calibration runs exist, which Mantid VESUVIO fitting workflow the facility recommends (the `scripts/Inelastic/vesuvio` package or the algorithms above).
**Sources:** ISIS VESUVIO page (https://www.isis.stfc.ac.uk/Pages/vesuvio.aspx); Mantid LoadVesuvio documentation (https://docs.mantidproject.org/nightly/algorithms/LoadVesuvio-v1.html); Mantid 7.0.0 source, `plugins/python/algorithms/Vesuvio*.py`.

### 3. Better force fields (after the GAFF2 comparison)

- **Goal:** replace GAFF2 in the MD and Hessian steps and measure how much the spectrum changes.
- **Candidates:** MACE, ANI-2x and AIMNet2 (machine-learned; a 2025 preprint compares all three on organic crystals, [arXiv 2505.06462](https://arxiv.org/pdf/2505.06462)), and AMOEBA (classical, polarizable, available in OpenMM). CHARMM-type fields are fixed-charge like GAFF2, so they are not expected to differ much.
- **Evidence on AMOEBA:** better than fixed-charge fields for sublimation free energies of five organic crystals and for crystal hydrate stability; no better, sometimes worse, than GAFF for solvation free energies. No lattice-energy or vibrational comparison with GAFF2 was found. Unverified for this crystal.
- **Unverified:** accuracy of any candidate for crystal vibrations; element coverage (C, H, O) of each ML model; whether thymol can be parametrized for AMOEBA; cost of an 1800-atom Hessian.

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
