# loop-bench, run 2 (2026-10-27)

Plain Claude Code (`iter`) against evolve v2 (rewritten after run 1, the same text as
[`../r13/arm-v2/SKILL.md`](../r13/arm-v2/SKILL.md):
local harness first, a strong first answer, then other algorithm families, no stopping at
correct). Six run-1 tasks plus three new ones (knapsack, coloring, dedup) that neither the skill
nor its author had seen. Same budget of 24 scorer calls; held-out scored by `final_scores.py`
with a seed no agent saw. Scorer calls actually used in brackets.

| Task | iter | evolve v2 | evolve vs iter |
|---|---|---|---|
| binpack | -1.0105 (6) | -1.0112 (6) | -0.07% |
| tsp | -0.7967 (2) | -0.7967 (6) | -0.01% |
| cache | 0.5615 (12) | 0.5680 (16) | +1.15% |
| speedup | 53.8× (2) | 56.7× (6) | +5.40% |
| schedule | -0.2541 (4) | -0.2620 (6) | -3.11% |
| regex | 0.9180 (1) | 0.9285 (3) | +1.14% |
| knapsack | 1.0269 (3) | 1.0270 (6) | +0.01% |
| coloring | -0.7169 (4) | -0.7190 (5) | -0.30% |
| dedup | 77.6× (3) | 93.2× (9) | +20.03% |

**Reading.**

- evolve v2 wins 5 of 9. Its wins are large where the solution space is open: dedup +20%,
  speedup +5.4%, cache +1.2%, regex +1.1%.
- iter's wins are near ties, except schedule (−3.1%): tsp −0.01%, binpack −0.07%,
  coloring −0.3%; knapsack is a tie the other way. On these tasks both reach what looks like
  the ceiling of the method within a few calls.
- Across both runs the loop beats plain Claude Code on every speed-optimisation instance:
  speedup in run 1 and run 2, and dedup. It also wins regex both times.
- The loop costs more: the evolve agents ran longer and used more tool calls (dedup: about 25
  minutes against 6).
- regex shows the overfitting risk the skill warns about. The final pick, chosen by search
  score as this harness required, dropped from 0.936 to 0.9285 on held-out. The agent's own
  held-out check had flagged a safer pattern, which scored 0.929.

**Limits.** One run per condition. Run-to-run variance is visible: iter speedup was 47× in run 1
and 54× in run 2. The laptop was overloaded early in this run (load average up to 22), which
matters for the 1 s wall-clock tasks; later agents ran one process at `nice -n 19`.
