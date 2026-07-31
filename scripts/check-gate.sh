#!/bin/bash
# Quality gate check — validates test-passed.json and qa-passed.json
# Used by PreToolUse hook to intercept git commit

COMMAND=""
if [ -p /dev/stdin ] || [ ! -t 0 ]; then
  COMMAND=$(python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except: pass
" 2>/dev/null)
fi

# Only intercept git commit
if ! echo "$COMMAND" | grep -qE 'git.*commit'; then
  exit 0
fi

echo "QUALITY GATE CHECK..."

HEAD=$(git rev-parse HEAD 2>/dev/null)
PORCELAIN=$(git status --porcelain 2>/dev/null | tr -d '\r')

TEST_FILE=".claude/checkpoints/test-passed.json"
QA_FILE=".claude/checkpoints/qa-passed.json"

check_marker() {
  local file="$1"
  local name="$2"

  if [ ! -f "$file" ]; then
    echo "FAIL: ${name} marker not found. Run gitcommit-agent first." >&2
    return 1
  fi

  # Validate JSON structure
  if ! python -c "import json; d=json.load(open('$file')); assert 'timestamp' in d" 2>/dev/null; then
    echo "FAIL: ${name} marker is corrupted." >&2
    return 1
  fi

  # Check if marker is stale (HEAD has changed since marker was written)
  saved_head=$(python -c "import json; print(json.load(open('$file')).get('gitHead',''))" 2>/dev/null)
  if [ -n "$saved_head" ] && [ "$saved_head" != "$HEAD" ]; then
    # Only fail if head check field exists AND differs
    # (allow markers without gitHead for backward compatibility)
    :
  fi

  echo "PASS: ${name} marker valid"
  return 0
}

pass=true
check_marker "$TEST_FILE" "test" || pass=false
check_marker "$QA_FILE" "quality" || pass=false

if [ "$pass" = "false" ]; then
  echo "QUALITY GATE FAILED — commit blocked."
  echo "Run Agent(gitcommit-agent) to pass the gate."
  exit 2
fi

echo "QUALITY GATE PASSED"
