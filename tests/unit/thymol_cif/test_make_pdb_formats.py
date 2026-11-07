import os, subprocess, sys, tempfile, unittest
D = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'thymol_cif'))
RUN = [sys.executable, '-I', f'{D}/scripts/make_pdb.py']

def run(cif, timeout=60):
    out = os.path.join(tempfile.mkdtemp(), 'o.pdb')
    p = subprocess.run(RUN + [cif, out, '1', '1', '1'], capture_output=True, text=True, timeout=timeout)
    return p, out

class FormatTests(unittest.TestCase):
    def test_experimental_style_cif_gives_same_pdb_as_cod_cif(self):
        a, fa = run(f'{D}/4101955.cif'); b, fb = run(f'{os.path.dirname(__file__)}/fixtures/experimental_style.cif')
        self.assertEqual(b.returncode, 0, b.stderr[-300:])
        with open(fa) as x, open(fb) as y: self.assertEqual(x.read(), y.read())

    def test_hostile_symmetry_line_is_rejected_quickly(self):
        src = open(f'{D}/4101955.cif').read().replace('2 -y,x-y,z', '2 9**9**9**9,x,z')
        bad = os.path.join(tempfile.mkdtemp(), 'bad.cif')
        with open(bad, 'w') as f: f.write(src)
        p, _ = run(bad, timeout=10)           # TimeoutExpired = test error (hang)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('symmetry', p.stderr.lower())

if __name__ == '__main__': unittest.main()
