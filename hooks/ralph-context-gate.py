#!/usr/bin/env python3
# ~/.claude/hooks/ralph-context-gate.py
#
# Update-safe context-budget gate for the ralph-loop plugin. Stops an active
# ralph loop when the live context occupancy of the most recent turn exceeds a
# per-model budget. Pure Python — no `jq` dependency (jq is not installed here).
#
# Mechanism: this runs as an extra Stop hook alongside the plugin's own. When
# over budget it deletes the loop state file (.claude/ralph-loop.local.md); the
# plugin's hook then finds no state file and early-exits, so the session stops.
# Worst case (if this runs after the plugin hook in a turn) the loop does one
# extra iteration before the deletion takes effect — bounded, never a runaway.
#
# Per-model rule (env vars RALPH_CONTEXT_WINDOW / RALPH_CONTEXT_LIMIT_PCT win):
#   *opus*   -> 1,000,000 window, 20% -> 200K budget
#   *sonnet* ->   200,000 window, 80% -> 160K budget
#   other    ->   200,000 window, 80% -> 160K budget + a notice to confirm

import json
import os
import re
import sys

STATE_FILE = ".claude/ralph-loop.local.md"


def env_int(name, default):
    val = os.environ.get(name)
    if val in (None, ""):
        return default
    try:
        return int(val)
    except ValueError:
        return default


def main():
    # Only act when a ralph loop is active in this project.
    if not os.path.isfile(STATE_FILE):
        return 0

    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        hook_input = {}

    # Session isolation: don't touch a loop another session owns.
    state_session = None
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^session_id:\s*(.+?)\s*$", line)
                if m:
                    state_session = m.group(1).strip()
                    break
    except OSError:
        pass
    if state_session and state_session != hook_input.get("session_id", ""):
        return 0

    transcript = hook_input.get("transcript_path", "")
    if not transcript or not os.path.isfile(transcript):
        return 0

    # Last assistant line that actually carries a usage block.
    model, ctx = "", 0
    try:
        with open(transcript, encoding="utf-8") as f:
            for line in f:
                if '"role":"assistant"' not in line:
                    continue
                try:
                    msg = json.loads(line).get("message", {})
                except Exception:
                    continue
                if msg.get("role") != "assistant":
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict) or usage.get("input_tokens") is None:
                    continue
                model = msg.get("model") or model
                ctx = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                )
    except OSError:
        return 0
    if ctx <= 0:
        return 0

    ml = model.lower()
    if "opus" in ml:
        def_window, def_pct = 1_000_000, 20
    elif "sonnet" in ml:
        def_window, def_pct = 200_000, 80
    else:
        def_window, def_pct = 200_000, 80
        sys.stderr.write(
            f"ℹ️  ralph gate: unknown model '{model}' — assuming 200000 window / 80%; "
            "set RALPH_CONTEXT_WINDOW or RALPH_CONTEXT_LIMIT_PCT to confirm.\n"
        )

    window = env_int("RALPH_CONTEXT_WINDOW", def_window)
    limit_pct = env_int("RALPH_CONTEXT_LIMIT_PCT", def_pct)
    if window <= 0:
        return 0

    ctx_pct = ctx * 100 // window
    if ctx_pct >= limit_pct:
        print(
            f"\U0001f6d1 ralph gate: context budget hit — {ctx} tok = {ctx_pct}% of "
            f"{window} (model '{model}', limit {limit_pct}%)."
        )
        print(
            "   Work preserved on disk. Re-run /ralph-loop to resume cold from the state file."
        )
        try:
            os.remove(STATE_FILE)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
