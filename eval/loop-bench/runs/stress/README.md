# Stress check: every final so far on inputs the statement allows but random kinds rarely make

`score.py <final> --split stress` on tsp, schedule, knapsack, dedup, coloring, binpack and cache.
The inputs stay inside each TASK.md: duplicate and collinear points, identical jobs and huge
times, all-fit and none-fit knapsacks, identical and very long records, empty and complete
graphs, exact-fit bins, single-key and all-distinct traces. Every baseline passes.

| task | finals checked | invalid |
|---|---|---|
| tsp | 7 (r1, r2, r3, r6, r8) | **1**: r8 candidate, v2.3, a hang when a point is its own nearest neighbour |
| schedule | 9 | 0 |
| knapsack | 4 | 0 |
| dedup | 9 | 0 |
| coloring | 3 | 0 |
| binpack | 5 | 0 |
| cache | 8 | 0 |

One fragile final in 45, from both evolve and plain Claude Code, and it is the one that would
have shipped a hang. `test_scorers.py` now requires every baseline to pass the stress split and
the run-8 tsp final to fail it.
