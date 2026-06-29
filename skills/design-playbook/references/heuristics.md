# Heuristics: opinionated defaults

Not a knowledge dump — you know the facts. These are *default stances* to steer a
choice fast, plus the trigger that overrides each default. State the trade-off
(SKILL.md Rule 2) whenever you deviate.

## Storage engine

- **Default: SQL.** Pick it unless a requirement pushes you off.
- **Switch to NoSQL when:** need super-low latency at huge volume, schema-flexible
  / unstructured data, no complex joins, or mostly blob get/put.
- **NoSQL family by access pattern:** simple get/put by key → key-value (Redis,
  DynamoDB); write-heavy time-series at scale → wide-column (Cassandra, Bigtable);
  flexible nested docs → document (Mongo); relationship traversal → graph.
- **Large blobs/media** never go in a row → object storage + CDN.

## Consistency

- **Default: the weakest the product tolerates.** Stale feeds/likes/counts are
  fine → eventual, buy availability + latency.
- **Use strong consistency only for:** money, inventory, uniqueness, booking — the
  few ops where a stale read causes a real error.
- **Tunable:** quorum `W + R > N` for read-your-writes; `W=N` favors read-heavy.

## Fanout (feeds, timelines, notifications)

- **Default: push (fanout-on-write)** — precompute each follower's feed; fast reads.
- **Switch to pull for high-fanout accounts** (celebrities) to avoid write
  amplification; merge at read time.
- **The expected answer is hybrid:** push for normal users, pull for the few huge
  accounts.

## Client ↔ server communication

- **Use the lightest mechanism that meets the latency need**, in this order:
  short poll → long poll → SSE (one-way server push) → WebSocket (bidirectional,
  persistent). Only reach for WebSocket when you truly need duplex/persistent
  (chat, gaming, presence).

## API style

- **External/public** → REST (simple, cacheable).
- **Internal service-to-service** → gRPC (low latency, streaming, contracts).
- **Many backends, varied clients** → GraphQL (client-shaped queries), accepting
  caching complexity.

## Architecture style

- **Default: modular monolith.** "Monolith first" — earn microservices with a
  concrete need (independent scaling/deploy, team ownership), not by fashion.
- **Event-driven / pub-sub** when decoupling producers from consumers, fan-out, or
  smoothing bursty load.
- **CQRS** when read and write shapes diverge sharply; **event sourcing** when the
  change log must be the source of truth (ledgers, wallets, audit).
- **Lambda vs Kappa** for high-volume aggregation: lambda = batch + speed layers
  (real-time estimate, batch-corrected exactness); kappa = stream-only, replay to
  reprocess.

## Sync vs async

- **Sync** when the result is needed now and the work is fast.
- **Async (queue + workers)** for slow, bursty, retryable, or fire-and-forget work
  (encoding, notifications, aggregation). Buys elasticity + retries; costs eventual
  completion + ordering/idempotency concerns.

## The scaling ladder (Step 3 when scale is the theme)

Introduce each rung *because a number forced it*, narrating the why:

1. Single server → 2. Split DB tier → 3. LB + multiple stateless web servers →
4. DB replication (read scaling + failover) → 5. Cache hot reads + CDN for static
→ 6. Stateless web tier (shared session store) → 7. Shard the DB when one box
can't hold the data/writes → 8. Message queue to decouple async work →
9. Multi-data-center for geo latency + DR.

## When to add each building block (one-line triggers)

- **Cache** — read-heavy, hot data repeated, expensive queries. Watch invalidation.
- **CDN** — static/media to a geo-spread audience.
- **Read replicas** — scale reads + HA; watch replication lag (route
  read-your-writes to leader).
- **Shard** — one box can't hold data/write throughput; the hard part is the shard
  key (even distribution, no hot keys).
- **Consistent hashing** — distributing keys over a *changing* node set with minimal
  reshuffle; only worth it when membership actually changes.
- **Queue** — decouple, absorb spikes, retryable/async work.
- **API gateway** — microservices entry point for routing/auth/rate-limit.
