# Framework: the 4-step interview process

The spine lives in SKILL.md. This file is the detail for **Step 1** (and the
process discipline) — the part people most often rush.

## Time budget (45-min interview)

| Step | Time | Goal |
|------|------|------|
| 1. Clarify scope | 3–10 min | Agree what's in/out, scale, NFRs |
| 2. Estimate | 10–15 min | Numbers that size the system |
| 3. High-level design | 10–15 min | Components + dataflow, get buy-in |
| 4. Deep dive | 10–15 min | Attack 2–3 bottlenecks |
| Wrap-up | 3–5 min | Recap, trade-offs, what's next |

If a step runs long, cut depth, not the step. Skipping clarification is the most
expensive mistake — you can design the wrong system flawlessly.

## Step 1 clarifying questions (ask the ones that change the design)

**Functional scope**
- What are the core features? Which are explicitly *out* of scope for now?
- Who are the actors (end users, internal services, admins)?
- What's the single most important user journey?

**Scale & traffic**
- DAU / MAU? Expected QPS (and peak vs average)?
- Read-heavy or write-heavy? What ratio?
- Payload sizes (a tweet vs a 4K video)? Data retention?
- Growth — design for today's scale or 10×?

**Non-functional**
- Latency target (p99)? Is this interactive or batch?
- Consistency need: is stale data acceptable, or must reads see the latest write?
- Availability target (how many nines)? Durability (can we ever lose data)?
- Geographic distribution — single region or global?

**Constraints**
- Existing tech/infra to reuse? Build vs buy?
- Security/compliance (PII, PCI, GDPR)?

> Don't interrogate. Ask the 3–5 questions whose answers fork the architecture,
> state your assumptions for the rest ("I'll assume 100M DAU, read-heavy 100:1"),
> and move on.

## Dos

- **Drive the conversation.** Propose, then validate. Silence reads as being stuck.
- **Think out loud.** The reasoning is the signal, not the final box-diagram.
- **Lead with requirements.** Every design choice should trace back to an NFR.
- **Start simple, then scale.** A single-server version first makes the scaling
  story legible.
- **Call out trade-offs explicitly.** "I'm choosing availability over consistency
  here because a stale feed is fine but downtime isn't."
- **Manage time.** Get to a complete high-level design before deep-diving anything.

## Don'ts

- Don't jump to a solution before scoping the problem.
- Don't over-engineer — no Kafka/Kubernetes/microservices reflex without a reason.
- Don't get stuck perfecting one component while the rest is undesigned.
- Don't bluff specifics you don't know; reason from principles instead.
- Don't ignore the interviewer's hints — they're steering you toward the gold.

## The "start simple, then scale" ladder

A reliable way to structure Step 3 when scale is the theme: begin single-server,
then introduce each piece *because a number forced it*:

1. Single server (web + DB together)
2. Separate the DB tier
3. Add a load balancer + multiple stateless web servers
4. DB replication (leader/follower) for read scaling & failover
5. Add a cache for hot reads; a CDN for static/media
6. Make the web tier stateless (sessions in a shared store)
7. Multi-data-center for geo latency & DR
8. Message queue to decouple async work
9. Shard the database when one box can't hold the data/writes

Each rung is a response to a bottleneck — narrate the *why*, not just the *what*.
