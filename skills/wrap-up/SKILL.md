---
name: wrap-up
description: Use when user says "wrap up", "close session", "end session",
  "wrap things up", "close out this task", or invokes /wrap-up — runs
  end-of-session checklist for session state capture, memory consolidation,
  and self-improvement
---

# Session Wrap-Up

Run three phases in order. Each phase is conversational and inline — no
separate documents unless noted. All phases auto-apply without asking; present
a consolidated report at the end.

## Phase 1: Record Session State

Write (or overwrite) `SESSION.md` at the project root. This file captures raw
working state so the next session can resume without re-deriving context. It is
not a changelog — it describes *current* state, not history.

Add `SESSION.md` to `.gitignore` if not already there.

Use this template exactly:

```markdown
# Session State
_Last updated: YYYY-MM-DD_

## Status
<!-- What is actively in progress right now. One focused paragraph. -->

## Pending
<!-- Ordered list of next steps and queued items, most important first. -->

## Recent Implementation
<!-- Brief bullet summary of what changed this session. Not a changelog —
     just enough context to remember what was touched. -->

## Testing
<!-- What has been tested, what still needs tests, any known failures. -->

## Design Notes
<!-- Decisions made this session, options that were considered and rejected,
     constraints discovered. -->

## Open Questions
<!-- Unresolved things to revisit. Delete items once resolved. -->
```

Fill every section. Use "—" for sections with nothing to report rather than
leaving them empty, so it's clear the section was reviewed.

## Phase 2: Remember It

Review what was learned during the session. Decide where each piece of
knowledge belongs in the memory hierarchy:

**Memory placement guide:**
- **Auto memory** (Claude writes for itself) — Debugging insights, patterns
  discovered during the session, project quirks
- **CLAUDE.md** (instructions for Claude) — Permanent project rules,
  conventions, commands, architecture decisions that should guide all future
  sessions
- **`.claude/rules/`** (modular project rules) — Topic-specific instructions
  scoped to certain file types or areas via `paths:` frontmatter
- **`CLAUDE.local.md`** (private per-project notes) — Personal WIP context,
  local URLs, sandbox credentials, current focus areas; gitignored, not
  committed
- **`@import` references** — When a CLAUDE.md would benefit from referencing
  another file rather than duplicating its content

**Decision framework:**
- Permanent project convention? → CLAUDE.md or `.claude/rules/`
- Scoped to specific file types? → `.claude/rules/` with `paths:` frontmatter
- Pattern or insight Claude discovered? → Auto memory
- Personal or ephemeral context? → `CLAUDE.local.md`
- Duplicates content elsewhere? → Use `@import` instead

## Phase 3: Review & Apply

Analyze the conversation for self-improvement findings. If the session was
short or routine with nothing notable, say "Nothing to improve" and you're done.

**Auto-apply all actionable findings immediately** — do not ask for approval.
Apply the changes, then present a summary of what was done.

**Finding categories:**
- **Skill gap** — Things Claude struggled with, got wrong, or needed multiple attempts
- **Friction** — Repeated manual steps, things the user had to ask for explicitly that should have been automatic
- **Knowledge** — Facts about the project, preferences, or setup that Claude didn't know but should have
- **Automation** — Repetitive patterns that could become skills, hooks, or scripts

**Action types:**
- **CLAUDE.md** — Edit the relevant project or global CLAUDE.md
- **Rules** — Create or update a `.claude/rules/` file
- **Auto memory** — Save an insight for future sessions
- **Skill / Hook** — Document a new skill or hook spec for implementation
- **CLAUDE.local.md** — Create or update per-project local memory

Present a summary after applying, in two sections:

Findings (applied):

1. ✅ Skill gap: Cost estimates were wrong multiple times
   → [CLAUDE.md] Added token counting reference table

2. ✅ Knowledge: Worker crashes on 429/400 instead of retrying
   → [Rules] Added error-handling rules for worker

3. ✅ Automation: Checking service health after deploy is manual
   → [Skill] Created post-deploy health check skill spec

---
No action needed:

4. Knowledge: Discovered X works this way
   Already documented in CLAUDE.md
