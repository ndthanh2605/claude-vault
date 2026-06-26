---
name: goalsmith
description: Use when the user wants to turn a rough idea, vague task, feature wish, or bug-fix intent into a clear, verifiable goal before autonomous or long-running work starts. Use this whenever the user mentions plan mode, /loop, scheduled or recurring agents, "set this running", "let it work on its own", long-running autonomous work, or asks to be interviewed or grilled before kicking off a goal — even if they don't say the word "goal". Forge fuzzy intent into something Claude Code can pursue, verify, and stop on.
metadata:
  dependencies: []
---

# Goalsmith

Forge fuzzy intent into a goal Claude Code can autonomously pursue, verify, and stop on. The
expensive failure mode for any long-running or unattended work isn't bad code — it's the agent
confidently finishing the *wrong* thing, or grinding forever because "done" was never defined. This
skill front-loads the cheap conversation that prevents that.

It borrows the `grill-me` posture — ask one question at a time, recommend an answer, and inspect the
codebase instead of asking when the answer is discoverable — but aims at a concrete artifact: a
verifiable goal plus the right Claude Code hand-off to run it (plan mode, `/loop`, or a scheduled
agent). Claude Code has no Codex-style `/goal` command; the goal is realized through these native
primitives instead.

## The hard gate

A goal isn't ready to run until these six fields are clear enough that a cold agent could pursue it
without guessing. Until then, keep interviewing — do not draft the final goal.

1. **Outcome** — the single truth the user wants made real. One sentence, one thing.
2. **Success condition** — measurable or objectively inspectable proof the outcome is true. "Tests
   X and Y pass", "endpoint returns 200 with field Z", not "it works better".
3. **Scope boundary** — what may change and what must not. The fence that keeps an autonomous run
   from wandering into unrelated files or rewriting things it shouldn't.
4. **Context to read first** — the files, docs, logs, issues, commands, or services the agent
   should load before acting, so it builds on what exists instead of reinventing it.
5. **Validation loop** — the cheap checks to run *during* the work (fast feedback) and the final
   checks that gate the success condition before claiming done.
6. **Stop and pause rules** — when to stop because it's done, and when to pause for a human instead
   of improvising past a decision the user should own.

If a field is missing, ask the single highest-leverage question that fills it. Don't draft around a
hole.

## Interview loop

1. Restate the apparent intent in one sentence and reflect it back. Misreads surface fastest here.
2. Find the weakest missing field from the hard gate.
3. **Inspect before asking.** If the answer is discoverable from local files, the active task/branch
   state, logs, tests, docs, or repo conventions, go find it instead of spending a question on it.
   The user shouldn't have to tell you what the repo already says.
4. Ask exactly one question at a time.
5. With each question, include your recommended answer and why it's probably right — you've been
   reading the code, so lead with a real hypothesis, not a blank prompt.
6. After the answer, update the working goal shape and repeat.

Prefer three sharp questions over ten generic ones. The interview should feel like it's converging,
not interrogating. Stop as soon as the goal is safely draftable — a tight goal beats an exhaustive one.

## Question priority

Ask in this order unless local context shows a different blocker:

1. What should be true at the end?
2. How will we prove it is true?
3. What is explicitly out of scope?
4. What should the agent read or preserve before acting?
5. What checks run repeatedly during the work versus only at the end?
6. What should make the agent pause instead of improvising?
7. What proof should it leave behind for review?

## Anti-vague rewrites

These intents are unrunnable as stated — they have no success condition and no scope fence, so an
autonomous agent can't tell when it's done or whether it's allowed to make a given change. When you
hear one, don't accept it; convert it into a single outcome plus its proof:

- "Improve the app" → "Reduce dashboard initial load by ≥25% with no visible behavior regressions,
  proven by benchmark output before/after and a UI screenshot."
- "Fix all bugs" → "Make the checkout flow pass the currently-failing Playwright suite while keeping
  the passing payment tests green."
- "Make it production ready" → name the specific gates: "all tests pass, no `console.error` on the
  happy path, and the health endpoint returns 200 under the smoke script."
- "Refactor this codebase" → "Extract the duplicated auth/session logic into one shared module,
  preserving every current test and the public API surface."
- "Research this and do the best thing" → split research (a written findings note) from the action,
  and make the action its own goal with its own proof.

The move is always the same: pin the outcome to an inspectable artifact.

## Choose the hand-off

Once the six fields are clear, match the *shape* of the work to a Claude Code primitive, recommend
one, and say why. Let the user override.

- **One-shot, reviewable, this session** → **plan mode**. Render the goal as a plan and hand it to
  `ExitPlanMode` for approval. Best when the work is a bounded change the user wants to review before
  it runs.
- **Iterative until a condition converges** → **`/loop`**. The success condition becomes the loop's
  done-criteria; the agent works, checks, and repeats until it's met or a pause rule fires. Use a
  fixed interval only when there's a natural cadence (polling external state); otherwise let it
  self-pace. Best for "keep going until green" work.
- **Recurring or deferred** → **scheduled agent** (the `schedule` skill / a routine on a cron). Best
  when the goal should run on a timetable or at a future time rather than now.

If it's genuinely ambiguous, default to plan mode — it's the most reviewable and the easiest to
escalate from.

## Goal spec contract

When the gate is satisfied, present the goal in this shape (runtime-agnostic — the hand-off block
below it adapts to the chosen primitive):

```text
Objective: [single outcome]

Context to read first:
- [...]

Constraints (must not change / must preserve):
- [...]

Operating rules:
- Prefer small verified iterations over large unverified edits.
- Keep a concise progress note in [file] if the work is long-running.
- Do not expand scope without pausing.

Validation loop:
- During work: [cheap checks]
- Final proof: [the success condition, concretely]

Done when:
- [...]

Pause if:
- [...]
```

Follow it with a short **Why this is safe to run** note: the success condition, the main risk, and
the proof artifact that will exist at the end. Then render the chosen hand-off concretely — the plan
text for `ExitPlanMode`, the `/loop <spec>` line, or the schedule definition.

## Do not silently start

Drafting the goal is not permission to run it. Never call `ExitPlanMode`, start a `/loop`, or create
a scheduled agent until the user has seen the drafted goal *and* the hand-off and explicitly
confirmed. Present the draft, ask for the go-ahead, and act only on a clear "yes". An autonomous run
is hard to claw back once it's moving — the confirmation is the cheap insurance.

If the user asked only for help *shaping* the goal (not launching it), stop at the draft and don't
offer to start unless they ask.

## Working inside this harness

This skill defers to the project. If the repo's `CLAUDE.md`, `AGENTS.md`, or a story/workpad defines
how work must be planned, validated, or committed, those win over this skill's defaults — fold their
requirements into the goal's context and validation loop rather than overriding them. When already in
plan mode, the plan-mode hand-off *is* `ExitPlanMode`; don't invent a second approval step.
