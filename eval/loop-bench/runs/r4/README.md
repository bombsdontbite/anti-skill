# Run 4: evolve v3.1 on dedup

v3.1 (`SKILL.md` in this folder) is v3 plus one rule: a task not at its ceiling is
searched until the budget is spent. It was to be tried on dedup, speedup and schedule, and to
replace v2 if it got dedup back to v2's level. It did not, so the other two were not run.

Held-out (run 2's seed), five interleaved scorings, median (`dedup_repeats.json`):

| v3.1 | v3 | v2 | plain |
|---|---|---|---|
| 80.98 | 81.84 | **94.57** | 72.35 |

v3.1 used 7 of 24 scorer calls, 1,781 s and 170 k tokens. It did not follow the new rule: it
stopped once its variants landed within the scorer's ±15% timing noise, judging further calls
unable to tell them apart. v2 in run 2 kept scoring near-equal variants and ended higher. With one
agent run per condition, whether that was v2's method or a lucky run is not yet known.
