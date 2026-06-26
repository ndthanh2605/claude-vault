---
name: opencode-dispatch
description: >
  Orchestrates OpenCode as a parallel subprocess executor for coding, editing, and document
  tasks — using open-source AI models (default: deepseek/deepseek-v4-pro). Handles task
  decomposition into atomic units, parallel dispatch across files, output capture via
  context-mode, and structured verification.

  Invoke this skill whenever the user says: "use opencode", "dispatch/delegate to opencode",
  "run through opencode", "have opencode do this", "use deepseek/qwen to implement",
  "offload to opencode", or when they want any task executed by a non-Claude AI runtime.
  Also invoke proactively when executing multi-step plans with many file changes — parallel
  opencode agents can do this work in a fraction of the time. If opencode or any open-source
  model is mentioned at all, trigger this skill. When a plan needs implementation, strongly
  prefer dispatching to opencode over inline implementation.
---

# OpenCode Dispatch

Runs `opencode run` as subprocess workers — one call per atomic task, dispatched in parallel
where files don't overlap, output captured in context-mode's sandbox. The orchestration
pattern: decompose → dispatch → verify.

## Model selection

**Default (paid):** `deepseek/deepseek-v4-pro`

**Paid options (DeepSeek API):**
| Model ID | Notes |
|----------|-------|
| `deepseek/deepseek-v4-pro` | **Default** — strongest DeepSeek |
| `deepseek/deepseek-v4-flash` | Faster, cheaper |
| `deepseek/deepseek-reasoner` | Extended reasoning (R1-style) |

### Free model discovery

Free models (opencode-hosted, no API key needed) change frequently — don't assume a specific
model ID is still available. **Discover them fresh each session:**

```bash
opencode models 2>/dev/null | grep '^opencode/'
```

This lists all opencode-provider models, which are the free-tier ones. Pick the strongest
from the current output using these ranking heuristics:

1. **Higher version beats lower** — v4 > v3 > v2
2. **Quality tier beats speed tier** — `plus` or `pro` > base > `flash` or `mini`
3. **Larger known architecture beats smaller** — prefer Qwen 3.x, DeepSeek V4 over older families
4. **When unsure between two** — pick the one with the longer/more specific name; generic names
   (e.g. `big-pickle`) are wildcards with unknown capability

Use the selected free model for all tasks in the session unless the user specifies otherwise.
Free models have proven production-capable: they handle 1500-line plan reads, multi-point
insertions, and complex edits reliably. Don't underestimate them.

**Task-type guidance:**
| Task | Model choice |
|------|-------------|
| General coding, edits, plans (cost matters) | Best current free model |
| General coding, edits, plans (quality matters) | `deepseek/deepseek-v4-pro` |
| Speed-sensitive batch work | Fastest current free model (look for `flash` in name) |
| Hard algorithmic reasoning | `deepseek/deepseek-reasoner` |

---

## Task sizing — the most critical decision

Each opencode call should do **one atomic action on one target file**. This is the single
most important factor for reliable results.

