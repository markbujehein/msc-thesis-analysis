import numpy as np
import pytest

from thermo import thermo_from_dos

KB_MEV = 0.08617333262  # meV/K
ENERGY = np.arange(0.0, 100.5, 0.5)


def spike(*positions_and_weights):
    g = np.zeros_like(ENERGY)
    for e, w in positions_and_weights:
        g[np.argmin(abs(ENERGY - e))] = w
    return g


def test_einstein_zero_point_and_low_temperature_limit():
    result = thermo_from_dos(ENERGY, spike((30.0, 1.0)), n_modes=3, temperatures_K=np.array([10.0]))
    assert result["U_meV"][0] == pytest.approx(3 * 15.0, abs=1e-6)


def test_einstein_high_temperature_heat_capacity_is_dulong_petit():
    result = thermo_from_dos(ENERGY, spike((1.0, 1.0)), n_modes=3, temperatures_K=np.array([300.0]))
    assert result["Cv_meV_per_K"][0] == pytest.approx(3 * KB_MEV, rel=0.01)


def test_free_energy_is_u_minus_ts():
    t = np.array([50.0, 150.0])
    result = thermo_from_dos(ENERGY, spike((20.0, 1.0), (60.0, 2.0)), n_modes=6, temperatures_K=t)
    np.testing.assert_allclose(result["F_meV"], result["U_meV"] - t * result["S_meV_per_K"], rtol=1e-9)


def test_zero_energy_modes_are_dropped_not_nan():
    with_zero = thermo_from_dos(ENERGY, spike((0.0, 5.0), (30.0, 1.0)), n_modes=3, temperatures_K=np.array([10.0, 100.0]))
    without = thermo_from_dos(ENERGY, spike((30.0, 1.0)), n_modes=3, temperatures_K=np.array([10.0, 100.0]))
    for key, value in with_zero.items():
        assert np.isfinite(value).all()
        np.testing.assert_allclose(value, without[key], rtol=1e-9)
