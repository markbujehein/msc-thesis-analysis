"""TOSCA reduction with Mantid: all-detector TOF counts -> two bank spectra on an energy-transfer axis (meV).

Method and open points: data/REDUCTION.md. Run with the analysis env python.
"""
import numpy as np
from mantid.simpleapi import (
    ExtractSpectra,
    ISISIndirectEnergyTransfer,
    TOSCABankCorrection,
    mtd,
)

REBIN = "-2.5,0.015,3,-0.005,1000"  # meV: 0.015 steps to 3 meV, then 0.5 percent steps to 1000 meV (the TOSCA default)
SEARCH_RANGE = "20,300"  # meV, where TOSCABankCorrection looks for a peak shared by both banks


def reduce_run(path):
    """Reduce one TOSCA file. Returns a dict: energy_meV, banks and errors (2, n_bins) in counts per meV, scale_factors, title."""
    ISISIndirectEnergyTransfer(
        InputFiles=str(path), Instrument="TOSCA", Analyser="graphite", Reflection="002",
        SpectraRange=[1, 140], GroupingMethod="IPF", UnitX="DeltaE", RebinString=REBIN,
        OutputWorkspace="reduced",
    )
    banks = ExtractSpectra(mtd["reduced"].getItem(0), WorkspaceIndexList=[0, 1], OutputWorkspace="banks")
    corrected = TOSCABankCorrection(banks, SearchRange=SEARCH_RANGE, OutputWorkspace="corrected")
    ws = corrected.OutputWorkspace
    edges = ws.readX(0)
    result = {
        "energy_meV": (edges[1:] + edges[:-1]) / 2,
        "banks": np.array([ws.readY(i) for i in range(2)]),
        "errors": np.array([ws.readE(i) for i in range(2)]),
        "scale_factors": [corrected.ScaleFactor1, corrected.ScaleFactor2],
        "title": ws.getTitle(),
    }
    mtd.clear()
    return result


def write_csv(result, path):
    """Columns: energy (meV), bank 1, bank 2, error 1, error 2 (counts per meV)."""
    table = np.column_stack([result["energy_meV"], result["banks"].T, result["errors"].T])
    np.savetxt(path, table, delimiter=",", header="energy_meV,bank1,bank2,error1,error2", comments="")
