#!/usr/bin/env bash
# PreToolUse(Bash) hook: any command that can delete or overwrite work needs explicit user approval.
# shortcut: pattern match on the command text, so a deletion hidden inside a script file or an unusual tool is not caught; extend the patterns if one slips through.
cmd=$(python3 -c 'import json,sys;print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null)
pos='(^|[;&|]|\$\(|`|\bxargs +|\bsudo +|\bdo +|\bthen +)[[:space:]]*'
if printf '%s' "$cmd" | grep -qE "${pos}(rm|rmdir|unlink|shred|truncate)([[:space:]]|$)" \
 || printf '%s' "$cmd" | grep -qE 'find .*(-delete|-exec +rm)' \
 || printf '%s' "$cmd" | grep -qE 'git +(reset +--hard|clean|restore|checkout +(--|\.)|rm( |$)|branch +-D|stash +(drop|clear)|filter-branch|push .*(--force|-f( |$)))' \
 || printf '%s' "$cmd" | grep -qE 'shutil\.rmtree|os\.(remove|unlink|rmdir)|\.unlink\('; then
  reason="Destructive command needs the user's approval. Before asking: list exactly what it would remove or overwrite (ls -la / git status), say what each item is and who made it, and only then run it. Never delete anything you did not create in this session without the user's explicit request."
  python3 -c 'import json,sys;print(json.dumps({"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":sys.argv[1]}}))' "$reason"
fi
exit 0
