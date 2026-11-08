import numpy as np

from molview import cell_parameters, chain_id, mmcif_text

CELL = np.array([[10.0, 0, 0], [-5.0, 5.0 * np.sqrt(3), 0], [0, 0, 8.0]])  # hexagonal: 10, 10, 8, 90, 90, 120


def test_cell_parameters_of_a_hexagonal_cell():
    a, b, c, alpha, beta, gamma = cell_parameters(CELL)
    assert np.allclose([a, b, c, alpha, beta, gamma], [10, 10, 8, 90, 90, 120])


def test_mmcif_has_cell_space_group_and_one_row_per_atom():
    symbols = ["O", "H", "H", "C"]
    positions = np.array([[0.0, 0, 0], [0.96, 0, 0], [-0.24, 0.93, 0], [3.0, 3.0, 3.0]])
    text = mmcif_text(symbols, positions, CELL, molecule=[0, 0, 0, 1])
    assert "_cell.length_a 10.000" in text and "_cell.angle_gamma 120.000" in text
    assert "_symmetry.space_group_name_H-M 'P 1'" in text
    rows = [line.split() for line in text.splitlines() if line.startswith("HETATM")]
    assert len(rows) == 4
    assert [r[2] for r in rows] == ["O", "H", "H", "C"]  # type_symbol column
    assert [r[7] for r in rows] == ["1", "1", "1", "2"]  # label_seq_id: one residue per molecule, from 1
    assert np.allclose([float(x) for x in rows[1][8:11]], [0.96, 0, 0])  # Cartn_x, y, z


def test_chain_ids_run_a_to_z_then_aa():
    assert [chain_id(i) for i in (0, 1, 25, 26, 27, 51, 52, 701, 702)] == ["A", "B", "Z", "AA", "AB", "AZ", "BA", "ZZ", "AAA"]


def test_each_molecule_is_its_own_chain():
    text = mmcif_text(["C", "C", "C"], np.zeros((3, 3)), CELL, molecule=[0, 0, 1])
    rows = [line.split() for line in text.splitlines() if line.startswith("HETATM")]
    assert [r[5] for r in rows] == ["A", "A", "B"]  # label_asym_id: Mol* colours carbon per chain


def test_mvs_describes_ball_and_stick_per_element_and_embeds_the_structure():
    import base64
    import json

    from molview import ELEMENT_COLORS, mvs_json

    text = "data_x\n_cell.length_a 1.000\n"
    spec = json.loads(mvs_json(text))
    nodes = []

    def walk(node):
        nodes.append(node)
        for child in node.get("children", []):
            walk(child)

    walk(spec["root"])
    download = next(n for n in nodes if n["kind"] == "download")
    prefix = "data:text/plain;base64,"
    assert download["params"]["url"].startswith(prefix)
    assert base64.b64decode(download["params"]["url"][len(prefix):]).decode() == text  # the structure travels inside
    assert next(n for n in nodes if n["kind"] == "parse")["params"]["format"] == "mmcif"
    reps = [n["params"]["type"] for n in nodes if n["kind"] == "representation"]
    assert reps == ["ball_and_stick"] * len(ELEMENT_COLORS) and set(ELEMENT_COLORS) == {"C", "H", "O"}  # no cartoon
    selected = [n["params"]["selector"]["type_symbol"] for n in nodes if n["kind"] == "component"]
    assert selected == list(ELEMENT_COLORS)
    colors = [n["params"]["color"] for n in nodes if n["kind"] == "color"]
    assert colors == list(ELEMENT_COLORS.values())
    assert not any(n["kind"] == "primitives" for n in nodes)  # nothing drawn besides the atoms and bonds


def test_mvs_sets_a_mid_grey_canvas():
    import json

    from molview import mvs_json

    root = json.loads(mvs_json("data_x\n"))["root"]
    canvas = [n for n in root["children"] if n["kind"] == "canvas"]
    assert [n["params"]["background_color"] for n in canvas] == ["#808080"]


def test_cell_edges_are_the_twelve_edges_of_the_cell_at_its_origin():
    from molview import cell_edges

    origin = np.array([1.0, 2.0, 3.0])
    edges = np.array(cell_edges(origin, CELL))
    assert edges.shape == (12, 2, 3)
    lengths = np.sort(np.linalg.norm(edges[:, 1] - edges[:, 0], axis=1))
    assert np.allclose(lengths, np.sort(np.repeat(np.linalg.norm(CELL, axis=1), 4)))
    corners = np.unique(edges.reshape(-1, 3).round(6), axis=0)
    assert len(corners) == 8 and np.allclose(corners.min(axis=0)[2], 3.0)  # eight corners, bottom face at the origin height


def test_mvs_draws_each_requested_cell_as_twelve_coloured_tubes():
    import json

    from molview import mvs_json

    cells = [(np.zeros(3), CELL, "#ffa500"), (np.zeros(3), 2 * CELL, "#00ffff")]
    root = json.loads(mvs_json("data_x\n", cells=cells))["root"]
    groups = [n for n in root["children"] if n["kind"] == "primitives"]
    assert len(groups) == 2
    for group, color in zip(groups, ["#ffa500", "#00ffff"]):
        lines = group["children"]
        assert len(lines) == 12 and all(n["kind"] == "primitive" for n in lines)
        assert all(n["params"]["kind"] == "tube" and n["params"]["color"] == color for n in lines)
        assert all(len(n["params"]["start"]) == 3 and "radius" in n["params"] for n in lines)
