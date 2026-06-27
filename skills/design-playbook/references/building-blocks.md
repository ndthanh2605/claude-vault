# Building blocks: when (and why) to add each

You know what these are. This is *when to reach for one*, what it buys, and what it
costs — so you add components because a requirement demands it, not by reflex.

## Load balancer

- **Add when:** more than one server in a tier (which is ~always at scale).
- **Buys:** horizontal scale, no single point of failure, health-checked failover.
- **Watch:** the LB itself needs redundancy; algorithm choice (round-robin vs least-
  connections vs consistent-hash for stickiness).

## Cache (in-memory, e.g. Redis/Memcached)

- **Add when:** read-heavy, repeated reads of the same hot data, expensive queries.
  The 80/20 rule: a small hot set serves most reads.
- **Buys:** big latency drop, offloads the DB.
- **Watch:** invalidation (the hard part — see `deep-dive-notes.md`), TTLs,
  cache-aside vs write-through, cold-start/thundering-herd, consistency with the DB.

## CDN

- **Add when:** static assets or media served to a geographically spread audience.
- **Buys:** edge latency, origin offload, bandwidth savings.
- **Watch:** cache TTL/invalidation, cost, dynamic content isn't a fit.

## Database replication (leader–follower)

- **Add when:** read scaling and/or high availability for the DB tier.
- **Buys:** reads scale across followers; failover if the leader dies; better
  durability.
- **Watch:** replication lag ⇒ stale reads (route read-your-writes to leader);
  leader is still the write bottleneck; failover/promotion logic.

## Sharding / partitioning

- **Add when:** one DB box can't hold the data or absorb the write throughput.
- **Buys:** horizontal write + storage scale.
- **Watch:** choosing a shard key (even distribution, avoids hotspots), cross-shard
  queries and joins, resharding, celebrity/hot-key skew. See `deep-dive-notes.md`.

## Consistent hashing

- **Add when:** distributing keys across a changing set of nodes (caches, shards,
  KV stores) and you want minimal reshuffling when nodes join/leave.
- **Buys:** only `k/n` keys move on membership change (vs everything with `mod n`);
  virtual nodes smooth out load.
- **Watch:** added complexity; only worth it when the node set actually changes.

## Message queue / event log

- **Add when:** decoupling producers from consumers, absorbing spikes, async/retryable
  work, fan-out to multiple consumers.
- **Buys:** elasticity, resilience (retries), independent scaling of producer and
  consumer.
- **Watch:** ordering, at-least-once vs exactly-once delivery, idempotent consumers,
  backpressure, dead-letter handling.

## API gateway

- **Add when:** microservices — a single entry point for routing, auth, rate
  limiting, TLS termination, aggregation.
- **Buys:** cross-cutting concerns in one place; clients don't know the topology.
- **Watch:** can become a bottleneck/SPOF; keep it stateless and replicated.

## Stateless web tier + shared session store

- **Add when:** you need any web server to handle any request (so the LB can route
  freely and you can autoscale).
- **Buys:** trivial horizontal scaling, resilience to node loss.
- **Watch:** push session/state out to a shared store (Redis) or make requests
  self-contained (tokens).

## Object storage (S3-like)

- **Add when:** large blobs/media/backups — anything you'd never put in a row.
- **Buys:** cheap, durable, virtually unlimited; pairs with a CDN.
- **Watch:** eventual consistency on some ops, metadata indexing lives elsewhere.
