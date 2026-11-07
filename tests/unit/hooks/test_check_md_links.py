import json, os, subprocess, tempfile, unittest
HOOK = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')), '.claude/hooks/check_md_links.py')
ROOT = tempfile.mkdtemp()                                   # stands in for the repo root
os.makedirs(os.path.join(ROOT, 'docs/specs'))
os.makedirs(os.path.join(ROOT, 'docs/figures'))
open(os.path.join(ROOT, 'docs/figures/p.svg'), 'w').close()
open(os.path.join(ROOT, 'docs/specs/a.md'), 'w').close()
SPEC_URL = 'file://' + ROOT + '/docs/specs/a.md'

def run(reply_blocks, active=False, prior_assistant=None):
    lines = []
    if prior_assistant: lines.append({'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': prior_assistant}]}})
    lines.append({'type': 'user', 'message': {'role': 'user', 'content': 'hi'}})
    for t in reply_blocks:
        lines.append({'type': 'assistant', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': t}]}})
    fd, path = tempfile.mkstemp(suffix='.jsonl'); os.close(fd)
    with open(path, 'w') as f: f.write('\n'.join(json.dumps(l) for l in lines))
    p = subprocess.run(['python3', HOOK], input=json.dumps({'transcript_path': path, 'stop_hook_active': active, 'cwd': ROOT}), capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != 'CLAUDE_PROJECT_DIR'})
    os.remove(path)
    return 'block' if '"block"' in p.stdout else 'allow'

class MdLinkTests(unittest.TestCase):
    def test_relative_path_blocks(self):
        for t in ('Spec is at `docs/specs/a.md`.', 'See docs/superpowers/plans/x.md', 'Read [the spec](docs/specs/a.md).', 'see ./docs/specs/a.md'):
            self.assertEqual(run([t]), 'block', t)
    def test_absolute_path_without_file_scheme_blocks(self):
        self.assertEqual(run([ROOT + '/docs/specs/a.md']), 'block')
    def test_absolute_file_url_to_an_existing_file_in_the_repo_is_allowed(self):
        self.assertEqual(run(['Spec: ' + SPEC_URL]), 'allow')
        self.assertEqual(run(['[spec](' + SPEC_URL + ')']), 'allow')
    def test_file_url_to_a_missing_file_blocks(self):
        self.assertEqual(run(['file://' + ROOT + '/docs/specs/missing.md']), 'block')
    def test_file_url_outside_the_repo_blocks(self):
        for p in ('/tmp/scratch/specs/a.md', '/tmp/claude-1000/x/scratchpad/plans/b.md'):
            self.assertEqual(run(['file://' + p]), 'block', p)
    def test_one_bad_link_among_good_ones_blocks(self):
        self.assertEqual(run([SPEC_URL + ' and docs/specs/b.md']), 'block')
    def test_ordinary_md_mentions_are_allowed(self):
        self.assertEqual(run(['I appended to LOG.md and read CLAUDE.md and README.md.']), 'allow')
    def test_reply_without_paths_is_allowed(self):
        self.assertEqual(run(['Done. Tests pass.']), 'allow')
    def test_only_the_current_turn_counts(self):
        self.assertEqual(run(['Done.'], prior_assistant='old: docs/specs/a.md'), 'allow')
    def test_text_across_several_blocks_of_the_turn_counts(self):
        self.assertEqual(run(['Working.', 'Spec at docs/specs/a.md']), 'block')
    def test_no_loop_when_stop_hook_is_active(self):
        self.assertEqual(run(['docs/specs/a.md'], active=True), 'allow')
    def test_missing_transcript_is_allowed(self):
        p = subprocess.run(['python3', HOOK], input='{}', capture_output=True, text=True)
        self.assertNotIn('block', p.stdout)

class FigureLinkTests(unittest.TestCase):
    FIG_URL = 'file://' + ROOT + '/docs/figures/p.svg'
    def test_relative_figure_paths_block(self):
        for t in ('`docs/figures/pipeline.svg`', 'see .local/pipe.png', '[d](docs/figures/p.svg)', 'docs/index.html', 'docs/x.pdf'):
            self.assertEqual(run([t]), 'block', t)
    def test_absolute_file_url_to_an_existing_figure_is_allowed(self):
        self.assertEqual(run([self.FIG_URL]), 'allow')
    def test_figure_in_a_temp_dir_blocks(self):
        self.assertEqual(run(['file:///tmp/claude-1000/x/banner.png']), 'block')
    def test_web_urls_are_ignored(self):
        self.assertEqual(run(['https://docs.mantidproject.org/nightly/algorithms/LoadVesuvio-v1.html']), 'allow')
    def test_bare_file_names_are_allowed(self):
        self.assertEqual(run(['banner.svg and pipeline.png']), 'allow')

if __name__ == '__main__': unittest.main()