**Right size (one call):**
- Create one new file with content from a spec section
- Make one targeted edit to an existing file (insert section, change a value, append a row)
- Run a verification sweep (multiple grep checks are fine — they're read-only)
- Summarize one document

**Too large (split it):**
- "Implement the whole plan" → one call per file/change
- "Create three skill files" → three parallel calls
- "Edit five files to add X" → five parallel calls

**Split rule:** if the task touches more than one file OR has more than one logically
independent edit, split it. Oversized prompts cause drift — opencode does things not asked
for (commits, out-of-scope edits, wrong steps).

---

## Prompt construction

**The pattern:**
```
Read [source file], find [section name]. Execute [step N] only:
[one clear action]. Then verify: [command]. Do not commit.
```

**Four principles:**

1. **Point to source files — don't embed content.** Let opencode read the plan/spec
   directly. Shell heredocs containing markdown (backticks, `-->`, fenced code blocks)
   cause quoting failures. A prompt like "Read docs/plan.md, find '## Task 3'" is both
   shorter and more reliable than pasting the task content inline.

2. **Name the step number explicitly.** "Execute Step 2 only" is unambiguous.
   "Do the second thing" is not.

3. **Include a verification command in the prompt.** Ask opencode to run
   `grep -n '^## ' <file>` or `head -4 <file>` at the end. The output gets indexed
   by context-mode and becomes queryable proof of success or failure.

4. **Always end with "Do not commit."** Opencode will commit if the task spec includes
   commit steps and you don't explicitly prohibit it. Every prompt, every time.

**Examples:**

*Create a file from a plan section:*
```
Read docs/plan.md, find '## Task 3: Create .claude/skills/pull.md'.
Execute Step 1 only: write .claude/skills/pull.md with the exact markdown
content shown in that step's code block. Then verify:
grep -n '^## ' .claude/skills/pull.md and head -4 .claude/skills/pull.md.
Do not commit.
```

*Targeted edit to an existing file:*
```
Read docs/plan.md, find '## Task 7: Update CLAUDE.md'. Execute Steps 1 and 2:
add item 10 to the Source Of Truth list, then add three checklist questions
after the last existing question. Then verify:
grep -cE '\.claude/skills|workpad sibling|state-machine gate' CLAUDE.md.
Do not commit.
```

*Parallel file creation (9 instances ran simultaneously in production):*
Each agent gets its own prompt following the pattern above, dispatched via
`ctx_batch_execute` with `concurrency: 8`.

**Structured prompt template (use when drift is a risk):**

```
TASK: <one atomic action on one target file>
CONTEXT: Read <source file>, find '<section name>'. Execute step <N> only.
CONSTRAINTS:
  - If anything is unclear, list ALL questions at the top before doing any work.
  - Do not touch files outside the task scope.
  - Do not commit.
VERIFY: After completing, run: <grep/head command>. Include the full output verbatim.
SUCCESS MARKER: End your response with exactly one of:
  RESULT:OK
  RESULT:FAIL:<one-line reason>
```

The `RESULT:` marker enables programmatic validation without model judgment.
Use this template (via `~/.claude/skills/opencode-dispatch/scripts/oc_task.sh`) whenever a plain `opencode run`
call has produced wrong output or scope drift on a similar task.

---

## Parallel execution

Multiple opencode instances can run simultaneously when their **target files don't overlap**.
Each instance runs in its own process with its own port and AI session — no shared state.
Source files (plan docs, specs) can be read simultaneously by all instances without conflict.

**Planning a parallel wave:**
1. List all tasks and their target files
2. Tasks touching the same target file → sequential
3. Everything else → one parallel wave

**Dispatch template (via context-mode):**

```python
ctx_batch_execute(
  commands=[
    {"label": "Task-A-filename", "command": "opencode run -m opencode/qwen3.6-plus-free --dangerously-skip-permissions '...'"},
    {"label": "Task-B-filename", "command": "opencode run -m opencode/qwen3.6-plus-free --dangerously-skip-permissions '...'"},
    # up to 8 simultaneously; additional tasks queue and start as slots free
  ],
  queries=[
    "task-A written sections verified",
    "task-B created confirmed",
    "error failed write exception",   # catches failures across all agents at once
  ],
  concurrency=8,
  timeout=300000  # 5 min per command; applies per-command when concurrency > 1
)
```

**Label quality matters.** The label becomes the FTS5 chunk title in context-mode's index.
`"Task3-pull.md"` is far more queryable than `"cmd3"`.

---

## Context-mode integration

Always wrap opencode calls in `ctx_batch_execute` — never call Bash directly for dispatch.
This keeps opencode's verbose terminal output in the sandbox and surfaces only what you
query for.

**Query strategy after a batch:**
- Success signal: `"<task-name> written verified"`, `"file created confirmed"`
- Failure signal: `"error failed write exception"` — one query catches all agent failures
- Specific checks: `"state machine count 9"`, `"frontmatter name description"`

**Race condition warning:** if command B reads a file that command A writes, they must run
sequentially — either chained with `&&` in one command, or in separate `ctx_batch_execute`
calls. Running them at `concurrency > 1` will cause B to read a missing or partial file
with no error reported.

**Final verification sweep:** after all agents complete, run a dedicated `ctx_batch_execute`
with the plan's expected grep counts as standalone commands (not inside opencode). This gives
a clean, authoritative pass/fail for every check without relying on opencode's self-reported
output.

---

## Verification patterns

Include these in the opencode prompt itself — the output gets indexed:

| Check | Command |
|-------|---------|
| File sections present | `grep -n '^## ' <file>` |
| Frontmatter correct | `head -4 <file>` |
| Pattern count | `grep -c '<pattern>' <file>` |
| File exists | `ls <file>` |
| Specific value | `grep -A1 '^## Status' <file> \| tail -1` |
| Installer smoke | `<script> --dry-run 2>&1 \| grep '<pat>' \| wc -l` |

---

## Isolation model

Opencode is **process-isolated** but **not filesystem-isolated**:

| Isolated | Shared |
|----------|--------|
| Process (own PID) | Working directory |
| Network port (random) | All files in the repo |
| AI session / memory | Git state |

Two agents writing the same file will produce a corrupted result with no error. Always
check for file overlap before parallelizing. Two agents reading the same file simultaneously
is always safe.

---

## Flags reference

| Flag | When to use |
|------|------------|
| `--dangerously-skip-permissions` | Always for unattended runs — auto-approves file edits and shell commands. Required when opencode is not supervised interactively. |
| `-m provider/model` | Override default model |
| `-f file` | Attach file to opencode's context (alternative to asking it to read the file) |
| `--dir /path` | Set working directory (defaults to current) |
| `--format json` | Structured output for programmatic parsing |
| `--thinking` | Show reasoning blocks (for reasoner models) |
| `--session SESSION_ID` | Continue an existing session — model retains full prior context |
| `--continue` | Continue the most recent session |
| `--fork` | Fork when continuing (branches history, use with `--session`) |

---


---

## Safety rules

1. **Never include commit steps in prompts.** End every prompt with "Do not commit."
   Opencode follows task specs literally — if a step says "commit", it commits.

2. **Check file overlap before parallelizing.** Two agents writing the same file will
   silently corrupt it. The check takes seconds; the recovery doesn't.

3. **Keep commits in the user's hands.** Use opencode for all implementation.
   Reserve `git commit` for an explicit, human-approved step.

4. **Prefer small tasks over large ones.** When uncertain about scope, split. A failed
   atomic task is easy to retry. A failed 10-step task may leave the repo in an
   inconsistent state.

---

## Supervision modes

Choose based on how much control you need:

| Mode | Tool | When to use |
|------|------|-------------|
| **Fire-and-forget** | `opencode run` via `ctx_batch_execute` | Stable tasks with well-understood scope; parallel wave execution |
| **Retry loop** | `~/.claude/skills/opencode-dispatch/scripts/oc_task.sh` | Drift is a risk; task has previously failed or is ambiguous |
| **Full supervision** | `~/.claude/skills/opencode-dispatch/scripts/oc_supervisor.py` | Need real-time file monitoring, tool audit, or selective permission control |

### Retry loop (`~/.claude/skills/opencode-dispatch/scripts/oc_task.sh`)

Wraps `opencode run` with a session-based retry loop. No new infrastructure needed.

```bash
MODEL=$(opencode models 2>/dev/null | grep '^opencode/' | head -1)
bash ~/.claude/skills/opencode-dispatch/scripts/oc_task.sh \
  --model "$MODEL" \
  --retries 3 \
  --prompt "TASK: Write .claude/skills/pull.md
CONTEXT: Read docs/plan.md, find '## Task 3'. Execute Step 1 only.
CONSTRAINTS:
  - If anything is unclear, list ALL questions before doing any work.
  - Do not commit. Do not touch other files.
VERIFY: grep -n '^## ' .claude/skills/pull.md && head -4 .claude/skills/pull.md
SUCCESS MARKER: End your response with RESULT:OK or RESULT:FAIL:<reason>"
```

On failure the script retries on the **same session** — opencode retains full context,
so corrections land on top of what it already knows rather than starting cold.

### Full supervision (`~/.claude/skills/opencode-dispatch/scripts/oc_supervisor.py`)

Requires `opencode serve --port 4097 &` running in the background.
Returns JSON with `files_edited`, `tool_calls`, and `verification_output`.

```bash
# Start hub once per harness session
opencode serve --port 4097 &

SESSION=$(curl -s -X POST http://localhost:4097/session | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['id'])")

python ~/.claude/skills/opencode-dispatch/scripts/oc_supervisor.py \
  --port 4097 \
  --session "$SESSION" \
  --prompt "$(cat prompts/task3.txt)" \
  --verify "grep -c '^## ' docs/plan.md" \
  --expect "5" \
  --retries 3 \
  --log /tmp/task3.log
```

Live events visible in `--log` during execution:
- `file.edited` — every file write as it happens
- `session.status` — `busy` / `idle` / `retry` transitions
- `todo.updated` — opencode's internal task checklist changes
- `permission.updated` — tool approval requests (future: approve/deny selectively)

---

## Post-task audit

After any supervised task, query the session for a full tool call audit.
Requires `opencode serve` running on port 4097.

```bash
# List tool calls from last session with their inputs and outputs
SESSION=$(opencode session list -n 1 --format json | \
  python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])")

curl -s "http://localhost:4097/session/$SESSION/message" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
for msg in msgs:
    for part in msg.get('parts', []):
        if part.get('type') == 'tool':
            state = part.get('state', {})
            print(f\"  tool: {part['tool']}\")
            print(f\"  status: {state.get('status')}\")
            print(f\"  output: {str(state.get('output',''))[:120]}\")
            print()
"

# Check what files were actually changed
git diff --stat HEAD
```

Cross-reference `files_edited` from `oc_supervisor.py` output against `git diff --stat`
to catch any writes opencode made outside the task scope.
