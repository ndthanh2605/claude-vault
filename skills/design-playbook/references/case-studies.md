# Case-study catalog: anchor to a known design

Condensed pattern-match index. When a prompt resembles one of these, start from its
**signature shape**, then adapt to the stated requirements — don't reinvent it.
Each entry: the shape that defines it + the deep-dive concern(s) it's famous for.
For the concern playbook, see `deep-dive-notes.md`; for the choosers,
`decision-tables.md`.

## Foundational

**Rate limiter** — Counter in Redis (token bucket default) at an API gateway /
middleware. *Deep dive:* algorithm choice (see table); distributed counter races →
Lua/atomic ops; sliding window for accuracy.

**Consistent hashing** — Hash ring + virtual nodes to map keys→nodes with minimal
movement on membership change. *Deep dive:* virtual nodes for balance; used inside
caches, shards, KV stores.

**Key-value store** — Partition (consistent hashing) + replicate (N) + quorum
(`W+R>N`); Cassandra-style write path (commit log → memtable → SSTable). *Deep
dive:* tunable consistency; conflict resolution (vector clocks); failure detection
(gossip), hinted handoff, Merkle-tree anti-entropy. (CAP trade-off lives here.)

**Unique ID generator** — Snowflake: 64-bit time-sortable id, no coordination.
*Deep dive:* clock sync / drift; bit-section sizing.

## Read-heavy / social

**URL shortener** — Write: store `id→longURL`, return base-62 of the id. Read: 301/302
redirect, heavily cached + CDN. *Deep dive:* base-62 vs hash+collision; read-heavy →
cache; key length sizing from estimation.

**News feed** — Write (post) → fanout service. Read (feed) → precomputed, cached.
*Signature:* **hybrid fanout** — push for normal users, pull for celebrities, merge
at read. *Deep dive:* hot key (high-follower), feed caching, pagination.

**Chat system** — WebSocket via stateful chat servers + service discovery; message
store (wide-column, keyed by channel/time); presence via heartbeat. *Deep dive:*
1-to-1 vs group fanout; delivery/ordering; online presence; push for offline.

**Notification system** — Producers → queue → per-channel workers (push/SMS/email)
→ 3rd-party providers. *Signature:* async, decoupled, event-driven. *Deep dive:*
at-least-once + idempotency (dedup), retries, rate limiting, fanout.

**Search autocomplete** — Trie (prefix tree), precomputed top-k per node, cached at
the edge; offline pipeline builds the trie from query logs. *Deep dive:* trie
sharding, update freshness vs cost, ranking.

## Media / storage

**YouTube** — Upload → object storage + transcoding pipeline (queue + workers,
multiple formats/resolutions); playback via CDN + adaptive streaming; metadata DB.
*Deep dive:* transcoding pipeline, CDN strategy, dedup, resumable upload.

**Google Drive** — File store on object storage + metadata DB; client sync with
block-level dedup + delta sync; notification service for changes. *Deep dive:* sync
conflicts, delta/block storage, consistency across devices.

**S3-like object storage** — Data service (immutable objects, replicated/erasure-
coded) + metadata service (bucket/object index); versioning. *Deep dive:* durability
(erasure coding vs replication), consistency, large-object multipart.

## Location

**Proximity service (Yelp-style)** — Geospatial index (geohash or quadtree) over a
business DB; read-heavy → cache hot cells; LBSS computes nearby by cell + radius.
*Deep dive:* geohash vs quadtree trade-off; index granularity; DB scaling + cache.

**Nearby friends** — Real-time location stream over WebSocket; pub/sub by geohash
cell; ephemeral location store (Redis) with TTL. *Deep dive:* update fanout, geohash
cells, scaling pub/sub.

**Google Maps** — Tiled map (precomputed image tiles on CDN by zoom/coords) + routing
service (graph + hierarchical/precomputed shortest path) + location/ETA service.
*Deep dive:* map tiling & projection, routing graph partitioning, ETA via live data.

## Streaming / pipelines

**Distributed message queue** — Partitioned, replicated append-only log; brokers +
coordination service; consumer groups + offsets. *Deep dive:* ordering within
partition, at-least/exactly-once, replication (ISR), retention.

**Metrics monitoring & alerting** — Agents → ingestion → time-series DB; query +
alert engine; visualization. *Signature:* pull or push collection, time-series
store. *Deep dive:* cardinality, downsampling/retention, lambda-style hot+cold.

**Ad click aggregation** — Click stream → message queue → stream aggregation →
aggregated counts store; dashboards query aggregates. *Signature:* **lambda/kappa**
(real-time speed layer + batch reconciliation for exactness). *Deep dive:*
exactly-once counting (idempotent by event id), watermarks/late events, reconciliation.

## Transactions / money

**Hotel reservation** — Inventory + reservation services on a SQL store with
transactions; idempotent booking. *Deep dive:* double-booking prevention
(constraints/locking/optimistic concurrency), strong consistency, overbooking
policy.

**Payment system** — Payment service + ledger (double-entry) + external PSP
integration via async events; reconciliation. *Signature:* strong consistency,
event-driven. *Deep dive:* idempotency (no double charge), exactly-once with PSPs,
reconciliation, failure recovery (saga).

**Digital wallet** — Account ledger with strong consistency; often **event sourcing
+ CQRS** for an auditable balance; distributed transactions across accounts. *Deep
dive:* exactly-once transfers, double-entry, audit trail, saga/2PC trade-offs.

**Stock exchange** — Matching engine (in-memory, single-threaded per symbol for
deterministic ordering) + sequencer + order/market-data gateways; event-sourced for
replay. *Deep dive:* ultra-low latency, deterministic ordering, fault tolerance via
event replay, market-data fanout.

## Distributed email service

**Email service** — Inbound/outbound mail gateways (SMTP) + queue; metadata store +
object storage for bodies/attachments; search index. *Deep dive:* huge storage,
search at scale, consistency of folder/metadata, spam handling.
