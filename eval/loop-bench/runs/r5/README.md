# Run 5: a second v2 agent on dedup

Checks whether v2's dedup win in run 2 was the method or a lucky run. Same skill
(v2, the same text as [`../r13/arm-v2/SKILL.md`](../r13/arm-v2/SKILL.md)), same task, a fresh agent. Held-out (run 2's seed), five interleaved
scorings of every dedup final, median (`dedup_repeats.json`):

| v2, run 5 | v2, run 2 | v3.1 | v3 | plain |
|---|---|---|---|---|
| **102.50** | 88.59 | 90.33 | 77.49 | 73.32 |

Both v2 agents beat plain by a wide margin; the win reproduces. The level of one file moves by up
to ±10 between scoring sessions (v3.1: 81 in run 4's scoring, 90 here), so compare columns of one
table only. This agent used 17 of 24 scorer calls, 2,862 s and 214 k tokens. Its gain came after
the official score stalled near 68 for several candidates: it rebuilt its harness until the
harness ranked candidates as the scorer did, and then found a new family (one-word deletions for
small sets).
