#!/usr/bin/env bash
# Structured opencode task runner with session-based retry loop.
# Tier 1 supervisor: no serve required.
#
# !! SERIAL USE ONLY !!
# Session ID is extracted from this invocation's --format json output stream.
# Running multiple instances concurrently risks misidentifying sessions and
# sending retries to the wrong task. For parallel dispatch use plain
# `opencode run` via ctx_batch_execute instead (no retry wrapper needed there).
#
# Usage:
#   oc_task.sh --model MODEL --prompt "PROMPT TEXT" [--retries N] [--session ID]
#
# The prompt MUST include a "RESULT:OK" or "RESULT:FAIL:<reason>" marker at the end.
# Use the structured template from the opencode-dispatch skill.
#
# Output: raw opencode output on success, exits 0.
#         Error summary on failure, exits 1.

set -euo pipefail

MODEL=""
PROMPT=""
MAX_RETRIES=3
SESSION_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --model)    MODEL="$2";       shift 2 ;;
    --prompt)   PROMPT="$2";      shift 2 ;;
    --retries)  MAX_RETRIES="$2"; shift 2 ;;
    --session)  SESSION_ID="$2";  shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$MODEL" ]]  && { echo "Error: --model required" >&2; exit 1; }
[[ -z "$PROMPT" ]] && { echo "Error: --prompt required" >&2; exit 1; }

run_once() {
  local prompt="$1"
  local extra_flags=""
  [[ -n "$SESSION_ID" ]] && extra_flags="--session $SESSION_ID"
  # --format json gives nd-JSON events we can parse for the session ID.
  # timeout 300 kills a hung opencode process rather than blocking forever.
  timeout 300 opencode run --format json --dangerously-skip-permissions \
    -m "$MODEL" $extra_flags "$prompt" 2>&1 || {
    local rc=$?
    [[ $rc -eq 124 ]] && echo "[oc_task] ERROR: opencode timed out after 300s" >&2
    return $rc
  }
}

extract_session_from_output() {
  # Parse the nd-JSON stream from `opencode run --format json` to find the
  # session ID for THIS invocation — race-free, unlike `session list -n 1`.
  python3 - <<'PYEOF'
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        ev = json.loads(line)
        props = ev.get("properties", {})
        sid = props.get("sessionID") or props.get("id", "")
        etype = ev.get("type", "")
        if sid and ("session" in etype or "message" in etype):
            print(sid)
            sys.exit(0)
    except (json.JSONDecodeError, KeyError):
        pass
PYEOF
}

extract_result() {
  echo "$1" | grep -oE 'RESULT:(OK|FAIL:.+)' | tail -1 || true
}

# --- Attempt 1 ---
echo "[oc_task] attempt 1/$MAX_RETRIES" >&2
OUTPUT=$(run_once "$PROMPT")

# Extract session ID from this run's JSON stream — must happen before retries.
if [[ -z "$SESSION_ID" ]]; then
  SESSION_ID=$(echo "$OUTPUT" | extract_session_from_output || true)
  if [[ -z "$SESSION_ID" ]]; then
    echo "[oc_task] WARNING: could not extract session ID; retries disabled" >&2
    MAX_RETRIES=1
  fi
fi
echo "[oc_task] session: ${SESSION_ID:-unknown}" >&2

RESULT=$(extract_result "$OUTPUT")

if [[ "$RESULT" == "RESULT:OK" ]]; then
  echo "$OUTPUT"
  exit 0
fi

# --- Retry loop ---
for attempt in $(seq 2 "$MAX_RETRIES"); do
  echo "[oc_task] attempt $attempt/$MAX_RETRIES — previous: ${RESULT:-NO_MARKER}" >&2

  REASON="${RESULT#RESULT:FAIL:}"
  [[ "$REASON" == "$RESULT" ]] && REASON="no RESULT marker — possible drift or incomplete output"

  CORRECTION="The previous attempt did not succeed. Failure: $REASON

Please retry the same task. Re-read the source files if needed. Focus only on the
original task scope. End your response with RESULT:OK or RESULT:FAIL:<reason>.
Do not commit."

  OUTPUT=$(run_once "$CORRECTION")
  RESULT=$(extract_result "$OUTPUT")

  if [[ "$RESULT" == "RESULT:OK" ]]; then
    echo "$OUTPUT"
    exit 0
  fi
done

echo "[oc_task] FAILED after $MAX_RETRIES attempts. Last: ${RESULT:-NONE}" >&2
echo "$OUTPUT"
exit 1
