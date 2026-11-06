"""Run: uv run --with numpy python thymol_cif/tests/test_make_pdb.py  (from anywhere)"""
import subprocess, sys, tempfile, itertools, os, numpy as np
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build(cif, nx=1, ny=1, nz=1):
    out = tempfile.mktemp(suffix='.pdb')
    subprocess.run([sys.executable, '-I', f'{D}/scripts/make_pdb.py', f'{D}/{cif}', out, str(nx), str(ny), str(nz)], check=True, capture_output=True)
    L = open(out).read().split('\n'); os.remove(out); return L

def check(L, n_mol):
    cr = L[0]; cell = [float(cr[i:i+w]) for i, w in zip([6, 15, 24, 33, 40, 47], [9, 9, 9, 7, 7, 7])]
    a, b, c, al, be, ga = cell; ca, cb, cg = np.cos(np.radians([al, be, ga])); sg = np.sin(np.radians(ga))
    M = np.array([[a, b*cg, c*cb], [0, b*sg, c*(ca-cb*cg)/sg], [0, 0, c*np.sqrt(1-ca**2-cb**2-cg**2+2*ca*cb*cg)/sg]])
    at = [(l[76:78].strip(), int(l[22:26]), [float(l[30:38]), float(l[38:46]), float(l[46:54])]) for l in L if l.startswith('ATOM')]
    E = [x[0] for x in at]; R = np.array([x[1] for x in at]); X = np.array([x[2] for x in at])
    assert len(at) == 25 * n_mol and len(set(R)) == n_mol, (len(at), len(set(R)))
    assert sorted(set(np.bincount(R)[1:])) == [25]
    for r in set(R):                                  # molecule is whole: 25 bonds
        s = X[R == r]; e = np.array(E)[R == r]; d = np.linalg.norm(s[:, None] - s[None], axis=2); np.fill_diagonal(d, 99)
        cut = np.where((e[:, None] == 'H') | (e[None] == 'H'), 1.2, 1.7); assert (d < cut).sum() // 2 == 25, r
    f = (X[:, None] - X[None]) @ np.linalg.inv(M).T; f -= np.round(f); D_ = np.linalg.norm(f @ M.T, axis=2)
    inter = np.where(R[:, None] == R[None], 99, D_); heavy = np.array(E) != 'H'
    assert np.where(heavy[:, None] & heavy[None], inter, 99).min() > 2.4   # no overlapping molecules (also across periodic images)
    mass = {'C': 12.011, 'H': 1.008, 'O': 15.999}
    rho = sum(mass[e] for e in E) / (abs(np.linalg.det(M)) * 0.6022); assert 0.9 < rho < 1.2, rho

check(build('4101955.cif'), 18)            # R-3, Z=18, the best-match structure
check(build('4101955.cif', 2, 2, 1), 72)   # supercell
check(build('4101957.cif'), 4)             # P2_1/c, Z=4: other space group, no hard-coded count
print('ok')
