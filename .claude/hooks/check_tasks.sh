#!/usr/bin/env bash
# Stop hook: block ending the turn if a project file is newer than docs/TASKS.md.
# Reads no file contents: only mtimes, so it costs no tokens when the tracker is current.
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" || exit 0
in=$(cat); echo "$in" | grep -q '"stop_hook_active": *true' && exit 0   # no loops
T=docs/TASKS.md
[ -f "$T" ] && git rev-parse --git-dir >/dev/null 2>&1 || exit 0
new=$(git ls-files -co --exclude-standard | grep -vE '^(\.claude/|md/output/|data/zeppelin|LOG\.md$|refs\.bib$|docs/TASKS\.md$)' \
      | while IFS= read -r f; do [ "$f" -nt "$T" ] && echo "$f"; done)
[ -z "$new" ] && exit 0
msg="docs/TASKS.md is older than $(printf '%s\n' "$new" | wc -l) changed file(s), e.g. $(printf '%s\n' "$new" | head -3 | tr '\n' ' '). Update it: list open items with grep -n '^- \[ \]' docs/TASKS.md, tick what is done (say how it was checked), add new items. Do not read other files for this."
printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$msg" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
