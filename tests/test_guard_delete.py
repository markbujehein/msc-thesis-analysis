import json, os, subprocess, tempfile, unittest
HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.claude/hooks/guard_delete.py')

def decision(cmd, cwd):
    p = subprocess.run(['python3', HOOK], input=json.dumps({'tool_input': {'command': cmd}, 'cwd': cwd}), capture_output=True, text=True)
    return 'ask' if '"ask"' in p.stdout else 'allow'

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        for f in ('exists.txt', 'a.txt', 'LOG.md'):
            with open(os.path.join(self.d, f), 'w') as fh: fh.write('x')
        os.mkdir(os.path.join(self.d, 'sub'))
    def asks(self, *cmds):
        for c in cmds: self.assertEqual(decision(c, self.d), 'ask', c)
    def allows(self, *cmds):
        for c in cmds: self.assertEqual(decision(c, self.d), 'allow', c)

    def test_deletes_ask(self):
        self.asks('rm -rf sub', 'cd sub && rm a', 'echo hi | xargs rm', 'find . -name x -delete', 'sudo rm a.txt',
                  'bash -c "rm a.txt"', 'FOO=1 rm a.txt', 'rmdir sub', 'python3 -c "import shutil; shutil.rmtree(1)"')
    def test_git_destruction_asks(self):
        self.asks('git reset --hard HEAD~1', 'git clean -fd', 'git restore a.txt', 'git checkout -- a.txt', 'git rm a.txt',
                  'git branch -D x', 'git stash drop', 'git push --force', 'git reflog expire --expire=now --all', 'git gc --prune=now')
    def test_overwrite_of_existing_file_asks(self):
        self.asks('cp a.txt exists.txt', 'mv a.txt exists.txt', 'echo x > exists.txt', 'cat > LOG.md <<\'EOF\'\nhi\nEOF',
                  'sed -i s/a/b/ exists.txt', 'echo x | tee exists.txt', 'cp a.txt sub/../exists.txt', 'echo x>exists.txt')
    def test_writing_a_new_file_is_allowed(self):
        self.allows('cp a.txt new.txt', 'mv a.txt new.txt', 'echo x > new.txt', 'echo x >> exists.txt', 'cp a.txt sub/',
                    'echo x | tee -a exists.txt', 'ls > /dev/null', 'make 2>&1 | tail -3', 'echo x > /tmp/zz_new_file_guard_test')
    def test_harmless_commands_are_allowed(self):
        self.allows('ls -la', 'git status', 'git log --oneline', 'grep rm file.txt', 'git reset --soft HEAD~1', 'git commit -m "x"')
    def test_destructive_words_inside_quotes_or_heredocs_are_text(self):
        self.allows('git commit -m "avoid git reset --hard and rm -rf"', 'echo "rm -rf sub"',
                    "cat >> LOG.md <<'EOF'\nrm -rf sub\ngit reset --hard\nEOF")
    def test_unparseable_command_asks(self):
        self.asks('echo "unterminated')

if __name__ == '__main__': unittest.main()
