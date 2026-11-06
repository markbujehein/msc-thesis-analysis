#!/usr/bin/env bash
# Stop hook: block ending the turn if scientific files changed but LOG.md (or refs.bib for new data files) did not.
cd "$(dirname "$0")/../.." || exit 0
in=$(cat); echo "$in" | grep -q '"stop_hook_active": *true' && exit 0   # no loops
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
ch=$(git status --porcelain -uall . | grep -vE ' \.claude/|LOG\.md$|refs\.bib$' | cut -c4-)
[ -z "$ch" ] && exit 0
msg=""
git status --porcelain . | grep -q 'LOG\.md$' || msg="LOG.md has no new entry for: $(echo $ch | tr '\n' ' '). Use the log-entry skill. "
if echo "$ch" | grep -qiE '\.(cif|pdb|pdf)$' && ! git status --porcelain . | grep -q 'refs\.bib$' \
   && ! git diff HEAD -U0 -- LOG.md | grep -qi '^+.*no reference:'; then
  msg="${msg}New/changed data files but refs.bib is unchanged: use the add-reference skill, or add a line 'No reference: <why no peer-reviewed source applies>' to the new LOG.md entry."
fi
[ -z "$msg" ] && exit 0
printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
