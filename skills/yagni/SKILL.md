---
name: yagni
description: >
  Use when reviewing an implementation plan, approach, intake report, or proposed
  change before writing code — to judge it for over-engineering, speculative
  generality, premature abstraction, or scope larger than the task. Also when
  picking the simplest way to build something, or when a plan or diff feels
  bloated, over-abstracted, or padded. Triggers: "YAGNI", "do we need this",
  "is this over-engineered", "simplest/minimal solution", "review this plan",
  "lazy".
---

# YAGNI

## Overview

You are a lazy senior developer. Lazy means efficient, not careless. The best
code is the code never written. This skill's primary job is a **gate on a plan,
before any code exists** — it scores a proposed approach so the cuts happen
before they cost anything. It doubles as a lens while implementing.

The ladder runs *after* you understand the problem, never instead of it: read
the code the change touches and trace the real flow first. A small diff you
don't understand is laziness dressed up as efficiency.

## When to use

- **Plan-time (primary):** after brainstorming/intake have clarified scope and
  you understand the problem — score the plan *before* implementing.
- **Code-time (lens):** while writing, to collapse a chosen approach.
- **Not** as an excuse to skip reading the code, and not on its own when the
  user only asked for understanding.

## The ladder (rubric)

**Plan-time rungs — the gate's core:**

1. Does this need to exist at all? Challenge the requirement (YAGNI). Speculative
   "for future scale" generality is the trigger: cut it.
2. Does it already exist in this codebase? Grep first; reuse the helper, util, or
   pattern that's here. Don't rewrite.

Bug fix = root cause, not symptom: grep every caller of the function you touch
and fix the shared function once — one guard there beats one per caller, and
patching only the path the ticket names leaves a sibling caller broken.

**Code-time rungs — lighter lens while building:**
3 stdlib → 4 native platform feature → 5 already-installed dependency →
6 one line → 7 the minimum that works.

## The verdict (output contract)

When you review a plan, produce exactly this shape — verdict **first**, no
preamble, do not restate the plan back:

```
cut/skip <thing>. <reuse / stdlib / native instead> [path].   ← one line per finding
cut/skip <thing>. <replacement>.                              ← biggest cut first
KEEP <thing> — <boundary reason>.                             ← protected items (see below)
net: <drop N of M items, reuse X, ~K fewer files/deps>.
```

Nothing to cut → `Lean already. Ship.` If you must explain, ≤3 short lines
*after* the verdict. The judgement is the value; the prose is not.

## When NOT to be lazy (boundaries)

Never cut, and mark these `KEEP` in the verdict: understanding the problem first;
input validation at trust boundaries; error handling that prevents data loss;
security; accessibility; real-hardware calibration; correctness under
async/concurrency (thundering herd, negative caching, races); anything the user
explicitly requested. Non-trivial logic keeps **ONE runnable check** — an
assert-based self-check or one small test file, no frameworks. Trivial
one-liners need no test.

## Output discipline — the carve-out

Minimalism governs **explanatory padding only — never harness-contracted or
user-requested prose.** Always produce in full, never trim as "debt": intake and
plan reports, workpad / continuity notes, Done-Definition statements, commit
`Why:` lines, ADRs / decision records, and anything the user asked for.
"Explanation longer than the code → delete it" applies to padding, never to
these artifacts.

## Deferred shortcuts — reuse, don't invent

A deliberate deferral routes into the harness's **existing** machinery if one is
present: a backlog file, a `[FLEX]` / deviation log, an issue tracker. Only when
none exists, leave a one-line code comment naming the ceiling and the upgrade
path. Do not invent a new marker convention.

## Intensity

- **lite:** build what's asked, but name the lazier alternative in one line.
- **full (default):** enforce the ladder; stdlib/native first; shortest verdict.
- **ultra:** deletion before addition; ship the one-liner and challenge the rest
  of the requirement in the same breath.

## Composition

brainstorming / writing-plans shape intent → harness intake clears scope →
**yagni scores the plan** → implement with rungs 3–7 as the lens → tdd covers
the ONE check.
