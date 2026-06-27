# Estimation: back-of-the-envelope numbers

Numbers drive architecture. QPS sizes the compute tier; storage/year sizes the DB
and the sharding story; bandwidth sizes the CDN. Be fast and approximate — the
*process* and the order of magnitude matter, not precision.

## How to estimate (the recipe)

1. **State assumptions** (DAU, actions/user/day, payload size, read:write ratio,
   retention). Write them down — they're the audit trail.
2. **QPS** = `daily_actions / 86,400`. Round 86,400 to ~10⁵.
   **Peak QPS** ≈ 2× average (rule of thumb).
3. **Storage/day** = `writes/day × payload size`. Multiply by retention (×365 ×
   years) for total.
4. **Bandwidth** = `QPS × payload`. Split read vs write.
5. **Memory for cache** = hot dataset × (e.g. 20% by the 80/20 rule).
6. **Label every unit, round aggressively.** `99,987 / 9.1 ≈ 100,000 / 10 = 10,000`.

## Powers of two (data volume)

| Power | Approx | Name |
|-------|--------|------|
| 2¹⁰ | 1 thousand | 1 KB |
| 2²⁰ | 1 million | 1 MB |
| 2³⁰ | 1 billion | 1 GB |
| 2⁴⁰ | 1 trillion | 1 TB |
| 2⁵⁰ | 1 quadrillion | 1 PB |

## Latency numbers every engineer should know

| Operation | Latency |
|-----------|---------|
| L1 cache reference | 0.5 ns |
| L2 cache reference | 7 ns |
| Main memory reference | 100 ns |
| SSD random read | ~150 µs |
| Round trip within a data center | ~500 µs |
| HDD seek | ~10 ms |
| Round trip between regions (e.g. CA↔Netherlands) | ~150 ms |

**Takeaways:** memory is fast, disk is slow, avoid disk seeks, keep hot data in
RAM, compress before sending over the network, cross-region calls are expensive
(co-locate or cache at the edge).

## Availability ("nines") — downtime per year

| Availability | Downtime/year |
|--------------|---------------|
| 99% (two nines) | ~3.65 days |
| 99.9% (three nines) | ~8.8 hours |
| 99.99% (four nines) | ~52 minutes |
| 99.999% (five nines) | ~5.3 minutes |
| 99.9999% (six nines) | ~32 seconds |

Most cloud SLAs target ≥ 99.9%. More nines ⇒ exponentially more cost and
redundancy — match the target to the business need.

## Worked example (Twitter-style)

Assume 300M MAU, 50% daily active ⇒ 150M DAU; each posts twice/day; read:write ~
100:1; tweet ~ a few hundred bytes plus optional media.

- Write QPS = `150M × 2 / 86,400` ≈ **3,500 writes/s**; peak ≈ **7,000/s**.
- Read QPS ≈ 100× ⇒ **~350K reads/s** → screams "cache + read replicas + fanout".
- Storage (text, 5 yr) = `150M × 2 × ~300 B × 365 × 5` ≈ tens of TB → shard.
- The read:write ratio alone tells you this is a read-optimization problem
  (precompute/fanout, cache, CDN) — that's the architectural payoff of estimating.
