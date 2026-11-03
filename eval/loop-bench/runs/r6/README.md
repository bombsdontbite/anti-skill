# Run 6: evolve v2.1 (v2 + noise rule + ceiling check)

`SKILL.md` in this folder is the skill as tested: v2 plus "measure the noise once" and a ceiling
check after the families step. One agent at a time; finals scored on run 2's held-out seed in one
session with the earlier finals, interleaved (five times for dedup and speedup, three for
schedule and tsp; medians, `*_repeats.json`).

| task | v2.1 | v2 | v3 | plain | v2.1 calls | v2.1 cost |
|---|---|---|---|---|---|---|
| dedup | 89.24 | 94.07 (run 2), 95.50 (run 5) | 80.49 | 78.20 | 12 | 1,472 s, 160 k |
| speedup | **59.01** | 55.51 | 56.96 | 52.94 | 10 | 367 s, 99 k |
| schedule | −0.2564 | −0.2622 | **−0.2524** | −0.2541 | 15 | 1,929 s, 152 k |
| tsp | −0.79673 | −0.79674 | −0.79791 | −0.79668 | 14 | 1,732 s, 142 k |

**Result: v2.1 not adopted.** Power is v2's within noise (−5%, +6%, +2%, tie). The ceiling check
did not fire on tsp, where every version ties: the families differed, so v2.1 spent 14 calls and
29 minutes for the same score that v3 reached in 3 calls. knapsack was not run; it could not change
the decision.

A fresh review of the next draft found why v2.1 stopped at 10–15 of 24 calls: it kept v2's
"stop after two rounds that do not beat the best official score" beside its own "only the ceiling
check ends a search early". The agents followed the first. The best dedup final (run 5) used 17.
