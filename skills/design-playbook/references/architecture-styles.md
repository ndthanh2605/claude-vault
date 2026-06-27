# Architecture styles: pick the overall shape

This is the highest-altitude decision in Step 3 — it frames everything below it.
Each style below is given as **when it fits / what it costs / who uses it**. Don't
default to microservices; most designs start simpler and earn complexity.

## Quick chooser

```
Single team, early product, unclear domain boundaries?     → Modular monolith
Independent scaling/deploy per domain, many teams?         → Microservices
Workflows driven by things-that-happened, loose coupling?  → Event-driven / pub-sub
Reads and writes have wildly different shapes/scale?        → CQRS
Need full audit trail / time-travel / replay?              → Event sourcing
High-volume analytics, both real-time + accurate batch?    → Lambda / Kappa
```

## Layered monolith / modular monolith

- **Fits:** new products, small teams, domains still in flux, low operational
  budget. One deployable, in-process calls, one database.
- **Costs:** scales as a unit; a hot path forces you to scale everything; large
  codebases get tangled without module discipline.
- **Note:** "monolith first" is usually right. A *modular* monolith (clear internal
  boundaries) lets you split into services later without a rewrite.

## Microservices

- **Fits:** large orgs, independent team ownership, components with very different
  scaling profiles or release cadences.
- **Costs:** distributed-systems tax — network failures, partial failures, data
  consistency across services, observability, deployment complexity. Don't adopt
  for a problem a monolith handles fine.
- **Implies:** an API gateway, service discovery, per-service datastores (no shared
  DB), and a story for cross-service transactions (saga / outbox).

## Event-driven & pub/sub

- **Fits:** decoupling producers from consumers, fan-out to many subscribers,
  smoothing bursty load, async workflows (notifications, feeds, pipelines).
- **Mechanics:** producers emit events to a broker (queue/log); consumers react
  independently. Adds buffering, retries, and elasticity.
- **Costs:** eventual consistency, harder end-to-end tracing, message
  ordering/duplication concerns (see `deep-dive-notes.md` on idempotency).

## CQRS (Command Query Responsibility Segregation)

- **Fits:** read and write workloads diverge sharply — e.g. a write model that's
  normalized/transactional and read models that are denormalized/precomputed for
  fast queries (news feed, dashboards).
- **Costs:** two models to keep in sync (usually via events), eventual consistency
  between write and read sides. Overkill when reads and writes are symmetric.

## Event sourcing

- **Fits:** systems where the *log of changes is the source of truth* and you need
  audit, replay, or temporal queries — ledgers, wallets, payments.
- **Costs:** rebuilding state from events, schema/versioning of events, snapshots
  for performance. Often paired with CQRS. See `case-studies.md` → Digital Wallet.

## Lambda vs Kappa (big-data processing)

- **Lambda:** parallel **batch** (accurate, slow) + **speed/stream** (fast,
  approximate) layers, merged at query time. Fits when you need both real-time
  estimates and later-corrected exact numbers (ad-click aggregation, metrics).
- **Kappa:** a single **stream** path; reprocess by replaying the log. Simpler, no
  dual codebase, but reprocessing large history is the cost.
- See `case-studies.md` → Ad Click Aggregation, Metrics Monitoring.

## Picking under pressure

Start with the simplest style that meets the NFRs, then justify each step up the
complexity ladder with a concrete requirement. "We split X into a service because
it needs to scale 50× independently and deploy daily" — good. "Microservices
because that's modern" — bad.
