---
name: design-playbook
description: >-
  Coaches a system-design problem to the right high-level architecture using a
  disciplined 4-step interview framework (clarify scope → estimate → high-level
  design → flag deep-dive concerns). Use this whenever the user is doing system
  design or design-interview prep — "design X at scale", "how would you build
  <Twitter/Uber/Dropbox/a chat app/a rate limiter>", "system design interview",
  "design the architecture for...", or asks which database / queue / caching /
  fanout / sharding / consistency approach fits a large-scale system. Trigger
  even when the user doesn't say the word "interview": any request to architect a
  scalable system from scratch is in scope. It DELIBERATELY stops at a clean
  high-level design plus a checklist of deep-dive concerns — it does not over-build
  a fully-specified low-level design unless explicitly asked.
---

# design-playbook

A system-design coach. It takes a vague prompt ("design Twitter") and drives it,
step by step, to a defensible **high-level design** — the right components, data
flow, and storage choices — then hands off a short list of **deep-dive concerns**
for the low-level phase.

## Operating principle: keep altitude

The failure mode in system design is going deep too early — debating a schema
before the components are agreed, or naming a specific Kafka config before anyone
knows if a queue is even needed. **Breadth before depth.** Land the high-level
shape first, get buy-in, *then* zoom in on one or two bottlenecks. This skill's job
is to enforce that altitude, not to dump every detail you know.

The other failure mode is restating textbook definitions. The user knows what a
cache is. Your value is **judgment**: which option fits *these* requirements and
why — the trade-off, not the dictionary.

## The 4-step flow

Run these in order. Don't skip step 1, and don't let any one step eat the clock
(rough budget for a 45-min interview: 3–10 min / 10–15 min / 10–15 min / 3–5 min).

### Step 1 — Clarify scope & requirements (don't design yet)

Pin down *what* you're building before *how*. Ask the questions that change the
design; assume the rest out loud and move on.

- **Functional**: the 2–4 core features in scope. Aggressively narrow — "feed +
  posting, not DMs or ads."
- **Non-functional**: scale (DAU, QPS, payload size, read/write ratio), latency
  target, consistency vs availability, durability.
- **Constraints**: existing infra, team, budget, anything fixed.

State the assumptions you're locking in. → For the canonical question checklist
and time management, read `references/framework.md`.

### Step 2 — Back-of-the-envelope estimate

Numbers decide architecture: QPS sizes the compute tier, storage/year sizes the DB
and sharding story, bandwidth sizes the CDN. Do the rough math — round
aggressively, label units, write assumptions.

→ For the formulas, latency/availability numbers, and powers-of-two, read
`references/estimation.md`. Don't reproduce the whole table from memory; pull what
the problem needs.

### Step 3 — High-level design (the core deliverable)

Produce a clean component diagram and the request/data flow through it. Aim for:
client → entry (LB/API gateway) → service(s) → storage, plus the async paths
(queues, workers) and read paths (cache, CDN). Describe it as a **text/ASCII
diagram or a component + dataflow list** — topology must be legible, not buried in
prose.

The decisions that define the shape:

- **Architecture style** — monolith vs microservices vs event-driven, etc. →
  `references/architecture-styles.md`.
- **Storage & access** — SQL vs NoSQL, push vs pull, sync vs async, which protocol,
  which consistency. This is where most designs are won or lost. →
  `references/decision-tables.md` is the chooser; consult it by name.
- **Building blocks** — when to add a cache / CDN / queue / shard / consistent
  hashing and the cost of each. → `references/building-blocks.md`.

If the problem resembles a classic (URL shortener, news feed, chat, rate limiter,
maps, payments…), anchor to its known shape first, then adapt. →
`references/case-studies.md` is a fast pattern-match catalog.

**Get buy-in.** Present the high-level design and confirm direction before going
deeper. Then stop expanding breadth.

### Step 4 — Flag deep-dive concerns (the hand-off)

Don't try to solve everything. Name the 2–3 places this specific design will hurt
at scale and *how you'd attack them* — sharding/hotspots, consistency & quorum,
idempotency/exactly-once, cache invalidation, fanout, backpressure, failure &
replication. A crisp list of the right concerns beats a half-built solution.

→ `references/deep-dive-notes.md` is the checklist of concerns + the standard
move for each. Use it to pick the few that matter here, not to enumerate all.

## Wrap-up

Recap the design in a few sentences, restate the key trade-offs you made and why,
and note what you'd revisit with more time. Tie it back to the requirements from
step 1.

## Reference map

| File | When to open it |
|------|-----------------|
| `references/framework.md` | Step 1 — clarifying questions, dos/don'ts, time budget |
| `references/estimation.md` | Step 2 — numbers, formulas, latency/availability |
| `references/architecture-styles.md` | Step 3 — picking the overall shape |
| `references/decision-tables.md` | Step 3 — SQL/NoSQL, push/pull, protocol, consistency choosers |
| `references/building-blocks.md` | Step 3 — when/why to add each component |
| `references/case-studies.md` | Step 3 — anchor to a known design |
| `references/deep-dive-notes.md` | Step 4 — the concern checklist + standard fixes |

Load a reference only when the step calls for it. Keep the conversation at the
high-level until step 4.
