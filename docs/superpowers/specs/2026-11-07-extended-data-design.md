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
- **Decision (circularity):** AFGA is itself still being validated on few materials, and an additional validation on new materials is a secondary aim of this work. An AFGA-based prior in the VESUVIO fit would then feed the model under test into its own test. AFGA is therefore used as an independent comparator, never as a prior in a fit whose result is used to judge AFGA. Priors for the fit come from instrument-level information (resolution, aluminium container width, stoichiometry) and broad physical bounds; AFGA and the simulated hydrogen dynamics are compared with the fitted values afterwards.
- **Unverified:** script behaviour for thymol (not run); NCrystal availability in the project environments; density input (from the crystal structure).

**Current VESUVIO analysis and its validation against harmonic lattice dynamics** (source: Krzystyniak et al. 2023, `krzystyniak2023`, hexamethylenetetramine HMT and its deuterated form DHMT; read in full).
- **Measurements on one sample:** neutron and X-ray diffraction, INS on TOSCA at 10 K, neutron transmission on VESUVIO (HMT at 10, 50, 120, 160, 200, 300 K; DHMT at 300 K) and neutron Compton scattering (NCS) concurrently with the transmission.
- **Reference calculation:** CASTEP with PBE and the Tkatchenko-Scheffler dispersion correction, geometry optimisation, density-functional perturbation theory for the dynamical matrix, atom-projected densities of states, Boltzmann population factors for temperature. INS spectra from OCLIMAX (incoherent approximation, up to order ten); cross sections from NCrystal (version 2.7.3) using these densities of states.
- **NCS data treatment:** the "traditional" treatment: multiple-scattering and gamma-background corrections applied self-consistently, recoil peaks fitted in the time-of-flight domain with Gaussian momentum distributions plus final-state corrections, stoichiometric fixing of the integral intensities (aluminium excepted), aluminium width fixed at 14 +- 1 inverse angstrom from calibration runs, empty-cryostat subtraction for the back-scattering banks, double-difference configuration for the forward banks. Bespoke routines in MantidPlot.
- **Link to the simulation:** for a Gaussian momentum distribution the second moment is s^2(T) = (2m / 3 hbar^2) * integral of g(w) coth(hbar w / 2 kT) dw, and E_kin = 3 hbar^2 s^2 / 2m (their equations 1 and 2), computed from each atom-projected density of states.
- **Outcome:** the harmonic calculation reproduces the total cross section above 50 K, TOSCA spectra (RMSD about 2 cm-1), lattice constant (below 0.5 percent) and carbon and nitrogen widths. It fails for hydrogen: the measured widths are below the harmonic prediction over the whole temperature range (H 4.93 +- 0.02, D 5.59 +- 0.06 inverse angstrom at 300 K; E_kin 146.7 +- 1.2 and 94.4 +- 2.0 meV as reported). Below 50 K the transmission departs from the prediction. The authors attribute these to combined anharmonicity and nuclear quantum effects and say the two cannot be separated in the NCS observables. Fitted excess kurtosis is zero (Gaussian profiles only).
- **Checks I made on the reported numbers** (unverified until compared with the journal figures): the widths give E_kin of about 150.0 (H) and 96.5 (D) meV with 3 hbar^2 s^2 / 2m, about 2 percent above the reported values for both; the reported width ratio 1.13 gives omega_H / omega_D of about 1.56 from s^2 proportional to M*omega, while the paper reports 1.28 from a different mapping; the classical value (3/2)kT is 38.8 meV at 300 K against about 147 meV measured.
- **What is not in the paper:** no bootstrap, jackknife or Monte Carlo Markov chain validation of the fits is described, no uncertainty propagation beyond the quoted errors, and no machine-learned force field. The validation workflow attributed to the facility in the earlier paragraph is still unsupported by a source.

