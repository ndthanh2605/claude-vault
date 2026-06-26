#!/usr/bin/env python3
"""
Tier 2 opencode supervisor: serve-based task dispatch with live SSE monitoring,
verification, and retry. Requires `opencode serve` running on --port.

Usage:
  # Start the hub once per harness session:
  opencode serve --port 4097 &

  # Dispatch a supervised task:
  python ~/.claude/skills/opencode-dispatch/scripts/oc_supervisor.py \\
    --port 4097 \\
    --prompt "TASK: ..." \\
    --verify "grep -c '^## ' docs/plan.md" \\
    --expect "5" \\
    --retries 3 \\
    --log /tmp/task.log

Output: JSON to stdout with keys: status, attempts, session_id,
        files_edited, tool_calls, verification_output, final_message
"""

import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from typing import Optional

BASE = ""  # set from --port


# ---------------------------------------------------------------------------
# HTTP helpers (no external deps)
# ---------------------------------------------------------------------------

def _req(method: str, path: str, body: Optional[dict] = None) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} on {method} {path}: {e.read().decode()}") from e


def create_session() -> str:
    return _req("POST", "/session")["id"]


def send_message(session_id: str, text: str) -> dict:
    body = {"parts": [{"type": "text", "text": text}]}
    return _req("POST", f"/session/{session_id}/message", body)


def get_messages(session_id: str) -> list:
    return _req("GET", f"/session/{session_id}/message")


# ---------------------------------------------------------------------------
# SSE monitor (background thread)
# ---------------------------------------------------------------------------

class SSEMonitor(threading.Thread):
    def __init__(self, port: int, session_id: str, log_path: Optional[str]):
        super().__init__(daemon=True)
        self.port = port
        self.session_id = session_id
        self.log_path = log_path
        self.files_edited: list[str] = []
        self.idle = threading.Event()
        self.connected = threading.Event()  # set once SSE connection is established
        self._stop = threading.Event()

    def run(self):
        url = f"http://localhost:{self.port}/event"
        log_fh = open(self.log_path, "w") if self.log_path else None
        try:
            req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
            with urllib.request.urlopen(req, timeout=600) as resp:
                # Connection established — safe for caller to send first message.
                self.connected.set()
                for raw_line in resp:
                    if self._stop.is_set():
                        break
                    line = raw_line.decode().strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type", "")
                    props = event.get("properties", {})

                    if etype == "file.edited":
                        fpath = props.get("file", "")
                        self.files_edited.append(fpath)
                        self._log(log_fh, f"file.edited: {fpath}")

                    elif etype == "session.idle":
                        if props.get("sessionID") == self.session_id:
                            self._log(log_fh, "session.idle — task complete")
                            self.idle.set()

                    elif etype == "session.status":
                        if props.get("sessionID") == self.session_id:
                            status_type = props.get("status", {}).get("type", "?")
                            self._log(log_fh, f"session.status: {status_type}")

                    elif etype == "todo.updated":
                        self._log(log_fh, "todo.updated")

                    elif etype == "permission.updated":
                        self._log(log_fh, f"permission.updated: {json.dumps(props)}")

        except Exception as e:
            if not self._stop.is_set():
                self._log(log_fh, f"SSE monitor error: {e}")
            # Unblock callers waiting on connected if the connection failed.
            self.connected.set()
        finally:
            if log_fh:
                log_fh.close()

    def stop(self):
        self._stop.set()

    def _log(self, fh, msg: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, file=sys.stderr)
        if fh:
            fh.write(line + "\n")
            fh.flush()


# ---------------------------------------------------------------------------
# Tool audit
# ---------------------------------------------------------------------------

def audit_tool_calls(messages: list) -> int:
    count = 0
    for msg in messages:
        for part in msg.get("parts", []):
            if part.get("type") == "tool":
                count += 1
    return count


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def extract_assistant_text(resp: dict) -> str:
    """Extract text from the assistant reply, guarding against role confusion."""
    info = resp.get("info", {})
    if info.get("role") != "assistant":
        return ""
    text_parts = [
        p.get("text", "")
        for p in resp.get("parts", [])
        if p.get("type") == "text"
    ]
    return "\n".join(text_parts)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def run_verify(cmd: str) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--port",    type=int, default=4097)
    ap.add_argument("--session", default="")
    ap.add_argument("--prompt",  required=True)
    ap.add_argument("--verify",  default="")
    ap.add_argument("--expect",  default="")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--log",     default="")
    args = ap.parse_args()

    BASE = f"http://localhost:{args.port}"

    session_id = args.session or create_session()
    print(f"[oc_supervisor] session: {session_id}", file=sys.stderr)

    monitor = SSEMonitor(args.port, session_id, args.log or None)
    monitor.start()

    # Wait for SSE connection before sending the first message — prevents the
    # race where session.idle fires before the monitor is listening.
    if not monitor.connected.wait(timeout=10):
        print("[oc_supervisor] WARNING: SSE connection not established after 10s; "
              "idle detection may miss fast-completing tasks", file=sys.stderr)

    result = {
        "status": "fail",
        "attempts": 0,
        "session_id": session_id,
        "files_edited": [],
        "tool_calls": 0,
        "verification_output": "",
        "final_message": "",
    }

    prompt = args.prompt
    for attempt in range(1, args.retries + 1):
        result["attempts"] = attempt
        print(f"[oc_supervisor] attempt {attempt}/{args.retries}", file=sys.stderr)

        monitor.idle.clear()
        resp = send_message(session_id, prompt)

        final_text = extract_assistant_text(resp)
        result["final_message"] = final_text

        # Wait up to 10 min for session.idle SSE event.
        monitor.idle.wait(timeout=600)

        # Determine success via verification command or RESULT: marker.
        if args.verify:
            verify_out = run_verify(args.verify)
            result["verification_output"] = verify_out
            print(f"[oc_supervisor] verify: {verify_out!r}", file=sys.stderr)
            success = (verify_out == args.expect) if args.expect else bool(verify_out)
        else:
            success = "RESULT:OK" in final_text

        if success:
            result["status"] = "ok"
            break

        if args.verify and args.expect:
            reason = f"verify '{args.verify}' returned {verify_out!r}, expected {args.expect!r}"
        else:
            reason = "no RESULT:OK marker in assistant response"

        prompt = (
            f"The previous attempt did not satisfy the success criteria: {reason}\n\n"
            "Please retry the task, focusing only on what went wrong. "
            "Re-read source files if needed. Do not commit."
        )

    # Final audit
    monitor.stop()
    all_messages = get_messages(session_id)
    result["files_edited"] = list(dict.fromkeys(monitor.files_edited))
    result["tool_calls"] = audit_tool_calls(all_messages)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
