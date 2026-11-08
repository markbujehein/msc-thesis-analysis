"""mmCIF text for a molecular crystal, for the Mol* viewer (the crystallographic format it is built around)."""
import numpy as np


def cell_parameters(cell):
    """Lengths a, b, c (angstrom) and angles alpha, beta, gamma (degrees) of a 3x3 cell (rows are vectors)."""
    a, b, c = (np.asarray(cell, dtype=float)[i] for i in range(3))
    angle = lambda u, v: np.degrees(np.arccos(u @ v / (np.linalg.norm(u) * np.linalg.norm(v))))  # noqa: E731
    return (*(np.linalg.norm(v) for v in (a, b, c)), angle(b, c), angle(a, c), angle(a, b))


def chain_id(index):
    """A, B, ..., Z, AA, AB, ... for index 0, 1, ... (spreadsheet-style column names)."""
    name = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(65 + rest) + name
    return name


def mmcif_text(symbols, positions, cell, molecule):
    """mmCIF with the cell, space group P 1 and one HETATM row per atom.

    positions: (n, 3) Cartesian, angstrom; molecule: per-atom molecule index, written as residue 1, 2, ... and as
    chain A, B, ... (Mol* colours carbon per chain, so each molecule gets its own carbon colour).
    """
    a, b, c, alpha, beta, gamma = cell_parameters(cell)
    lines = [
        "data_crystal",
        f"_cell.length_a {a:.3f}", f"_cell.length_b {b:.3f}", f"_cell.length_c {c:.3f}",
        f"_cell.angle_alpha {alpha:.3f}", f"_cell.angle_beta {beta:.3f}", f"_cell.angle_gamma {gamma:.3f}",
        "_symmetry.space_group_name_H-M 'P 1'",
        "loop_",
        *(f"_atom_site.{name}" for name in (
            "group_PDB", "id", "type_symbol", "label_atom_id", "label_comp_id", "label_asym_id",
            "label_entity_id", "label_seq_id", "Cartn_x", "Cartn_y", "Cartn_z", "occupancy", "B_iso_or_equiv",
            "pdbx_PDB_model_num",
        )),
    ]
    for i, (symbol, (x, y, z), mol) in enumerate(zip(symbols, positions, molecule), start=1):
        lines.append(f"HETATM {i} {symbol} {symbol}{i} THY {chain_id(mol)} 1 {mol + 1} {x:.3f} {y:.3f} {z:.3f} 1.0 0.0 1")
    return "\n".join(lines) + "\n"


BACKGROUND = "#808080"  # mid grey: dark carbon and white hydrogen both show
ELEMENT_COLORS = {"C": "#303030", "H": "#ffffff", "O": "#e01010"}  # C dark, H white, O red


def cell_edges(origin, vectors):
    """The 12 edges of a cell as (start, end) pairs of Cartesian points; vectors are the rows a, b, c."""
    origin, vectors = np.asarray(origin, dtype=float), np.asarray(vectors, dtype=float)
    corner = lambda i, j, k: origin + i * vectors[0] + j * vectors[1] + k * vectors[2]  # noqa: E731
    edges = []
    for a in (0, 1):
        for b in (0, 1):
            edges += [(corner(0, a, b), corner(1, a, b)), (corner(a, 0, b), corner(a, 1, b)), (corner(a, b, 0), corner(a, b, 1))]
    return [(start.tolist(), end.tolist()) for start, end in edges]


def mvs_json(cif_text, cells=()):
    """MolViewSpec (JSON) showing the structure as ball and stick, one coloured component per element.

    The mmCIF text is embedded as a data URL, so no file or server is needed.
    cells: optional (origin, vectors, color) triples, each drawn as the 12 edges of that cell.
    """
    import base64
    import json

    url = "data:text/plain;base64," + base64.b64encode(cif_text.encode()).decode()
    components = [
        {
            "kind": "component", "params": {"selector": {"type_symbol": symbol}},
            "children": [{
                "kind": "representation", "params": {"type": "ball_and_stick"},
                "children": [{"kind": "color", "params": {"color": color}}],
            }],
        }
        for symbol, color in ELEMENT_COLORS.items()
    ]
    structure = {"kind": "structure", "params": {"type": "model"}, "children": components}
    parse = {"kind": "parse", "params": {"format": "mmcif"}, "children": [structure]}
    canvas = {"kind": "canvas", "params": {"background_color": BACKGROUND}}
    outlines = [
        {
            "kind": "primitives", "params": {"color": color},
            "children": [
                {"kind": "primitive", "params": {"kind": "tube", "start": start, "end": end, "color": color, "radius": 0.1}}
                for start, end in cell_edges(origin, vectors)
            ],
        }
        for origin, vectors, color in cells
    ]
    root = {"kind": "root", "children": [canvas, *outlines, {"kind": "download", "params": {"url": url}, "children": [parse]}]}
    return json.dumps({"metadata": {"version": "1"}, "root": root})
