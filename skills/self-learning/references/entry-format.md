# LEARNINGS.md format

The whole point of a fixed format is that entries stay both **human-readable** (you can open the file
and skim it) and **machine-filterable** (you can grep it, and `learnings.py` can parse it). Keep to
the format and both stay true.

## Sections

Use these H2 headings, in this order. Each groups entries by *category* so the section itself tells
the reader what kind of knowledge they're looking at:

```markdown
# Project Learnings — <repo name>

## What Works
<!-- Approaches, patterns, and solutions that have proven effective here -->

## What Doesn't Work
<!-- Failed approaches, dead ends, antipatterns to avoid -->

## Codebase Patterns
<!-- Project-specific conventions, architecture decisions, naming -->

## Tool & Library Notes
<!-- Quirks, gotchas, and useful behaviors of dependencies (pin versions) -->

## Recurring Errors & Fixes
<!-- Errors seen more than once and their resolutions -->

## Session Notes
<!-- Dated, one-line summaries of what each session accomplished -->

## Open Questions
<!-- Unresolved things, left for a future session -->
```

Don't skip **What Doesn't Work**. People gravitate toward recording wins, but a sharp "don't do this,
because X" entry is often the single most time-saving line in the file.

## Entry format

Every entry is a markdown bullet with a compact metadata prefix, then a concrete statement:

```
- [YYYY-MM-DD · tag1,tag2 · conf:high] <concrete statement with a specific anchor and action>
```

- **Date** — when the learning was captured (ISO `YYYY-MM-DD`). Drives staleness scanning.
- **Tags** — comma-separated, no spaces (`auth,jwt`). The feature area / tools, used for scoped recall.
  Include a stack/version tag when the learning is version-specific (`passport-jwt-v4`, `react-18`) so
  it can be discounted after an upgrade.
- **conf** — `high` (verified, reproduced, or user-confirmed) · `med` (observed once, plausible) ·
  `low` (suspected, not yet confirmed). Recall weights higher-confidence entries first.

The prefix is intentionally small; the *category* lives in the section heading, so don't also encode
"success/failure" in the prefix — that's what `## What Works` vs `## What Doesn't Work` is for.

### Examples

```
## Tool & Library Notes
- [2026-06-24 · jest,test-config · conf:high] Jest hangs on exit without `--forceExit`; it's wired
  into the `test` script in package.json. Don't remove it.

## What Doesn't Work
- [2026-06-24 · checkout,state · conf:high] Local component state in the checkout flow breaks —
  cart data is shared across three components. Use the Zustand store (src/stores/cartStore.ts) for
  anything touching cart state.

## Recurring Errors & Fixes
- [2026-06-24 · auth,passport-jwt-v4 · conf:high] passport-jwt v4 doesn't reject expired tokens on
  its own; add a manual `exp` check before `validate()` in src/middleware/auth.ts.

## Session Notes
- [2026-06-24] Migrated auth middleware to JWT refresh tokens; documented the passport-jwt expiry gap.
```

## Supersede, decay, prune

These three keep noise out. Noise accumulates silently, so treat maintenance as part of the loop, not
an afterthought.

- **Supersede (contradictions).** When a new learning contradicts an existing one, replace the old
  entry in place — don't leave both. Git history is your audit trail, so you lose nothing by deleting
  the stale claim, and you spare the next reader from reconciling two conflicting lines.
- **Decay (staleness).** A learning about a library version you've since upgraded can be actively
  misleading. Date every entry and version-tag the stack-specific ones. The `scan-stale` command of
  the helper script (`python3 <skill-dir>/scripts/learnings.py scan-stale ./LEARNINGS.md`) flags old
  and version-tagged entries for review — it deliberately doesn't auto-delete, because only a human
  knows whether a given entry still applies.
- **Prune (bloat).** Remove entries for code that was deleted or refactored away, and consolidate
  near-duplicates into one clearer line. Aim to keep the file skimmable.

## Scoped files

If the file grows past what's comfortable to load, split by domain — `LEARNINGS-auth.md`,
`LEARNINGS-db.md`, `LEARNINGS-frontend.md` — and have `CLAUDE.md` reference the relevant one based on
the task. This keeps each recall focused.

## Team conventions

When a `LEARNINGS.md` is shared across a team, two rules prevent it from becoming a merge-conflict
magnet or a contradictory mess:

- **Append-only in pull requests.** Each person adds entries; nobody edits someone else's in the same
  PR. This avoids conflicts and accidental overwrites.
- **A designated maintainer** periodically consolidates, resolves contradictions, and prunes — the
  cleanup that append-only defers.
