import numpy as np

KEYS = ("fc", "origins", "sc_matrix", "unit_cell_nm", "frac_positions", "symbols", "masses_amu")


def assign_cells(sc_positions_nm, unit_positions_nm, unit_cell_nm, tol_nm=1e-3):
    """Match every supercell atom to a unit-cell atom plus an integer lattice offset.

    Returns atom_in_cell (N,) and cell_origin (N, 3), in units of the unit-cell vectors.
    Raises ValueError naming the first atom with no match within tol_nm.
    """
    inverse = np.linalg.inv(unit_cell_nm)
    sc_frac = np.asarray(sc_positions_nm) @ inverse
    unit_frac = np.asarray(unit_positions_nm) @ inverse
    atom_in_cell = np.empty(len(sc_frac), dtype=int)
    cell_origin = np.empty((len(sc_frac), 3), dtype=int)
    for i, frac in enumerate(sc_frac):
        offset = frac - unit_frac
        origin = np.round(offset)
        distance = np.linalg.norm((offset - origin) @ unit_cell_nm, axis=1)
        best = distance.argmin()
        if distance[best] > tol_nm:
            raise ValueError(f"atom {i} matches no unit-cell atom (closest {distance[best]:.4f} nm)")
        atom_in_cell[i], cell_origin[i] = best, origin[best]
    return atom_in_cell, cell_origin


def unfold_hessian(hessian, atom_in_cell, cell_origin, n_cell_atoms):
    """Supercell Hessian (3N, 3N) to force constants fc[c, i, j] = hessian[atom i in the origin cell, atom j in cell c].

    Returns origins (n_cells, 3) and fc (n_cells, 3 n_cell_atoms, 3 n_cell_atoms). Cell (0, 0, 0) must exist,
    and every (cell, atom) pair must occur exactly once.
    """
    origins = np.unique(cell_origin, axis=0)
    index = {(tuple(o), a): n for n, (o, a) in enumerate(zip(cell_origin, atom_in_cell))}
    if len(index) != len(atom_in_cell) or len(index) != len(origins) * n_cell_atoms:
        raise ValueError("each (cell, atom) pair must occur exactly once in the supercell")
    fc = np.zeros((len(origins), 3 * n_cell_atoms, 3 * n_cell_atoms))
    for c, origin in enumerate(origins):
        for a in range(n_cell_atoms):
            j = index[(tuple(origin), a)]
            for i in range(n_cell_atoms):
                ref = index[((0, 0, 0), i)]
                fc[c, 3 * i : 3 * i + 3, 3 * a : 3 * a + 3] = hessian[3 * ref : 3 * ref + 3, 3 * j : 3 * j + 3]
    return origins, fc


def save_force_constants(path, fc, origins, sc_matrix, unit_cell_nm, frac_positions, symbols, masses_amu):
    """Write the force constants (kJ/mol/nm^2) and the crystal they belong to as .npz."""
    np.savez(path, fc=fc, origins=origins, sc_matrix=sc_matrix, unit_cell_nm=unit_cell_nm,
             frac_positions=frac_positions, symbols=symbols, masses_amu=masses_amu)


def load_force_constants(path):
    with np.load(path) as data:
        return {key: data[key] for key in KEYS}
