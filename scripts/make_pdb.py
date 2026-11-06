"""CIF (R-3, 25-atom asymmetric unit) -> PDB with whole molecules. usage: make_pdb.py in.cif out.pdb nx ny nz"""
import sys, re, itertools, numpy as np
cif, out, nx, ny, nz = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:6])
t = open(cif).read().split('\n')
val = lambda k: float(re.search(r'^_cell_' + k + r'\s+([\d.]+)', '\n'.join(t), re.M).group(1))
a, b, c, al, be, ga = (val(k) for k in ['length_a', 'length_b', 'length_c', 'angle_alpha', 'angle_beta', 'angle_gamma'])
ca, cb, cg = np.cos(np.radians([al, be, ga])); sg = np.sin(np.radians(ga))
v = np.sqrt(1 - ca**2 - cb**2 - cg**2 + 2*ca*cb*cg)
M = np.array([[a, b*cg, c*cb], [0, b*sg, c*(ca - cb*cg)/sg], [0, 0, c*v/sg]])  # frac -> cart
# symmetry ops (only characters allowed in eval are checked)
ops = []
for l in t[t.index('_symmetry_equiv_pos_as_xyz') + 1:]:
    if not l.strip() or l.startswith(('loop_', '_')): break
    expr = l.split(None, 1)[1].strip()
    assert re.fullmatch(r'[xyz0-9+\-*/.,]+', expr), expr
    ops.append(compile('(' + expr + ')', '', 'eval'))
i = t.index('_atom_site_fract_z')
at = [l.split() for l in t[i+1:] if len(l.split()) == 5 and l.split()[1] in ('C', 'H', 'O')]
assert len(at) == 25
el = [x[1] for x in at]; F = np.array([[float(y) for y in x[2:]] for x in at])
# whole molecule in cartesian (BFS with minimum image)
cart = np.zeros((25, 3)); cart[0] = M @ F[0]; seen = {0}; q = [0]
while q:
    k = q.pop()
    for j in range(25):
        if j in seen: continue
        d = F[j] - F[k]; d -= np.round(d)
        if np.linalg.norm(M @ d) < 1.7: cart[j] = cart[k] + M @ d; seen.add(j); q.append(j)
assert len(seen) == 25, 'asymmetric unit is not one connected molecule'
f0 = cart @ np.linalg.inv(M).T
mols = []
for op in ops:
    G = np.array([eval(op, {}, dict(x=p[0], y=p[1], z=p[2])) for p in f0])
    G -= np.floor(G.mean(0))          # centroid into the cell, molecule stays whole
    mols.append(G)
# unique molecules only (centering ops generate the full set; R-3 gives 18)
cen = np.array([m.mean(0) for m in mols]); cen -= np.floor(cen)
keep = []
for k in range(len(mols)):
    if not any(np.linalg.norm(((cen[k]-cen[j]+.5) % 1 - .5) @ M.T) < 0.5 for j in keep): keep.append(k)
mols = [mols[k] for k in keep]
assert len(mols) == 18, len(mols)
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
