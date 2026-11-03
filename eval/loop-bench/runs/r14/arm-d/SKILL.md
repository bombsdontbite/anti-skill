---
name: evolve
description: Improves code against an automatic score by a propose → score → improve loop with a local test harness and a held-out check. Use when a coding problem has a measurable target (speed, a benchmark, a quality metric, a test-suite-backed objective) and the user wants the best solution, not the first one; or when the user asks for an AlphaEvolve-, FunSearch- or autoresearch-style search.
---

# evolve

A correct, good answer is where the search starts, not where it ends. Keep improving while the
scorer budget lasts.

1. **The scorer is outside what you edit.** Never read its hidden data, special-case its
   instances, or probe it to learn about them. Invalid is never a score.
2. **Build a local harness first:** an instance generator that follows the problem statement, a
   correctness check (the reference, or brute force on small cases), the scorer's time limits.
   Iterate on it; spend scorer calls only on candidates it rates well.
3. **Write the expert's first answer**, check it, score it. This is the champion.
4. **Try 3–5 materially different approaches** (other algorithms, data structures,
   decompositions; not parameter tweaks), each far enough to measure.
5. **Improve in rounds** from the 2–3 best: 4–6 different children per round, mostly targeted
   edits, about 1 in 3 a bigger rewrite. Skip near-duplicates. Keep a one-line log per candidate.
6. **Stop only when the scorer calls are spent.** Then tune constants on the harness and submit
   the best scored candidate.

Report the baseline, first champion and final scores, why the final code is better, and the log.
