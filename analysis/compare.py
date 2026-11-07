"""Put a simulated spectrum on the energy bins of the reduced measurement (run with the `ins` environment)."""
from pathlib import Path

import numpy as np


def edges_from_centres(centres_mev):
    """Bin edges halfway between neighbouring centres; the two ends extend by half a step."""
    c = np.asarray(centres_mev, dtype=float)
    middle = (c[1:] + c[:-1]) / 2
    return np.concatenate([[c[0] - (c[1] - c[0]) / 2], middle, [c[-1] + (c[-1] - c[-2]) / 2]])


def bin_integral(energy_mev, y, edges_mev):
    """Mean of the model y(E) over each bin: its integral (trapezoid, linear between grid points) over the bin width."""
    energy = np.asarray(energy_mev, dtype=float)
    y = np.asarray(y, dtype=float)
    cumulative = np.concatenate([[0.0], np.cumsum((y[1:] + y[:-1]) / 2 * np.diff(energy))])
    at_edges = np.interp(edges_mev, energy, cumulative)
    return np.diff(at_edges) / np.diff(edges_mev)


def fit_scale(model, data, error):
    """The single weighted least-squares factor s that minimises sum(((data - s model) / error)^2)."""
    weight = 1.0 / np.asarray(error, dtype=float) ** 2
    return float(np.sum(weight * data * model) / np.sum(weight * model * model))


def write_overlay(path, energy_mev, model, data, error):
    table = np.column_stack([energy_mev, model, data, error])
    np.savetxt(Path(path), table, delimiter=",", header="energy_meV,model,data,error", comments="")
