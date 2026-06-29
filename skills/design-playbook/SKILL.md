---
name: design-playbook
description: >-
  A process coach for system design. It does NOT teach facts (you already know
  what a cache or a shard is) — it enforces the *workflow*: a 4-step framework,
  the right altitude (breadth before depth, stop at high-level), mandatory
  trade-off articulation, and clean output templates. Use this whenever the user
  is doing system design or design-interview prep — "design X at scale", "how
  would you build <Twitter/Uber/Dropbox/a chat app/a rate limiter>", "system
  design interview", "design the architecture for...", or asks which database /
  queue / caching / fanout / sharding / consistency approach fits a large-scale
  system. Trigger even when the user doesn't say "interview": any request to
  architect a scalable system from scratch is in scope. It DELIBERATELY stops at
  a clean high-level design plus a checklist of deep-dive concerns — it does not
  over-build a fully-specified low-level design (schemas, exact configs, code)
  unless explicitly asked.
---

# design-playbook

A **process** for turning a vague prompt ("design Twitter") into a defensible
**high-level design**, then handing off a short list of deep-dive concerns. This
skill is intentionally knowledge-free — your training already has the facts. Its
only job is to make you *work* like a strong designer, not to tell you things you
know.

## Three rules that define a good answer

1. **Keep altitude — breadth before depth.** The failure mode is going deep too
   early (debating a schema before the components exist, naming a Kafka config
   before anyone knows a queue is needed). Land the full high-level shape first,
   get buy-in, *then* zoom into one or two bottlenecks. Stop at high-level +
   flagged concerns; do not produce schemas, exact commands, or config tuning
   unless asked.

2. **Articulate every major trade-off.** A decision without a stated alternative
   is a guess. For each significant choice, say it in this shape:

   > **Chose** <option> over <alternative> because <reason tied to a requirement>;
   > the cost is <what you give up>.

   This is the single highest-value habit — do it for storage, consistency,
   fanout, sync/async, and protocol choices every time.

3. **Trace every choice back to a requirement.** No component without a number or
   an NFR that justifies it. "We added read replicas because reads are 100× writes
   at 350K QPS" — good. "We added Kafka because it's modern" — cut it.

## The 4-step workflow

Run in order. Budget for a 45-min interview: ~5 / ~12 / ~13 / ~12 min + wrap-up.

### Step 1 — Clarify scope (don't design yet)

Ask only the questions whose answers fork the design; state assumptions for the
rest and move on. Cover these four buckets:

- **Functional**: the 2–4 core features in scope — and what's explicitly *out*.
- **Scale**: DAU/QPS (avg & peak), read:write ratio, payload size, retention.
- **NFRs**: latency target (p99), consistency vs availability, durability, geo.
- **Constraints**: existing infra, build-vs-buy, compliance.

Close the step by stating the locked assumptions out loud.

### Step 2 — Size it (numbers drive architecture)

Do rough back-of-the-envelope math — it's what *justifies* the design. Round
hard, label units. The numbers that matter:

- **QPS** = daily actions / ~10⁵; peak ≈ 2× average → sizes the compute tier.
- **Storage/year** = writes/day × payload × 365 → decides if you must shard.
- **Read:write ratio** → decides cache/replica/precompute strategy.
- **Bandwidth** = QPS × payload → decides CDN.

Don't recite latency tables from memory unless a number is load-bearing for a
decision. Compute only what changes the design.

### Step 3 — High-level design (the core deliverable)

Produce a legible component diagram + the request/data flow. Use this template,
not prose:

```
HIGH-LEVEL DESIGN
Components: <list: client, LB/gateway, services, stores, cache, CDN, queue/workers>
Write path: <step → step → step>
Read path:  <step → step → step>
Async path: <what goes through the queue and why>
Storage:    <store → what it holds → why this store (trade-off)>
```

The decisions that define the shape — make each with the trade-off template from
Rule 2: architecture style, storage engine, consistency level, fanout strategy,
client↔server protocol, and which building blocks (cache/CDN/queue/shard) you add
and why. For the opinionated defaults that steer these, read
`references/heuristics.md`.

**Get buy-in**, then stop expanding breadth.

### Step 4 — Flag deep-dive concerns (the hand-off)

Don't solve everything. Name the **2–3 places this design will hurt at scale** and
the standard move for each. Use this template:

```
DEEP-DIVE CONCERNS
1. <concern> → <standard move>
2. <concern> → <standard move>
3. <concern> → <standard move>
```

Typical concerns to pick from (choose the ones that bite *this* design, don't
enumerate all): hot keys/sharding, consistency & quorum, idempotency/exactly-once,
cache invalidation, fanout amplification, backpressure/overload, failure &
replication, geo-latency. Go one level deeper on the 1–2 most impactful; name the
rest.

## Wrap-up

Recap the design in a few sentences, restate the key trade-offs and *why*, note
what you'd revisit with more time. Tie it back to Step 1's requirements.

## Anti-patterns (stop if you catch yourself here)

- Designing before scoping; skipping the clarifying questions.
- Reaching for microservices / Kafka / a NoSQL store by reflex, no requirement.
- Perfecting one component while the rest is undesigned.
- Stating a choice with no alternative and no cost (breaks Rule 2).
- Drifting into schemas / exact commands / config tuning at high-level (breaks
  Rule 1) — that's the low-level phase, and only if asked.
- Reciting definitions of well-known components — the user knows them.

## Reference

| File | When |
|------|------|
| `references/heuristics.md` | Step 3 — opinionated default choices (storage, consistency, fanout, protocol, scaling order) |
