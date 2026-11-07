#!/usr/bin/env bash
# Stop hook: block ending the turn if scientific files changed since the last LOG.md commit
# but LOG.md did not (or refs.bib / a "No reference:" line for new data files).
# Baseline = last commit that touched LOG.md, so committing in the same turn cannot hide changes.
cd "$(dirname "$(readlink -f "$0")")/../.." || exit 0   # real script path: immune to a stale CLAUDE_PROJECT_DIR
in=$(cat); echo "$in" | grep -q '"stop_hook_active": *true' && exit 0   # no loops
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
B=$(git log -1 --format=%H -- LOG.md 2>/dev/null)
[ -z "$B" ] && B=$(git hash-object -t tree /dev/null)
ts=$(git log -1 --format=%ct "$B" 2>/dev/null || echo 0)   # untracked files only count if newer than the last LOG.md commit
ch=$( { git diff --name-only "$B" -- . ; git ls-files -o --exclude-standard | while IFS= read -r f; do [ "$(stat -c %Y "$f")" -gt "$ts" ] && echo "$f"; done; } | sort -u \
      | grep -vE '^\.claude/|^LOG\.md$|^refs\.bib$|^\.gitignore$' )
[ -z "$ch" ] && exit 0
msg=""
git diff --quiet "$B" -- LOG.md && msg="LOG.md has no new entry for: $(printf '%s' "$ch" | tr '\n' ' '). Use the log-entry skill. "
if printf '%s\n' "$ch" | grep -qiE '\.(cif|pdb|pdf)$' && git diff --quiet "$B" -- refs.bib; then
  new=$(git diff "$B" -U0 -- LOG.md | grep '^+')
  ok=0; printf '%s\n' "$new" | grep -qi 'no reference:' && ok=1
  # derived/extracted files: a "[ref: key]" tag in the new log text naming a key that exists in refs.bib
  for k in $(printf '%s\n' "$new" | grep -oiE '\[ref: *[^]]+\]' | sed -E 's/^\[ref: *//I;s/\]$//' | tr ',' ' '); do
    grep -qE "^@[A-Za-z]+\{$k," refs.bib && ok=1
  done
  [ $ok = 1 ] || msg="${msg}New/changed data files and no reference: add the source to refs.bib (add-reference skill), or tag the new LOG.md entry with '[ref: key]' for a key already in refs.bib (derived/extracted files), or add 'No reference: <why>'."
fi
[ -z "$msg" ] && exit 0
printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
