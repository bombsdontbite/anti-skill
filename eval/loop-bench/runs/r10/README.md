# Run 10: v2.5 (the awkward-input check narrowed to failures, fixed with the smallest change)

`candidate/SKILL.md` is v2.5 as tested, revised after a fresh review. Held-out on run 2's
seed on an idle machine, interleaved with earlier finals (five scorings for dedup and speedup,
three for tsp, one for cache). Every v2.5 final passes the stress split.

| task | v2.5 | v2.4 (r9) | v2 | plain |
|---|---|---|---|---|
| dedup | 87.51, 70.26 | 86.67 | **95.67, 93.56** | 78.63 |
| speedup | **67.57** | 58.62, 57.15 | 55.64, 53.32 | 53.38 |
| tsp | −0.79722 | −0.79843 | −0.79674 | **−0.79668** |
| cache | 0.5582 | 0.5602, 0.5607 | **0.5680, 0.5677** | 0.5615 |

Cost: $1.24 per agent on average (5 agents, `agent-costs.json`).

**Result: not adopted; skills/evolve stays v2.** The narrower wording removed the tsp cost (v2.4
lost 0.2–0.5% there) but not the rest. In all five runs with the check, across v2.4 and v2.5,
dedup and cache sit under v2 and speedup above it. A line that acts only after the pick shifts how
the whole search goes. Net over the open tasks it is about zero against v2. Its reason to exist
does not hold either: no v2 final failed the stress split; the one fragile final came from v2.3.

Six variants in runs 3–10 (v2.1–v2.5, v2 on Sonnet), about $50 of agents: none beat v2 reliably.
At two runs a variant, wording changes move single tasks by 10–20% and cancel out over the set.
