# Run 14: variants E and D, plus more nudge and plain agents, cache

Two streams ran at once (this folder and `../r14b`); cache is scored afterwards and is
deterministic, so load does not move the scores. Same neutral brief as run 12.

- `arm-e/SKILL.md` (E): v2 with step 5 replaced by "**Stop** only when the official scorer calls
  are spent."
- `arm-d/SKILL.md` (D): a lean 20-line evolve: harness, first champion, 3–5 families, rounds,
  stop only when the budget is spent.
- `nudge.txt`: the one line from run 12.

Held-out on seed `anti-skill-heldout-r2`, against the mean of the four plain agents (54.03%).

| agent | vs plain | calls | cost | minutes |
|---|---|---|---|---|
| E 1 | +4.8% | 9 | $1.56 | 8.6 |
| E 2 | +5.7% | 10 | $1.46 | 9.3 |
| E 3 (r14b) | +6.5% | 19 | $3.91 | 23.7 |
| E 4 (r14b) | +5.0% | 14 | $2.55 | 23.4 |
| D 1 | +5.6% | 21 | $2.58 | 17.0 |
| D 2 | +5.2% | 24 | $2.82 | 17.1 |
| D 3 (r14b) | +4.3% | 20 | $1.91 | 10.6 |
| D 4 (r14b) | +5.5% | 15 | $3.30 | 17.4 |
| nudge 3 | +5.8% | 14 | $1.72 | 9.4 |
| nudge 4 (r14b) | +0.9% | 16 | $1.54 | 10.4 |
| plain 3 | −0.3% | 8 | $0.67 | 2.9 |
| plain 4 (r14b) | +0.7% | 14 | $1.31 | 5.7 |

Minutes in r14b overlap the other stream and are not comparable with single-stream runs.

**Result:** E +5.5% on average (worst +4.8%), D +5.2% at the highest cost, the nudge +4.3%
over its four agents (one fell to +0.9%). E and D both beat v2 (+2.8%). Agents under E still
stopped early (9–19 calls of 24), so the rule reads as advice, but taking away the permission
to stop after two flat rounds is what moved the result.
