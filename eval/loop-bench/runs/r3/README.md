# Run 3: evolve v3 (short skill with a ceiling check) against v2 and plain

One evolve-v3 agent per task (`SKILL.md` in this folder, 44 lines), run one at a time.
Finals scored on run 2's held-out seed, so v3, v2 (`runs/r2/evolve`) and plain (`runs/r2/iter`)
are compared on the same instances. dedup and speedup are CPU-timed and noisy: they were scored
five times, interleaved, and the median is kept (`timing_repeats.json`).

| task | v3 | v2 | plain | v3 calls |
|---|---|---|---|---|
| dedup (median of 5) | 73.67 | **87.26** | 72.04 | 6 |
| speedup (median of 5) | 56.12 | 54.46 | 54.05 | 4 |
| schedule | **−0.2557** | −0.2657 | −0.2549 | 8 |
| cache | 0.5670 | 0.5680 | 0.5615 | 6 |
| regex | 0.919 | **0.9285** | 0.918 | 1 |
| coloring | −0.7256 | −0.7190 | −0.7169 | 5 |
| tsp | −0.8031 | −0.7980 | −0.7974 | 3 |
| binpack | −1.0113 | −1.0112 | −1.0105 | 4 |
| knapsack | 1.0268 | 1.0270 | 1.0268 | 2 |

Cost (agent wall time, tokens): v3 4,742 s and 0.90 M; v2 12,126 s and 1.21 M (inflated by machine
overload early in run 2); plain 7,352 s and 0.94 M (`agent-costs.json`, `runs/r2/agent-costs.json`).

**Result: v3 not adopted.** It costs about what plain costs and scores about what plain scores. It
lost v2's one large win, dedup: it stopped after two rounds without a local gain, having used 6 of
24 scorer calls, while v2 kept going and reached 95 on search. The shortening dropped v2's rule
not to stop while budget remains on a task that is not at its ceiling. The ceiling check itself
worked: tsp and knapsack stopped in 2–3 calls at the same score.
One agent run per condition, so per-task differences under about 1% are within noise.
