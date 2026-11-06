"""Is this structure thymol (2-isopropyl-5-methylphenol)? usage: check_thymol.py file.cif|file.pdb ...
Reads the 25-atom molecule, builds bonds from distances, finds the aromatic ring and prints which ring
positions carry OH / isopropyl / methyl, numbered from the OH carbon. Thymol = OH at 1, iPr at 2, Me at 5."""
import sys, re, numpy as np

def read(fn):
    t = open(fn).read().split('\n')
    if fn.endswith('.pdb'):
        at = [l for l in t if l.startswith(('ATOM', 'HETATM'))]
        el = [re.sub(r'[^A-Z]', '', l[12:16].strip()[:1].upper()) for l in at]   # element = first letter of atom name
        return el, np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in at])
    val = lambda k: float(re.search(r'^_cell_' + k + r'\s+([\d.]+)', '\n'.join(t), re.M).group(1))
    a, b, c, al, be, ga = (val(k) for k in ['length_a', 'length_b', 'length_c', 'angle_alpha', 'angle_beta', 'angle_gamma'])
    ca, cb, cg = np.cos(np.radians([al, be, ga])); sg = np.sin(np.radians(ga)); v = np.sqrt(1 - ca**2 - cb**2 - cg**2 + 2*ca*cb*cg)
    M = np.array([[a, b*cg, c*cb], [0, b*sg, c*(ca - cb*cg)/sg], [0, 0, c*v/sg]])
    i = t.index('_atom_site_fract_z')
    at = [l.split() for l in t[i+1:] if len(l.split()) == 5 and l.split()[1] in ('C', 'H', 'O')]
    F = np.array([[float(y) for y in x[2:]] for x in at]); xyz = np.zeros((len(at), 3)); xyz[0] = M @ F[0]; seen = {0}; q = [0]
    while q:                                   # make the molecule whole across cell boundaries
        k = q.pop()
        for j in range(len(at)):
            d = F[j] - F[k]; d -= np.round(d)
            if j not in seen and np.linalg.norm(M @ d) < 1.7: xyz[j] = xyz[k] + M @ d; seen.add(j); q.append(j)
    return [x[1] for x in at], xyz

def pattern(el, xyz):
    n = len(el); D = np.linalg.norm(xyz[:, None] - xyz[None], axis=2)
    adj = {k: [j for j in range(n) if j != k and D[k, j] < (1.2 if 'H' in (el[j], el[k]) else 1.7)] for k in range(n)}
    heavy_nb = lambda k: [j for j in adj[k] if el[j] != 'H']
    arom = [k for k in range(n) if el[k] == 'C' and len(adj[k]) == 3 and sum(el[j] == 'C' and len(adj[j]) == 3 for j in adj[k]) >= 2]
    ro = [k for k in arom if any(el[j] == 'O' for j in adj[k])]
    if len(ro) != 1: return None
    order = [ro[0]]
    while len(order) < 6:
        nxt = [j for j in adj[order[-1]] if j in arom and j not in order]
        if not nxt: return None
        order.append(nxt[0])
    out = []
    for p, k in enumerate(order, 1):
        s = [j for j in heavy_nb(k) if j not in arom]
        if s: out.append((p, 'OH' if el[s[0]] == 'O' else ('iPr' if len(heavy_nb(s[0])) == 3 else 'Me')))
    return out

THYMOL = [(1, 'OH'), (2, 'iPr'), (5, 'Me')]
def mirror(pat):  # same ring numbered in the other direction, still starting at the OH carbon
    return sorted(((1 - p) % 6 + 1, name) for p, name in pat)

for fn in sys.argv[1:]:
    el, xyz = read(fn); pat = pattern(el, xyz)
    formula = sorted(el) == sorted("C" * 10 + "H" * 14 + "O")
    ok = formula and pat is not None and (pat == THYMOL or mirror(pat) == THYMOL)
    print(f'{fn}: atoms={len(el)} formula_ok={formula} ring_positions={pat} -> {"THYMOL" if ok else "NOT thymol / unclear"}')
