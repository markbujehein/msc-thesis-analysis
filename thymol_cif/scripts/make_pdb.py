"""CIF (R-3, 25-atom asymmetric unit) -> PDB with whole molecules. usage: make_pdb.py in.cif out.pdb nx ny nz"""
import sys, re, itertools, numpy as np
cif, out, nx, ny, nz = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:6])
t = open(cif).read().split('\n')
val = lambda k: float(re.search(r'^_cell_' + k + r'\s+([\d.]+)', '\n'.join(t), re.M).group(1))
a, b, c, al, be, ga = (val(k) for k in ['length_a', 'length_b', 'length_c', 'angle_alpha', 'angle_beta', 'angle_gamma'])
ca, cb, cg = np.cos(np.radians([al, be, ga])); sg = np.sin(np.radians(ga))
v = np.sqrt(1 - ca**2 - cb**2 - cg**2 + 2*ca*cb*cg)
M = np.array([[a, b*cg, c*cb], [0, b*sg, c*(ca - cb*cg)/sg], [0, 0, c*v/sg]])  # frac -> cart
# symmetry ops: either CIF header name; each op is checked before it reaches eval
hdr = next((h for h in ('_symmetry_equiv_pos_as_xyz', '_space_group_symop_operation_xyz') if h in t), None)
if hdr is None: sys.exit('no symmetry operations found in CIF')
ops = []
for l in t[t.index(hdr) + 1:]:
    if not l.strip() or l.startswith(('loop_', '_')): break
    m = re.match(r"^(?:\d+\s+)?['\"]?([^'\"]+)['\"]?$", l.strip())
    expr = m.group(1).replace(' ', '').lower()
    if not re.fullmatch(r'[xyz0-9+\-/.,]+', expr) or expr.count(',') != 2: sys.exit(f'bad symmetry operation: {expr!r}')
    ops.append(compile('(' + expr + ')', '', 'eval'))
# atom loop: columns are found by header name, "(esd)" is dropped from numbers
i = t.index('_atom_site_fract_x'); j = i
while t[j - 1].startswith('_'): j -= 1
cols = []
while t[j].startswith('_'): cols.append(t[j]); j += 1
rows = []
while j < len(t) and t[j].strip() and not t[j].startswith(('loop_', '_', '#')): rows.append(t[j].split()); j += 1
at = [r for r in rows if len(r) == len(cols)]
num = lambda x: float(re.sub(r'\(.*\)', '', x))
ix = [cols.index('_atom_site_fract_' + k) for k in 'xyz']
sym = cols.index('_atom_site_type_symbol') if '_atom_site_type_symbol' in cols else None
n_at = len(at)
el = [x[sym] if sym is not None else re.match('[A-Z][a-z]?', x[0]).group(0) for x in at]; F = np.array([[num(x[k]) for k in ix] for x in at])
# whole molecule in cartesian (BFS with minimum image)
cart = np.zeros((n_at, 3)); cart[0] = M @ F[0]; seen = {0}; q = [0]
while q:
    k = q.pop()
    for j in range(n_at):
        if j in seen: continue
        d = F[j] - F[k]; d -= np.round(d)
        if np.linalg.norm(M @ d) < 1.7: cart[j] = cart[k] + M @ d; seen.add(j); q.append(j)
assert len(seen) == n_at, 'asymmetric unit is not one connected molecule'
f0 = cart @ np.linalg.inv(M).T
mols = []
for op in ops:
    G = np.array([eval(op, {}, dict(x=p[0], y=p[1], z=p[2])) for p in f0])
    G -= np.floor(G.mean(0))          # centroid into the cell, molecule stays whole
    mols.append(G)
# unique molecules: same molecule if every atom of one sits on an atom of the other (same element) modulo lattice
def same(A, B):
    for fa, ea in zip(A, el):
        d = fa - B; d -= np.round(d)
        if not (np.linalg.norm(d @ M.T, axis=1) + 99 * (np.array(el) != ea) < 0.2).any(): return False
    return True
uniq = []
for m_ in mols:
    if not any(same(m_, u) for u in uniq): uniq.append(m_)
mols = uniq
Z = int(re.search(r'^_cell_formula_units_Z\s+(\d+)', '\n'.join(t), re.M).group(1))
assert len(mols) == Z, f'{len(mols)} unique molecules found, CIF says Z={Z}'
names, cnt = [], {}
for e in el: cnt[e] = cnt.get(e, 0) + 1; names.append(f'{e}{cnt[e]}')
L = [f'CRYST1{a*nx:9.3f}{b*ny:9.3f}{c*nz:9.3f}{al:7.2f}{be:7.2f}{ga:7.2f} P 1           1']
n = r = 0
for ix, iy, iz in itertools.product(range(nx), range(ny), range(nz)):
    for m in mols:
        r += 1
        for nm, e, f in zip(names, el, m + [ix, iy, iz]):
            n += 1; x, y, z = M @ f
            L.append(f'ATOM  {n:5d} {nm:<4s} THY A{r:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {e:>2s}')
L.append('END'); open(out, 'w').write('\n'.join(L) + '\n')
print(out, n, 'atoms', r, 'molecules')
