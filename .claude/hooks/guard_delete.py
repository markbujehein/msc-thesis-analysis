#!/usr/bin/env python3
"""PreToolUse(Bash) hook: commands that can delete or overwrite existing work need the user's approval.
shortcut: reads the command text only, so a deletion hidden inside a script file or an unusual tool is not caught; extend the checks if one slips through."""
import json, os, re, shlex, sys

REASON = ("Destructive command needs the user's approval. Before asking: list exactly what it would remove or overwrite "
          "(ls -la / git status), say what each item is and who made it, and only then run it. Never delete or overwrite "
          "anything you did not create in this session without the user's explicit request.")
WRAP = {'sudo', 'xargs', 'time', 'nice', 'do', 'then', 'exec', 'command'}
GIT_ALWAYS = {'clean', 'restore', 'rm', 'filter-branch', 'gc'}

def exists(path, cwd):
    p = os.path.expanduser(path)
    return not p.startswith('/dev/') and os.path.lexists(p if os.path.isabs(p) else os.path.join(cwd, p))

def danger(tokens, cwd):
    while tokens and (re.fullmatch(r'\w+=.*', tokens[0]) or tokens[0] in WRAP): tokens = tokens[1:]
    if not tokens: return False
    c, a = os.path.basename(tokens[0]), tokens[1:]
    opts = [x for x in a if x.startswith('-')]; args = [x for x in a if not x.startswith('-')]
    if any(re.search(r'shutil\.rmtree|os\.(remove|unlink|rmdir)|\.unlink\(', x) for x in a): return True
    if c in ('rm', 'rmdir', 'unlink', 'shred', 'truncate'): return True
    if c in ('bash', 'sh', 'zsh') and '-c' in a and a.index('-c') + 1 < len(a): return bad(a[a.index('-c') + 1], cwd)
    if c == 'find': return '-delete' in a or ('-exec' in a and any(os.path.basename(x) == 'rm' for x in a))
    if c == 'sed': return any(re.fullmatch(r'-[a-zA-Z]*i.*|--in-place.*', o) for o in opts)
    if c in ('cp', 'mv', 'install') and len(args) >= 2:
        dst, srcs = args[-1], args[:-1]
        if exists(dst, cwd) and not os.path.isdir(dst if os.path.isabs(dst) else os.path.join(cwd, dst)): return True
        return any(exists(os.path.join(dst, os.path.basename(s.rstrip('/'))), cwd) for s in srcs)
    if c == 'tee': return '-a' not in opts and any(exists(x, cwd) for x in args)
    if c == 'git' and args:
        sub, rest = args[0], args[1:]
        return (sub in GIT_ALWAYS or (sub == 'reset' and '--hard' in a) or (sub == 'checkout' and ('--' in a or '.' in rest))
                or (sub == 'branch' and '-D' in a) or (sub == 'stash' and rest[:1] in (['drop'], ['clear']))
                or (sub == 'push' and any(x in ('--force', '-f') or x.startswith('--force-') for x in a))
                or (sub == 'reflog' and rest[:1] == ['expire']))
    return False

def redirects(tokens, cwd):
    for i, t in enumerate(tokens):
        m = re.search(r'(?<![>&])\d*>(?![>&])(.*)', t)
        if m:
            target = m.group(1) or (tokens[i + 1] if i + 1 < len(tokens) else '')
            if target and exists(target, cwd): return True
    return False

def bad(cmd, cwd):
    cmd = re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\2[ \t]*(?:\n|$)", lambda m: m.group(0).split('\n')[0] + '\n', cmd, flags=re.S)
    for seg in re.split(r'&&|\|\||[;|\n]', cmd):
        try: tokens = shlex.split(seg)
        except ValueError: return True            # cannot parse: ask
        if tokens and (danger(tokens, cwd) or redirects(tokens, cwd)): return True
    return False

if __name__ == '__main__':
    d = json.load(sys.stdin)
    if bad(d.get('tool_input', {}).get('command', ''), d.get('cwd') or os.getcwd()):
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'ask', 'permissionDecisionReason': REASON}}))
