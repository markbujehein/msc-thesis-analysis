import json, os, subprocess, tempfile, unittest
HOOK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.claude/hooks/check_deps.py'))

def project(manifest, baseline=None):
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, '.claude'))
    if manifest is not None: open(os.path.join(root, 'pixi.toml'), 'w').write(manifest)
    if baseline is not None: open(os.path.join(root, '.claude/deps.baseline'), 'w').write(baseline)
    return root

def run(root, active=False):
    p = subprocess.run(['python3', HOOK], input=json.dumps({'stop_hook_active': active}), capture_output=True, text=True,
                       env={**os.environ, 'CLAUDE_PROJECT_DIR': root})
    return ('block', json.loads(p.stdout)['reason']) if '"block"' in p.stdout else ('allow', '')

M = '[dependencies]\nnumpy = "*"\n[pypi-dependencies]\nmarimo = "*"\n[feature.a.dependencies]\naltair = "*"\n'
B = 'conda:altair\nconda:numpy\npypi:marimo\n'

class CheckDepsTests(unittest.TestCase):
    def test_all_present_allows(self):
        self.assertEqual(run(project(M, B))[0], 'allow')
    def test_removed_package_blocks_and_is_named(self):
        verdict, reason = run(project(M.replace('altair = "*"\n', ''), B))
        self.assertEqual(verdict, 'block'); self.assertIn('conda:altair', reason)
    def test_new_package_allows(self):
        self.assertEqual(run(project(M + 'scipy = "*"\n', B))[0], 'allow')
    def test_moved_between_features_allows(self):
        self.assertEqual(run(project('[dependencies]\nnumpy = "*"\naltair = "*"\n[pypi-dependencies]\nmarimo = "*"\n', B))[0], 'allow')
    def test_changed_source_blocks(self):
        self.assertEqual(run(project(M.replace('[dependencies]\nnumpy = "*"\n', '[dependencies]\n').replace('marimo = "*"', 'marimo = "*"\nnumpy = "*"'), B))[0], 'block')
    def test_extras_and_name_spelling_are_normalised(self):
        m = '[dependencies]\nnumpy = "*"\n[feature.a.dependencies]\nVL_Convert-python = "*"\n[pypi-dependencies]\nmarimo = { version = "*", extras = ["mcp"] }\n'
        self.assertEqual(run(project(m, 'conda:numpy\nconda:vl-convert-python\npypi:marimo\n'))[0], 'allow')
    def test_no_baseline_or_manifest_allows(self):
        self.assertEqual(run(project(M))[0], 'allow'); self.assertEqual(run(project(None, B))[0], 'allow')
    def test_active_stop_hook_does_not_loop(self):
        self.assertEqual(run(project(M.replace('altair = "*"\n', ''), B), active=True)[0], 'allow')

if __name__ == '__main__':
    unittest.main()
