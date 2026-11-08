import numpy as np

H_MEV_FS = 4135.667696  # Planck constant in meV fs


def resolution_mev(n_frames, dt_fs):
    """Energy resolution h / (N dt) in meV; dt_fs is the time between frames."""
    return H_MEV_FS / (n_frames * dt_fs)


def dos(velocities, dt_fs, block=300):
    """Power spectrum of the velocities (Fourier transform of the VACF).

    velocities: (n_frames, n_atoms, 3), an array or a memory map; dt_fs: time between frames.
    The columns (atom and axis) are transformed `block` at a time, so peak memory is a few copies of
    n_frames x block values instead of several copies of the whole trajectory.
    Returns the energy in meV and g(E) with area 1.
    """
    n_frames = len(velocities)
    signal = velocities.reshape(n_frames, -1)
    window = np.hanning(n_frames)[:, None]
    power = np.zeros(n_frames // 2 + 1)
    for start in range(0, signal.shape[1], block):
        part = np.asarray(signal[:, start:start + block], dtype=np.float64)
        part -= part.mean(axis=0)
        part *= window
        power += (np.abs(np.fft.rfft(part, axis=0)) ** 2).sum(axis=1)
    energy_meV = np.fft.rfftfreq(n_frames, d=dt_fs) * H_MEV_FS
    return energy_meV, power / np.trapezoid(power, energy_meV)
