# loop-bench, run 1 (2026-10-27)

Four conditions per task, all Claude agents, 24 scorer calls of budget:

- **oneshot** — the first of the best-of-N files (`bon/<task>/cand_01.py`).
- **bon** — 24 independent candidates written without running anything; the harness picks the
  best on the search split.
- **iter** — plain Claude Code: solve the task, `./score` allowed up to 24 times.
- **evolve** — the first evolve text, kept as [`evolve/SKILL.md`](evolve/SKILL.md) (round-0 control of 6,
  then rounds of 6), same budget.

Every pick is scored by `final_scores.py` on a held-out set generated from a seed no agent saw
(`LOOP_BENCH_TEST_SEED`); speedup is the median of 3. Raw numbers: `final_scores.json`.

| Task | oneshot | bon | iter | evolve | Best |
|---|---|---|---|---|---|
| binpack | −1.0422 | −1.0159 | **−1.0046** | −1.0165 | iter |
| tsp | −0.8409 | **−0.7876** | −0.7886 | −0.7904 | bon (all three within 0.003) |
| cache | 0.3931 | 0.5184 | **0.5480** | 0.5187 | iter |
| speedup | 30.5× | 56.7× | 47.5× | **66.1×** | evolve |
| schedule | invalid | invalid | **−0.2628** | −0.2695 | iter |
| regex | 0.803 | 0.902 | 0.912 | **0.919** | evolve |

**Reading.**

- evolve beats its best-of-N baseline 4–2, but loses to plain Claude Code 2–4.
- Where iter won, it built its own fast local test harness and tuned on it, using the scorer
  only to confirm (2–14 calls).
- Where evolve won (speedup, regex), iter stopped after one call with a correct answer, and the
  loop kept pushing.
- bon's schedule pick and the oneshot file start jobs before their release on unseen
  instances: without feedback, real bugs go unnoticed.

**Flaws of this run.** The scorer wrapper resolved relative paths after `cd`, so failed calls
were charged; fixed mid-run, and the failed calls were refunded to agents still running.
evolve on tsp and cache had finished with 18 effective calls of 24. The iter binpack agent
probed the scorer to learn the instance length (2000 items) and used it in an end-game term.
One run per condition; machine load varied (another app was running), which matters for the
1 s wall-clock limits.
