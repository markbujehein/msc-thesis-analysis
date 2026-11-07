#!/usr/bin/env python3
"""Stop hook: a reply that names a spec/plan .md file must link it as an absolute file:// URL
to an existing file inside the repo. Relative paths and temp-dir files are unclickable or unreachable for the user."""
import json, os, re, sys

try:
    data = json.load(sys.stdin)
    if data.get('stop_hook_active'): sys.exit(0)           # no loops
    lines = [json.loads(l) for l in open(data['transcript_path']) if l.strip()]
except Exception:
    sys.exit(0)
root = os.path.realpath(os.environ.get('CLAUDE_PROJECT_DIR') or data.get('cwd') or '.')

text = []
for e in reversed(lines):                                   # text of the current turn only
    m = e.get('message') or {}
    if e.get('type') == 'user' and not (isinstance(m.get('content'), list) and all(b.get('type') == 'tool_result' for b in m['content'])):
        break
    if e.get('type') == 'assistant':
        text += [b.get('text', '') for b in m.get('content', []) if b.get('type') == 'text']
text = '\n'.join(text)

bad = []
for tok in re.findall(r'(?:file://)?[\w./~-]*(?:docs|specs|plans)/[\w./-]*\.md\b', text):
    path = tok[len('file://'):] if tok.startswith('file:///') else None
    if not (path and os.path.realpath(path).startswith(root + os.sep) and os.path.isfile(path)): bad.append(tok)
if bad:
    print(json.dumps({'decision': 'block', 'reason':
        'Spec/plan files must be linked as an absolute file:// URL to an existing file inside the repo (%s/...), '
        'never a relative path or a temp dir. Fix: %s' % (root, ', '.join(sorted(set(bad))))}))
