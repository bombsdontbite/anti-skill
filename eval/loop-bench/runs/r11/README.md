# Run 11: v2.6 (two independent searches in subagents, the better one picked by the scorer)

`candidate/SKILL.md` is the text as tested: the pre-review wording. The review edits were meant
to be in it, but `--amend` without `-a` left them out; the text with them is untested. By their reports, the agents ran the two searches one after the other in
subagents, with the lead alone touching held-out, so the risks the review named did not happen.
Held-out on run 2's seed, idle machine, interleaved (five scorings for dedup and speedup, one for
cache). Every final passes the stress split.

| task | v2.6 run 1 | v2.6 run 2 | v2 run 1 | v2 run 2 | plain |
|---|---|---|---|---|---|
| dedup | **96.81** | 90.16 | 94.63 | 94.92 | 77.90 |
| speedup | **66.27** | **66.25** | 55.41 | 53.13 | 53.46 |
| cache | 0.5661 | – | **0.5680** | 0.5677 | 0.5615 |

Cost: $5.15 per agent on average, 39 minutes ($25.77 for 5 agents), against about $1.3 and 9
minutes for v2.

**Result: not adopted; skills/evolve stays v2.** The gain shows on speedup only (+21%), not on dedup
(−1%) or cache, and the cost is four times v2's.

**A retraction.** The offline estimate that motivated v2.6 ("best of two runs beats one by
5–9%", `../r10/best_of_two.json`) paired finals from *different* variants. For example, it paired
v2 with v2.4 and v2.5, which were weaker on dedup, so "best of two" mostly picked v2. Within one
variant there is no such gain: the two v2 dedup finals score 96.2 and 96.0. The estimate measured
the gap between variants, not a portfolio effect.

**Open question.** On speedup every run of the changed variants (v2.4, v2.5 and v2.6, five
runs) scored 57–68, and both v2 runs about 54, level with plain. Either the changes help speedup
or both v2 runs were unlucky. A third v2 speedup run would tell.
