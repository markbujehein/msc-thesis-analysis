import numpy as np

from dos import H_MEV_FS, dos, resolution_mev


def oscillator(energy_meV, n_frames=4000, dt_fs=2.0, n_atoms=3):
    t = np.arange(n_frames) * dt_fs
    omega = energy_meV / H_MEV_FS * 2 * np.pi  # rad/fs
    v = np.cos(omega * t)[:, None, None] * np.ones((1, n_atoms, 3))
    return v


def test_peak_at_oscillator_energy():
    e, g = dos(oscillator(100.0), 2.0)
    assert abs(e[np.argmax(g)] - 100.0) < 2 * (e[1] - e[0])


def test_resolution_is_h_over_n_dt():
    assert np.isclose(resolution_mev(5000, 2.0), H_MEV_FS / (5000 * 2.0))
    e, _ = dos(oscillator(100.0, n_frames=5000), 2.0)
    assert np.isclose(e[1], resolution_mev(5000, 2.0))


def test_area_is_one():
    e, g = dos(oscillator(100.0), 2.0)
    assert np.isclose(np.trapezoid(g, e), 1.0)


def test_constant_velocity_gives_no_peak():
    v = np.ones((2000, 2, 3))  # drift only, removed by mean subtraction
    rng = np.random.default_rng(0)
    v = v + 1e-3 * rng.standard_normal(v.shape)
    _e, g = dos(v, 2.0)
    assert g.max() < 5 * g.mean()
