# Run 13: variant C (stop only after half the budget and two rounds without a gain) against v2, cache

Same neutral brief as run 12; the arm adds the skill. `arm-c/SKILL.md` is the tested text (branch
`eval/17-variant-c`), `arm-v2/SKILL.md` is v2 as shipped. Three agents each, one at a time.
Held-out on seed `anti-skill-heldout-r2`; cache is deterministic, so one scoring is exact.
Percentages are against the mean of the four plain agents of runs 12 and 14 (hit rate 54.03%).

| agent | vs plain | calls | cost | minutes |
|---|---|---|---|---|
| C 1 | +5.6% | 13 | $2.07 | 13.7 |
| C 2 | +0.1% | 12 | $1.81 | 14.0 |
| C 3 | +6.1% | 11 | $1.96 | 12.5 |
| v2 a | +3.9% | 17 | $1.28 | 10.8 |
| v2 b | +3.9% | 10 | $1.55 | 10.7 |
| v2 c | +4.6% | 10 | $1.50 | 10.9 |

**Result:** C +3.9% on average, v2 +4.1% in this run (+2.8% over all five v2 agents of runs 12
and 13). C is not better and is less steady; its agents stopped near half the budget anyway.
Not adopted. Runs 14 and 16 test stricter stop rules.
