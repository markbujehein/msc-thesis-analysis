import json, os, subprocess, tempfile, time, unittest
HOOK = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')), '.claude/hooks/check_tasks.sh')

def repo(files, tasks=True):
    """Temp git repo; every file in `files` is written, then TASKS.md is aged to 100 s ago (older than the files)."""
    root = tempfile.mkdtemp()
    subprocess.run(['git', 'init', '-q', root], check=True)
    for f in files:
        os.makedirs(os.path.dirname(os.path.join(root, f)) or root, exist_ok=True)
        open(os.path.join(root, f), 'w').close()
    if tasks:
        os.makedirs(os.path.join(root, 'docs'), exist_ok=True)
        t = os.path.join(root, 'docs/TASKS.md'); open(t, 'w').close()
        os.utime(t, (time.time() - 100, time.time() - 100))
    return root

def run(root, active=False):
    p = subprocess.run(['bash', HOOK], input=json.dumps({'stop_hook_active': active}), capture_output=True, text=True,
                       env={**os.environ, 'CLAUDE_PROJECT_DIR': root})
    return 'block' if '"block"' in p.stdout else 'allow'

class CheckTasksTests(unittest.TestCase):
    def test_code_newer_than_tasks_blocks(self):
        self.assertEqual(run(repo(['md/a.py'])), 'block')
    def test_tasks_newer_than_code_allows(self):
        root = repo(['md/a.py']); os.utime(os.path.join(root, 'docs/TASKS.md'))
        self.assertEqual(run(root), 'allow')
    def test_ignored_paths_allow(self):
        self.assertEqual(run(repo(['LOG.md', '.claude/x.sh', 'md/output/v.f32', 'refs.bib'])), 'allow')
    def test_reason_names_the_cheap_check_and_the_file(self):
        root = repo(['md/a.py'])
        p = subprocess.run(['bash', HOOK], input='{}', capture_output=True, text=True, env={**os.environ, 'CLAUDE_PROJECT_DIR': root})
        reason = json.loads(p.stdout)['reason']
        self.assertIn('md/a.py', reason); self.assertIn("grep -n '^- \\[ \\]'", reason)
    def test_active_stop_hook_does_not_loop(self):
        self.assertEqual(run(repo(['md/a.py']), active=True), 'allow')
    def test_no_tracker_allows(self):
        self.assertEqual(run(repo(['md/a.py'], tasks=False)), 'allow')

if __name__ == '__main__':
    unittest.main()
