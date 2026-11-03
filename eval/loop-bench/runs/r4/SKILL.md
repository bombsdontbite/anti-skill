---
name: evolve
description: Gets the best solution, not the first one, for code with a measurable target (speed, a benchmark score, a quality metric backed by tests) by a short propose → measure → improve loop. Use when the user wants code faster, smaller or higher-scoring and there is, or can be, a scorer; or when they ask for an AlphaEvolve- or autoresearch-style search.
---

# evolve

When a result can be measured, the first correct answer is usually not the best one, and a
small loop of try → measure → improve finds better. When several different approaches land on
the same number, the task is at its ceiling and more search is wasted.

## Rules

1. **Measure, never eyeball.** Use the user's scorer or write one first. It fails closed: any
   error, timeout, NaN or broken constraint is invalid, never a score. Do not edit it, read its
   hidden data or game it; if you find a hole, fix it and say so.
2. **Build a fast local harness** first: an instance generator that follows the problem
   statement, a correctness oracle (the reference, a brute force or a constraint checker), the
   same time limits. Check it ranks two candidates the way the scorer does. Iterate on it; spend
   scorer calls on candidates it already rates well.
3. **Keep a held-out split** (other instances or seeds) and pick the final on it, not on the
   numbers you tuned against. Report the drop between the two.

## Loop

1. **Strong first answer.** Write what an expert would write first, make it correct, measure it.
2. **Other families.** Build 2–3 materially different approaches (another algorithm, data
   structure or decomposition, not new constants) far enough to measure.
3. **Ceiling check.** If the families come within noise of each other, and of any known bound,
   the task is at its ceiling: tune constants once, report, and stop.
4. **Improve.** Otherwise the task is not at its ceiling, so search until the budget is spent:
   a correct, good answer is not a reason to stop. Run rounds of 4–6 children from the 2–3 best:
   mostly targeted edits, sometimes a rewrite or a crossover; drop near-duplicates before
   measuring. After two rounds without a gain, change the kind of change (profile and attack the
   hottest part, or a new family) rather than stopping.
5. **Finish.** Tune constants, then score the final pick on the held-out split.

## Output

Baseline, first answer and final pick, each with search and held-out scores; the final code and
in plain words why it is better; which families were tried; whether the ceiling check stopped
the search early.
