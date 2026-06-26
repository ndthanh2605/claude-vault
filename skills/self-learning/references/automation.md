# Optional automation

The skill works fine driven by hand — you recall at the start, capture at the end. But the failure
mode of every self-learning system is the same: capture gets skipped, and the loop stops compounding.
The cure is to stop relying on memory and let the harness fire the loop for you. Two pieces, both
optional.

## 1. Recall on start — point CLAUDE.md at the file

Claude Code reads `CLAUDE.md` at the repo root every session. Add a short pointer so recall happens
without anyone asking:

```markdown
## Session Context

Before starting substantial work, read `LEARNINGS.md` in the repo root. It holds accumulated
operational knowledge from past sessions — approaches that worked, approaches that failed, codebase
conventions, and known fixes. Treat it as high-confidence guidance unless an entry is clearly stale
or explicitly overridden.

## End of Session

When wrapping up, capture what was learned into `LEARNINGS.md` (the self-learning skill). Don't skip
this — it's what makes the next session start ahead instead of cold.
```

## 2. Capture on end — a Stop hook

A reminder in `CLAUDE.md` still depends on the model choosing to act on it. For true automation, wire
a hook in `.claude/settings.json` (or `settings.local.json` for personal config) that fires when the
session stops and nudges the capture step:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Session ending — run the self-learning capture step: review this session and update LEARNINGS.md with concrete, anchored learnings (extend existing entries, do not duplicate).'"
          }
        ]
      }
    ]
  }
}
```

The hook's stdout is surfaced back into the session as context, prompting the capture before the
session closes. Keep the message short and specific — it's a nudge, not the instructions (those live
in `SKILL.md`).

> Note: hook event names and payloads evolve. Verify the current `Stop` / session-end hook contract
> in the Claude Code docs before relying on this, and adjust the event key if needed.

## A note on heavier setups

The two source articles also describe storing learnings as typed JSON (JSONL → SQLite/FTS5 → vector
store) with automatic embedding-based retrieval, and offloading storage/retrieval to a hosted
workflow. That's the right call only when you've outgrown a single markdown file — many runs per day,
cross-machine sharing, or task descriptions varied enough that semantic search beats tag matching.
For the overwhelming majority of single-project work, the markdown loop in this skill is simpler,
inspectable, and sufficient. Graduate to the heavier machinery when the file genuinely stops scaling,
not before.
