---
name: evolve
description: Improves code against an automatic score by a small propose → score → improve loop with a held-out check. Use when a coding problem has a measurable target (speed, a benchmark, a quality metric, a test-suite-backed objective) and the user wants the best solution, not the first one; or when the user asks for an AlphaEvolve-, FunSearch- or autoresearch-style search.
---

# evolve

The one place AI has produced genuinely new solutions is a loop where a model proposes and an
automatic evaluator scores (FunSearch, AlphaEvolve). At the scale a session can afford, tens
of evaluations, simple loops do as well as elaborate ones, and plain best-of-N sampling often
matches them. So this loop is small, and it always reports against its own best-of-N control.

## Before anything: the scorer

1. **Find or write the scorer, in code**, before the first candidate. It returns validity and a
   number, higher is better. If the user has one, use it as is.
2. **It fails closed.** Any exception, timeout, NaN, inf, wrong type or broken constraint is
   *invalid*, never a score. Check every constraint exactly, not by sampling.
3. **Two splits.** Optimise on a *search* split; keep a *held-out* split (other instances or
   seeds) that no candidate is ever selected on. If there is no held-out split, make one. If it
   has fewer than about 30 cases, say the final number is anecdotal.
4. **The scorer is outside what you edit.** Never change it, read its hidden data, special-case
   its instances, or game its checks to raise the number. If you find a way to game it, fix the
   scorer and say so.
5. Score the current code (the baseline) on both splits. If the scorer is noisy, score 3 times
   and use the median.

## The loop

Budget: about 24 scored candidates unless the user says otherwise. Count every scorer call.

**Round 0, the control (6 candidates).** Write 6 independent solutions from the problem
statement alone, as different from each other as you can, without scoring any of them until
all 6 exist. Score all 6. The best of them is the **control**: the loop must beat it.

**Rounds 1–3 (6 candidates each).** Each round:

1. **Pick parents**: from the top 3 so far by search score, prefer the ones with fewer
   children; plus one random valid candidate.
2. **Show yourself** 2–3 earlier candidates sorted from worst to best, with their scores and
   the scorer's feedback, and the list of changes already tried and dropped.
3. **Propose one materially different change per child**, not "improve it":
   - mostly targeted edits;
   - about 1 in 3 a full rewrite of the idea;
   - about 1 in 6 a crossover of the two best.
4. **Reject near-duplicates before scoring**: if a child is essentially an earlier candidate,
   replace it.
5. Score, and add one line per child to the log: score, kept or dropped, why.
6. **Stop early** if two rounds in a row do not beat the best so far.

Every two rounds, write 3–5 lines on what has worked and what has not, and read them before
the next round.

**After the loop.**

1. Tune the constants of the best candidate separately; this counts against the budget.
2. Score the final pick and the control on the **held-out** split (3 times if noisy).
3. Pick by held-out result only if it was decided in advance; otherwise report the search
   winner's held-out score as it is, including any drop.

## Output

- A table: baseline, control (best of round 0), final pick, each with search and held-out scores.
- The final code, and in plain words why it is better.
- An honest line: did the loop beat its own best-of-N control on the held-out split? If not,
  say so; the control is then the answer.
- The candidate log.

## Do not

- Grade your own candidates by reading them. Only the scorer scores.
- Select and report on the same split.
- Keep adding hints or expert tricks to every prompt; add one only after a stalled round.
- Spend budget on candidates you already know are invalid.
