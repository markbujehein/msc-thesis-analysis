#!/usr/bin/env python3
"""Stop hook: block if a package listed in .claude/deps.baseline is no longer declared in pixi.toml.
Key = source:name (conda or pypi), so moving a package between features is fine but dropping or re-sourcing it is not.
shortcut: the baseline is a plain file the agent could edit; only the user should remove lines. Upgrade: protect it with a PreToolUse hook."""
import json, os, re, sys, tomllib

root = os.environ.get('CLAUDE_PROJECT_DIR') or ''
if not (os.path.exists(os.path.join(root, '.git')) or os.path.exists(os.path.join(root, 'pixi.toml'))):
    root = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')   # stale CLAUDE_PROJECT_DIR: use the script's own repo
if json.loads(sys.stdin.read() or '{}').get('stop_hook_active'): sys.exit(0)   # no loops
manifest, baseline = (os.path.join(root, p) for p in ('pixi.toml', '.claude/deps.baseline'))
if not (os.path.exists(manifest) and os.path.exists(baseline)): sys.exit(0)

def declared(d):
    name = lambda n: re.sub(r'[-_.]+', '-', n).lower()
    out = {f'{src}:{name(n)}' for k, src in (('dependencies', 'conda'), ('pypi-dependencies', 'pypi')) for n in d.get(k, {})}
    for f in d.get('feature', {}).values(): out |= declared(f)
    return out

missing = sorted(set(open(baseline).read().split()) - declared(tomllib.load(open(manifest, 'rb'))))
if missing:
    print(json.dumps({'decision': 'block', 'reason': f"pixi.toml no longer declares: {', '.join(missing)}. Restore them. Only the user may remove lines from .claude/deps.baseline."}))
