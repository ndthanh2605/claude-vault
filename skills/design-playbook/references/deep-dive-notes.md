# Deep-dive notes: the Step-4 concern checklist

The high-level design is agreed. Don't solve everything — pick the **2–3 concerns
this specific design will actually hurt on** and show the standard move for each.
This is a menu to choose from, not a list to exhaust.

## Sharding & hot keys

- **Concern:** one shard/key takes disproportionate load (celebrity user, popular
  product, trending hashtag).
- **Standard moves:** choose a high-cardinality, evenly-distributed shard key;
  consistent hashing + virtual nodes; split/replicate hot keys; add a cache layer in
  front; for celebrities use the pull side of a hybrid fanout.

## Consistency & replication

- **Concern:** stale reads, lost updates, conflicting writes across replicas.
- **Standard moves:** route read-your-writes to the leader; quorum (`W+R>N`) for
  tunable consistency; version vectors / last-write-wins / CRDTs for conflict
  resolution; read-repair and anti-entropy (Merkle trees) to converge replicas.

## Idempotency & exactly-once

- **Concern:** retries and at-least-once queues cause duplicate effects (double
  charge, double notification).
- **Standard moves:** idempotency keys (dedup on a unique request id); make
  consumers idempotent; outbox pattern for reliable publish; dedup store/window;
  treat "exactly-once" as "at-least-once + idempotent."

## Cache invalidation & coherence

- **Concern:** cache serves stale data, or the DB and cache disagree.
- **Standard moves:** TTLs; cache-aside with explicit invalidation on write;
  write-through/write-back where appropriate; versioned keys; guard against
  thundering herd (request coalescing, jittered TTLs, early refresh).

## Fanout & feed delivery

- **Concern:** write amplification on push, slow assembly on pull.
- **Standard moves:** hybrid push/pull (push for normal users, pull for high-fanout
  accounts); precompute and cache feeds; paginate; merge at read time.

## Backpressure & overload

- **Concern:** a burst overwhelms a downstream tier.
- **Standard moves:** queue + bounded buffers; rate limiting / load shedding;
  autoscaling on queue depth; circuit breakers; graceful degradation (serve cached
  or partial results).

## Failure handling & availability

- **Concern:** node/DC failures, partial failures, cascading outages.
- **Standard moves:** replication + automated failover; multi-AZ/region with
  health-checked routing; retries with exponential backoff + jitter; circuit
  breakers; timeouts everywhere; gossip + heartbeat for failure detection; hinted
  handoff for temporary node loss.

## Geo-distribution & latency

- **Concern:** global users, cross-region round trips are ~150 ms.
- **Standard moves:** CDN/edge for static + cacheable; regional replicas; geo-DNS /
  geo-routing; data locality (keep a user's data near them); accept eventual
  consistency across regions.

## Geospatial indexing (location/proximity systems)

- **Concern:** "find things near me" efficiently.
- **Standard moves:** geohash (prefix = proximity, easy range scans) or quadtree
  (adaptive density); index in the DB; cache hot cells. See `case-studies.md` →
  Proximity, Maps, Nearby Friends.

## Time-series & high-volume aggregation

- **Concern:** counting/aggregating massive event streams (clicks, metrics) at scale.
- **Standard moves:** stream processing + pre-aggregation; lambda (batch + speed) or
  kappa (stream-only) architecture; columnar/time-series store; idempotent
  aggregation keyed by event id; reconciliation/back-correction for exactness.

## Security & correctness for money

- **Concern:** double-spend, race conditions, audit.
- **Standard moves:** strong consistency / transactions on the ledger; idempotency
  keys; double-entry bookkeeping; event sourcing for an immutable audit trail;
  reconciliation jobs. See `case-studies.md` → Payment, Digital Wallet.
