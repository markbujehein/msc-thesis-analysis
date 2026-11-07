import numpy as np

H_MEV_FS = 4135.667696  # Planck constant in meV fs


def resolution_mev(n_frames, dt_fs):
    """Energy resolution h / (N dt) in meV; dt_fs is the time between frames."""
    return H_MEV_FS / (n_frames * dt_fs)


def dos(velocities, dt_fs):
    """Power spectrum of the velocities (Fourier transform of the VACF).

    velocities: (n_frames, n_atoms, 3); dt_fs: time between frames.
    Returns the energy in meV and g(E) with area 1.
    """
    n_frames = len(velocities)
    signal = velocities.reshape(n_frames, -1)
    signal = signal - signal.mean(axis=0)
    signal = signal * np.hanning(n_frames)[:, None]
    power = (np.abs(np.fft.rfft(signal, axis=0)) ** 2).sum(axis=1)
    energy_meV = np.fft.rfftfreq(n_frames, d=dt_fs) * H_MEV_FS
    return energy_meV, power / np.trapezoid(power, energy_meV)
