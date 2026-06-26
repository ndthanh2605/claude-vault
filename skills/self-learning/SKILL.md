---
name: self-learning
description: >-
  Capture and reuse durable, project-specific operational knowledge across sessions via a
  version-controlled LEARNINGS.md file — what works, what fails, codebase conventions, tool/library
  gotchas, and recurring fixes for THIS repo. Use it at the START of substantial work to recall
  relevant past learnings before acting, and at the END of a session (or right after solving
  something non-obvious, debugging a tricky failure, or discovering a convention) to capture what was
  learned. Trigger whenever the user says "wrap up the learnings", "what do we know about this
  codebase", "remember this for next time", "capture what we learned", "update LEARNINGS", or starts
  work in a repo that already has a LEARNINGS.md. Also trigger proactively when you just spent real
  effort uncovering something that would save time next session — don't let that knowledge evaporate.
  This is distinct from short-term session-resume notes and from general wiki/zettel notes: it is
  specifically the accumulated "how to work in THIS codebase" memory.
---

# Self-Learning

A coding agent is brilliant for one session and then forgets everything. The next session — same
repo, similar task — it starts cold: it repeats last week's mistakes, re-discovers the same edge
cases, re-derives conventions you already established. The model isn't getting smarter over time; it
keeps getting a clean slate.

This skill closes that gap with a small, durable feedback loop built around a **`LEARNINGS.md`** file
that lives in the repo. The loop has three moves:

1. **Recall** — before substantial work, read the relevant past learnings and let them shape the approach.
2. **Capture** — after the work, write back what was learned: what worked, what failed, what surprised you.
3. **Maintain** — periodically prune and reconcile so the file stays high-signal.

`LEARNINGS.md` is a human-readable, version-controlled "working memory" for the project — think of it
as the dynamic counterpart to the static `CLAUDE.md` operating manual. It's lightweight by design
(manual RAG, no infrastructure); for most projects a single markdown file is more than enough.

## Recall — start of substantial work

Do this before diving into a non-trivial task, especially in any repo that has a `LEARNINGS.md`.

1. **Locate the file.** Look for `LEARNINGS.md` at the repo root (or `.claude/LEARNINGS.md`). If the
   project clearly warrants one and none exists, offer to create it with
   `python3 <skill-dir>/scripts/learnings.py init ./LEARNINGS.md` (the script lives in this skill's
   directory, whose base path you're given at load time — the cwd is the user's repo).
2. **Pull only what's relevant.** Don't flood your reasoning with the whole file. Identify the
   current task's scope (the feature area, the tools involved) and surface the entries that match by
   section and tags. A focused handful beats a wall of context.
3. **Weight failures heavily.** Negative entries (What Doesn't Work, Recurring Errors) prevent
   repeating a known mistake — they teach more than successes. Read those first.
4. **Treat entries as high-confidence guidance, not law.** They came from real runs, so trust them —
   unless an entry is clearly stale (version-tagged against a stack that has since moved) or the user
   contradicts it. When in doubt, say what the entry claims and let the user confirm.

## Capture — end of session, or right after a non-obvious solve

Capture is the move that makes the loop compound, so it has to happen consistently. The most common
way these systems fail is simply that capture gets skipped "because I'm in a hurry." Build it into the
session-ending ritual, the same way you commit code. Capture after: a hard-won debug, a solution
found only after trying several approaches, a new convention or architectural decision, or a tool
behaving in a surprising way.

1. **Mine the session for signal.** Ask: What did we land on after trying multiple approaches? What
   error showed up more than once, and how was it fixed? What decision did we make about structure?
   What library/API behavior surprised us? What's still unresolved? **Bias toward failures and
   surprises** — they're the highest-value entries and the ones people instinctively skip.
2. **Apply the concreteness gate** (below) to each candidate. Drop anything that doesn't pass —
   a vague entry is worse than no entry.
3. **Read the existing file first, then extend — never duplicate.** For each candidate, check whether
   a related entry already exists. If so, sharpen or replace it. If a new learning contradicts an old
   one, *replace the old entry* (git history preserves it) rather than letting both sit there and
   confuse the next reader.
4. **Write in the standard format** under the right section, and add a dated line to `Session Notes`
   summarizing what the session accomplished. See `references/entry-format.md`.
5. **Report what you changed.** These entries are proposals. You are an LLM summarizing your own
   session, and you can mischaracterize what happened — so surface the additions and keep the file
   easy for the user to review and correct.

### The concreteness gate

This is the single most important rule, because vague entries are what quietly ruin these files.

> An entry earns its place only if someone — human or agent — reading it cold could act on it without
> re-investigating. Require two things: **(a) a specific anchor** (a file path, a symbol, a
> tool/library + version, or an exact error message) and **(b) a specific action or consequence.**

- Fails the gate: *"Promises can be tricky."* — no anchor, no action. Pure noise.
- Passes the gate: *"`Promise.all()` in the ingestion pipeline times out past ~30 items; use
  `Promise.allSettled()` with batches of 10 in `src/ingest/*.ts`."*

If you can't yet be that specific, don't write the entry. You can always capture it next time once
you understand it well enough to be concrete. Every vague line dilutes every future recall.

## Maintain — keep the file high-signal

Learnings go stale and files bloat; past a couple hundred entries the signal-to-noise ratio drops.
Run maintenance periodically, on request, or whenever a recall surfaced something that looked stale or
self-contradictory.

The helper script lives in **this skill's own directory** (its base path is given to you when the
skill loads), not in the user's repo — so invoke it by that path while staying in the repo, e.g.
`python3 <skill-dir>/scripts/learnings.py stats ./LEARNINGS.md`. Don't write `python scripts/...`
relative to the cwd; the cwd is the user's project, where the script isn't present.

- `python3 <skill-dir>/scripts/learnings.py stats LEARNINGS.md` — section distribution and
  confidence/format health. A pile-up of unresolved `Open Questions`, or a section that's nearly all
  failures, is a signal worth acting on rather than just logging more.
- `python3 <skill-dir>/scripts/learnings.py scan-stale LEARNINGS.md --days 90` — flags entries older
  than the horizon and version-tagged entries, for human review (it flags; it never deletes).
- By hand: prune entries for code that was deleted or refactored, consolidate near-duplicates,
  resolve contradictions explicitly, and move resolved questions out of `Open Questions`.
- If the file gets long, split it into scoped files (`LEARNINGS-auth.md`, `LEARNINGS-db.md`) and have
  `CLAUDE.md` point at the relevant one per task.

## Relationship to other memory tools

Keep these layers distinct so you reach for the right one:

- **Session-resume notes** (e.g. a `.remember/` buffer) — short-term continuity to pick a task back up
  mid-stream. Ephemeral. Not this skill.
- **Wiki / zettel / knowledge-base notes** — durable *conceptual* knowledge ("how channels work"),
  often cross-project. Not this skill.
- **`LEARNINGS.md` (this skill)** — durable *operational* knowledge for one specific codebase: what
  works here, what fails here, the conventions and gotchas of this repo.

## Resources

- `references/entry-format.md` — the file's sections, the entry prefix format, confidence levels,
  supersede/decay/prune mechanics, scoped files, and team (append-only) conventions. Read it before
  writing entries.
- `references/automation.md` — optional: a hook + `CLAUDE.md` snippet to make recall-on-start and
  capture-on-end fire automatically instead of relying on memory.
- `scripts/learnings.py` — `init`, `stats`, `scan-stale`. Dependency-free; run with `python3` by its
  path inside this skill's directory (see Maintain above), since the cwd at runtime is the user's repo.
