#!/usr/bin/env bash
# Stop hook: block ending the turn if scientific files changed since the last LOG.md commit
# but LOG.md did not (or refs.bib / a "No reference:" line for new data files).
# Baseline = last commit that touched LOG.md, so committing in the same turn cannot hide changes.
cd "$(dirname "$0")/../.." || exit 0
in=$(cat); echo "$in" | grep -q '"stop_hook_active": *true' && exit 0   # no loops
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
B=$(git log -1 --format=%H -- LOG.md 2>/dev/null)
[ -z "$B" ] && B=$(git hash-object -t tree /dev/null)
ch=$( { git diff --name-only "$B" -- . ; git ls-files -o --exclude-standard; } | sort -u \
      | grep -vE '^\.claude/|^LOG\.md$|^refs\.bib$|^\.gitignore$' )
[ -z "$ch" ] && exit 0
msg=""
git diff --quiet "$B" -- LOG.md && msg="LOG.md has no new entry for: $(printf '%s ' $ch). Use the log-entry skill. "
if printf '%s\n' "$ch" | grep -qiE '\.(cif|pdb|pdf)$' && git diff --quiet "$B" -- refs.bib \
   && ! git diff "$B" -U0 -- LOG.md | grep -qi '^+.*no reference:'; then
  msg="${msg}New/changed data files but refs.bib is unchanged: use the add-reference skill, or add a line 'No reference: <why no peer-reviewed source applies>' to the new LOG.md entry."
fi
[ -z "$msg" ] && exit 0
printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
