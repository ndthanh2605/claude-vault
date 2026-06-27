# Decision tables: the chooser

The engine that steers a problem to the right high-level design. Each section is a
**comparison** plus a **decision rule**. Pick by requirement, and say the trade-off
out loud.

## SQL vs NoSQL

| | SQL (relational) | NoSQL |
|---|---|---|
| Data | Structured, relational | Unstructured/semi, denormalized |
| Schema | Fixed, enforced | Flexible |
| Consistency | Strong (ACID) | Often eventual (BASE), tunable |
| Joins / transactions | First-class | Limited / app-side |
| Scale | Vertical first; sharding is work | Horizontal by design |
| Query | Rich, ad-hoc (SQL) | Access-pattern-specific |

**Choose NoSQL when:** super-low latency, huge volume, unstructured or
schema-flexible data, no complex joins, or you mainly serialize/deserialize blobs.
**Choose SQL when:** strong consistency / multi-row transactions, complex queries
and relationships, or moderate scale. **Default to SQL** unless a requirement
pushes you off it.

### NoSQL family — pick by access pattern

| Type | Shape | Use when | Examples |
|------|-------|----------|----------|
| Key-Value | hash by key | simple get/put by id, sessions, caches | Redis, DynamoDB |
| Wide-column | rows of sparse columns | write-heavy, time-series, huge scale | Cassandra, Bigtable |
| Document | JSON docs | flexible nested objects, per-doc queries | MongoDB |
| Graph | nodes + edges | relationship traversal (social, fraud) | Neo4j |

## Consistency: strong vs eventual

- **Strong** — every read sees the latest write. Needed for money, inventory,
  uniqueness (no double-spend, no double-booking). Costs latency/availability under
  partition (CP side of CAP).
- **Eventual** — replicas converge over time; reads may be stale. Fine for feeds,
  likes, view counts, timelines. Buys availability and low latency (AP side).
- **Rule:** default to the weakest consistency the product can tolerate; reserve
  strong consistency for the few operations that truly need it.
- **Tunable (quorum):** with N replicas, `W + R > N` gives read-your-writes.
  `W=N` favors read-heavy; `R=1,W=N` and vice-versa trade read vs write latency.

## Fanout: push vs pull (feeds, timelines, notifications)

| | Push (fanout-on-write) | Pull (fanout-on-read) |
|---|---|---|
| When | precompute each follower's feed at post time | assemble feed at read time |
| Read latency | very low (feed is ready) | higher (gather + merge) |
| Write cost | high (1 write × N followers) | low |
| Best for | normal users, read-heavy | celebrities / huge fanout |
| Problem | "hot key" for users with millions of followers | slow reads, repeated work |

**Standard answer:** *hybrid* — push for most users, pull for high-follower
accounts, merge at read time. See `case-studies.md` → News Feed.

## Client ↔ server communication

| Mechanism | Direction | Use when |
|-----------|-----------|----------|
| Short polling | client pulls on a timer | simple, low-freq updates; wastes requests |
| Long polling | client holds request open | near-real-time, moderate scale |
| SSE | server → client, one-way stream | server push, no client→server needed (feeds) |
| WebSocket | full duplex, persistent | bidirectional real-time (chat, gaming, presence) |

**Rule:** pick the lightest that meets the latency need. WebSocket only when you
genuinely need bidirectional/persistent; SSE for one-way push; long-poll for
occasional updates.

## API style: REST vs gRPC vs GraphQL

- **REST** — default for public/external APIs, cacheable, simple.
- **gRPC** — internal service-to-service, low latency, streaming, strict contracts
  (protobuf). Not browser-native.
- **GraphQL** — client-shaped queries, avoids over/under-fetching; great for
  aggregating many backends for varied clients (mobile + web). Costs caching
  simplicity and adds query-complexity concerns.

## Sync vs async processing

- **Sync** — caller waits; use when the result is needed now and the work is fast.
- **Async (queue + workers)** — use for slow, bursty, retryable, or
  fire-and-forget work (encoding video, sending notifications, aggregations).
  Decouples producer from consumer, absorbs spikes, enables retries. Costs:
  eventual completion, ordering/idempotency concerns.

## Rate-limiting algorithms (quick reference)

| Algorithm | Pro | Con |
|-----------|-----|-----|
| Token bucket | allows bursts, simple, common | two params to tune |
| Leaking bucket | smooth, stable outflow | bursts get delayed |
| Fixed window | memory-light, easy | edge-of-window burst (2× at boundary) |
| Sliding window log | accurate | high memory (stores timestamps) |
| Sliding window counter | good accuracy/memory balance | approximate |

## Unique-ID generation (distributed)

| Approach | Pro | Con |
|----------|-----|-----|
| Multi-master auto-increment | DB-native | hard to scale, gaps, not k-sortable |
| UUID v4 | no coordination, simple | 128-bit, not time-sortable, not numeric |
| Ticket server (central counter) | numeric, small | SPOF, scaling bottleneck |
| **Snowflake** | 64-bit, time-sortable, decentralized | needs clock sync |

**Snowflake layout (64 bits):** 1 sign + 41 timestamp (ms since custom epoch) + 5
datacenter + 5 machine + 12 sequence. Time-ordered, ~4096 ids/ms/node, no central
coordination. Default answer for distributed, sortable IDs; watch clock drift.
