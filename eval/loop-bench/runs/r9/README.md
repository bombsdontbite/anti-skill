# Run 9: v2.4 (v2 + an awkward-input check before reporting), and v2 on Sonnet

`candidate/SKILL.md` is v2.4 as tested: v2 plus one line, after the held-out pick, to run
it on awkward inputs the task allows and fix any failure. `sonnet/SKILL.md` is v2 (main), run with
`--model claude-sonnet-5-5`. Held-out: run 2's seed, interleaved, on an idle machine (load about
2), five scorings for dedup and speedup, three for tsp, one for cache.

| task | v2.4 runs | v2 runs | plain (Opus) | v2 on Sonnet |
|---|---|---|---|---|
| dedup | 86.86, 70.76, 66.10 | **94.29, 93.76** | 76.72 | 75.70 |
| speedup | **58.73, 57.20** | 55.74, 53.47 | 53.46 | 32.62 |
| tsp | −0.79843, −0.80051 | −0.79674 | **−0.79668** | −0.79697 |
| cache | 0.5602, 0.5607 | **0.5680, 0.5677** | 0.5615 | 0.5490 |

dedup is from the re-run scoring (`dedup_heldout_rerun.json`); the first scoring ranked them the
same. The second dedup run overlapped a game on the same laptop, and the third, on an idle machine, scored
lower still.

Cost: v2.4 $1.79 per agent on average (9 agents), Sonnet $0.85 (4); run 9 in all, re-runs
included, $17.63 (`agent-costs.json`).

**Results.**
- *v2 on Sonnet: dropped.* It costs half as much, but on the open tasks it scores under plain
  Opus (speedup 33 against 53). Its agents stop after 2–5 calls.
- *v2.4: not adopted, and the reason matters.* The check did what it was for: both tsp agents
  found the self-neighbour hang that run 8 shipped (on duplicate points), and fixed it. Elsewhere it cost score,
  because agents hardened the pick against extreme inputs by changing what every input goes through.
  On dedup they handled a 200,000-word record and made the pick "never slower than the reference
  on any awkward input". On cache they capped eviction scans, at 1.3 s against an 8 s limit, and
  kept "the simpler, faster" policy. None of these was a failure. v2.5 (run 10) keeps the check and
  limits it to hangs, crashes, wrong answers and broken time or memory limits, fixed with the
  smallest change.
