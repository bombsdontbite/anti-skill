# Run 8: v2.3 (v2 + a bound-based ceiling check + a limits note), first run by `claude -p`

`candidate/SKILL.md` is the candidate as tested; `shipped2/SKILL.md` is the shipped evolve of
the time (v2). Agents ran one at a time from `../../run_queue.sh`, each with
`claude -p`, so costs are the CLI's own report (`agent-costs.json`). Held-out: run 2's seed,
interleaved, five scorings for dedup and speedup, three for schedule and tsp, one for the
deterministic cache and knapsack (`*_heldout.json`, `cache_heldout.json`).

| task | v2.3 run 1 | v2.3 run 2 | v2 run 1 | v2 run 2 | plain |
|---|---|---|---|---|---|
| dedup | 90.03 | **93.01** | 89.83 (r2) | 90.81 (r5) | 75.86 |
| speedup | 53.34 | **55.44** | 54.44 (r2) | 51.92 | 52.09 |
| schedule | −0.2575 | −0.2560 | −0.2624 (r2) | −0.2584 | **−0.2541** |
| cache | 0.5638 | 0.5623 | **0.5680** (r2) | 0.5677 | 0.5615 |
| tsp | **invalid** (3 of 3) | – | −0.79674 (r2) | – | −0.79668 |
| knapsack | 1.02704 | – | 1.02704 (r2) | – | 1.02695 |

Cost: v2.3 $1.47 and 12.4 min per agent on average (10 agents), v2 $1.22 and 9.1 min (3 agents);
$18.40 in all.

**Result: v2.3 not adopted.** On the open tasks it averages about +1% over v2, within noise; on
cache both v2.3 runs sit under both v2 runs. Its tsp final times out on the held-out split. With
duplicate points a point can be its own neighbour (`sorted(...)[1:]` assumes it sorts first) and
the local search never ends. The training instances have no duplicates and the agent's harness
made none. A v2.1 agent hit the same bug on the same task and fixed it (run 6). The ceiling check
never fired: on tsp and knapsack no agent computed a bound.

What this run adds beyond v2.3: a loop that fits code to its data can ship code that breaks on
inputs it never saw, and search scores do not show it. That makes robustness the next thing to
measure.
