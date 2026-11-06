import importlib.util, os, tempfile, unittest
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location('check_thymol', f'{D}/scripts/check_thymol.py')
ct = importlib.util.module_from_spec(spec); spec.loader.exec_module(ct)

class PatternTests(unittest.TestCase):
    def test_thymol_pattern(self):
        self.assertTrue(ct.is_thymol_pattern([(1, 'OH'), (2, 'iPr'), (5, 'Me')]))
    def test_same_ring_numbered_the_other_way_is_thymol(self):
        self.assertTrue(ct.is_thymol_pattern([(1, 'OH'), (3, 'Me'), (6, 'iPr')]))
    def test_carvacrol_is_not_thymol_in_either_direction(self):
        self.assertFalse(ct.is_thymol_pattern([(1, 'OH'), (2, 'Me'), (5, 'iPr')]))
        self.assertFalse(ct.is_thymol_pattern([(1, 'OH'), (3, 'iPr'), (6, 'Me')]))
    def test_missing_ring_is_not_thymol(self):
        self.assertFalse(ct.is_thymol_pattern(None))

def molecule():
    with open(f'{D}/../pdb/thymol_structure3_R-3_unitcell.pdb') as f:
        return [l for l in f if l.startswith('ATOM')][:25]

class FileTests(unittest.TestCase):
    def test_cod_cif_is_thymol(self):
        self.assertTrue(ct.classify(f'{D}/4101955.cif')[1])
    def test_atom_order_in_a_pdb_does_not_matter(self):
        L = molecule()
        for order in (L, L[::-1]):
            p = os.path.join(tempfile.mkdtemp(), 'm.pdb')
            with open(p, 'w') as f: f.write(''.join(order))
            self.assertTrue(ct.classify(p)[1], p)
    def test_not_thymol_when_a_methyl_is_missing(self):
        L = molecule()
        p = os.path.join(tempfile.mkdtemp(), 'm.pdb')
        with open(p, 'w') as f: f.write(''.join(l for l in L if l[12:16].strip() not in ('C10', 'H12', 'H13', 'H14')))
        self.assertFalse(ct.classify(p)[1])

if __name__ == '__main__': unittest.main()
