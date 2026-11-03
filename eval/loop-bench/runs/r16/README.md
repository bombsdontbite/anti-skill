# Run 16: variant F (E plus a calls-left counter), cache

Three streams over the night: this folder, `../r16b`, `../r16c`. `arm-f/SKILL.md` is v2 with
step 5 replaced by "Stop only when the official scorer calls are spent. Keep `calls left: N` as
the first line of the candidate log and update it after every call: while it is above zero you
are not done. When ideas run out, go back to step 3 and build a family you have not tried", and
"Scorer calls used, of the budget" added to the output.

Held-out on seed `anti-skill-heldout-r2`, against the mean of the four plain agents (54.03%).

| agent | vs plain | calls | cost | minutes |
|---|---|---|---|---|
| F 1 | +5.6% | 12 | $1.70 | 9.0 |
| F 2 | +6.1% | 21 | $2.54 | 20.0 |
| F 3 (r16b) | +5.6% | 16 | $3.28 | 21.2 |
| F 4 (r16b) | +5.2% | 11 | $1.86 | 11.8 |
| F 5 (r16c) | +5.3% | 17 | $2.33 | 20.8 |
| F 6 (r16c) | +4.5% | 12 | $2.12 | 12.3 |

**Result:** F +5.4% on average (worst +4.5%), level with E (+5.5%). The counter did not make
agents spend the budget: F 1 wrote that the skill said to spend it all and stopped at 12 calls
because the last five scores were flat, and its counter stayed at its first value.