**Harmonic lattice dynamics versus machine-learned force fields** (open question; evidence so far).
- **What the pipeline here already does:** the INS and thermodynamic steps use a Hessian of the force field (finite displacements in OpenMM) and euphonic. Replacing GAFF2 by a machine-learned potential changes only where the Hessian comes from; the harmonic formalism stays.
- **Where the harmonic step is cheap and the force field is the limit:** the reference above shows that the harmonic model with DFT forces already reproduces TOSCA to about 2 cm-1 and cross sections above 50 K.
- **Where it is not enough:** hydrogen momentum widths (NCS) and low-temperature cross sections, which carry nuclear quantum and anharmonic effects. A classical MD run gives (3/2)kT for the kinetic energy whatever the potential, so it cannot predict these widths. A machine-learned potential does not change that; it needs path-integral dynamics or a quantum treatment on top. Path-integral MD with machine-learned potentials exists (for example [arXiv 2503.23728](https://arxiv.org/pdf/2503.23728)); a search found no comparison of a computed hydrogen kinetic energy with NCS data.
- **Evidence for machine-learned potentials on neutron spectra:** a benchmark of universal potentials on phonons and simulated INS spectra of crystals ([arXiv 2506.01860](https://arxiv.org/pdf/2506.01860); not molecular-crystal specific) and a MACE-based potential fine-tuned on targeted DFT data reproducing INS of a molecular crystal under pressure (`armstrong2026` ([arXiv 2603.05442](https://arxiv.org/abs/2603.05442), J. Phys. Chem. Lett. 2026, 17, 6596 per the arXiv listing)). Only search snippets were read; error metrics are unverified.
- **Working position:** machine-learned potentials are expected to replace DFT as the source of forces for phonons and INS; harmonic lattice dynamics on top is not replaced by them. For VESUVIO hydrogen widths a quantum treatment is still required. The statement that lattice dynamics is no longer used is not supported by these sources.
- **Test here:** compare GAFF2 and MACE Hessians on the same cell against the TOSCA spectrum; keep the VESUVIO width comparison as the stricter test.

**Relevance to this project** (my reasoning, not a source claim): thymol is hydrogen-rich, with an O-H group in a hydrogen bond and methyl and isopropyl C-H groups. A classical MD run cannot give the hydrogen kinetic energy, because the classical value is (3/2)kT regardless of the potential. A harmonic model can: with the hydrogen-projected vibrational density of states, the mean kinetic energy is a thermal sum over the modes. That gives a number from the simulation to compare with the fitted hydrogen width, and a way to test GAFF2 against MACE. This needs checking against the literature before any plan.

**Diffraction** on the same instrument can confirm that the sample has the predicted crystal structure.

**Environment:** `mantid` for steps 1 to 3 (Mantid pins Python 3.13); the harmonic comparison runs in `ins` or `md`; data cross as files.
**Open:** where the VESUVIO runs are, which sample and temperatures, whether empty-can and calibration runs exist, which Mantid VESUVIO fitting workflow the facility recommends (the `scripts/Inelastic/vesuvio` package or the algorithms above).
**Sources:** ISIS VESUVIO page (https://www.isis.stfc.ac.uk/Pages/vesuvio.aspx); Mantid LoadVesuvio documentation (https://docs.mantidproject.org/nightly/algorithms/LoadVesuvio-v1.html); Mantid 7.0.0 source, `plugins/python/algorithms/Vesuvio*.py`.

### 3. Better force fields (after the GAFF2 comparison)

- **Goal:** replace GAFF2 in the MD and Hessian steps and measure how much the spectrum changes.
- **Candidates:** MACE, ANI-2x and AIMNet2 (machine-learned; a 2025 preprint compares all three on organic crystals, [arXiv 2505.06462](https://arxiv.org/pdf/2505.06462)), and AMOEBA (classical, polarizable, available in OpenMM). CHARMM-type fields are fixed-charge like GAFF2, so they are not expected to differ much.
- **To investigate: OMol25.** Models trained on the OMol25 molecular data (wB97M-V reference per `levine2025`), compared with GAFF2 and with the molecular-crystal task of UMA (PBE-D3 labels per a search summary) on the Hessian and the TOSCA spectrum. Open points: how dispersion is treated in the OMol25 labels and models (not confirmed from the papers read); whether the 6 angstrom cutoff matters for a crystal.
- **Evidence on AMOEBA:** better than fixed-charge fields for sublimation free energies of five organic crystals and for crystal hydrate stability; no better, sometimes worse, than GAFF for solvation free energies. No lattice-energy or vibrational comparison with GAFF2 was found. Unverified for this crystal.
- **Unverified:** accuracy of any candidate for crystal vibrations; element coverage (C, H, O) of each ML model; whether thymol can be parametrized for AMOEBA; cost of an 1800-atom Hessian.

**State of machine-learned methods** (survey of 2026-11-07; abstracts, search summaries and the first 100000 characters of the UMA paper only, so every claim below is the authors' own and unverified).

| Area | Status found | Relevance here |
|---|---|---|
| Universal potentials: OMol25 and UMA (Meta FAIR) | `levine2025`: over 100 million DFT calculations (about 83 million molecular systems, up to 350 atoms, 83 elements) at wB97M-V/def2-TZVPD, with variable charge and spin. `wood2025`: UMA trained on about 500 million structures from OMol25 (wB97M-V, ORCA), OMat24 (PBE, VASP), OC20, ODAC25 and OMC25 (molecular crystals), one energy head with a task embedding that selects the dataset's DFT settings; mixture of linear experts (UMA-medium: 1.4 billion parameters, about 50 million active); 6 angstrom cutoff. | Replaces the force evaluation, not the formalism: a Hessian from UMA instead of GAFF2 or DFT. |
| Molecular crystals: OMC25 | `gharakhanyan2025`: over 27 million structures, 12 elements, up to 300 atoms per cell, PBE with D3 dispersion in VASP (from a search summary; unverified). UMA reports lattice energies within 3 kJ/mol on the 7th crystal-structure-prediction blind test. | The relevant task for crystalline thymol; its reference level (PBE-D3) is close to the CASTEP PBE with Tkatchenko-Scheffler used in `krzystyniak2023`. |
| ML Hamiltonians (ML-DFT) | `li2022` (DeepH) learns the DFT Hamiltonian from local environments and skips the self-consistent cycle; several later variants and a 2025 review were found. Reported mostly for materials and electronic structure. | Not needed for INS; no molecular-crystal phonon result found. |
| ML functionals | Skala (`luise2025`): 2.8 kcal/mol on GMTKN55 at semi-local cost (authors' claim); DM21 and aPBE0-ML named in a 2026 review. | Improves the reference level of future training data; no forces or phonons benchmark found. |
| ML basis sets | `khan2024`: environment-adapted basis sets (preprint). | Niche; no bearing on this work. |
| ML dispersion (D3, D4 replacements) | NN-Dx (preprint on Research Square; 70 to 91 percent lower error than D4 on held-out non-covalent benchmarks, abstract only), D3-ML for MP2, DNN-MBD. | When the training labels include D3 (as in OMC25) the potential learns the dispersion-corrected surface, so no separate D3 step remains inside the model. Beyond the cutoff the tail is missing. |
| ML long-range | Latent Ewald summation (`cheng2024`): latent charges plus an Ewald sum, about twice the cost of a short-range potential, authors' results only. UMA states that interactions beyond 6 angstrom are effectively absent. | Matters for polar crystals; thymol is weakly polar (O-H hydrogen bond), unverified. |
| ML lattice dynamics | No separate method found: the potential supplies a Hessian or finite displacements and the harmonic or anharmonic step is the usual one. Benchmarks: ThO2 anharmonicity (`bandi2024`), universal potentials against INS (`han2025`), fine-tuned MACE against INS under pressure (`armstrong2026`), ANI-2x and an equivariant network on ice XI with VSCF and VCI (a 2026 Digital Discovery paper, first author Petrov, summary only, not in `refs.bib`). | The same route as the planned MACE test. |
| ML path-integral MD | `fan2025` and others. No comparison with neutron Compton data found. | The missing piece for hydrogen widths. |

*What UMA and OMol25 effectively replace for analyses other than VESUVIO* (reasoning, not source claims):
- **Replaced:** DFT single points, relaxations, finite-displacement Hessians and short MD for molecules and molecular crystals, at force-field cost. For thymol this includes the DFT vibrational calculation planned in `dft/`, to the extent that the OMC25 level of theory is acceptable.
- **Not replaced:** the quality ceiling of the reference method (PBE-D3 for crystals, or wB97M-V for molecules); nuclear quantum effects and anharmonic effects beyond what the classical-nuclei surface gives; interactions beyond the cutoff; unseen charge and spin states; any quantity other than energy, forces and stress, such as spectra or densities.
- **Checks before use:** whether the OMC25 task covers C, H, O (12 elements; list unverified); the licence of the weights (a search summary mentions geographic and acceptable-use restrictions), which matters for a public portfolio repository; Hessian cost for 1800 atoms with the conservative models (about 16 steps per second for 1000 atoms for UMA-small per the paper; a finite-displacement Hessian then needs on the order of minutes to an hour, my estimate); agreement with the TOSCA spectrum, which is the real test.

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
