---
name: evolve
description: Improves code against an automatic score by a propose → score → improve loop with a local test harness and a held-out check. Use when a coding problem has a measurable target (speed, a benchmark, a quality metric, a test-suite-backed objective) and the user wants the best solution, not the first one; or when the user asks for an AlphaEvolve-, FunSearch- or autoresearch-style search.
---

# evolve

The one place AI has produced genuinely new solutions is a loop where a model proposes and an
automatic evaluator scores (FunSearch, AlphaEvolve). At the scale a session can afford, simple
loops do as well as elaborate ones. In this skill's own benchmark, the two things that decided
results were: **a fast local harness to iterate on**, and **not stopping at the first correct
answer**. This loop is built around both.

## 1. Two evaluators

1. **The official scorer** (the user's, or one you write first if there is none). It returns
   validity and a number, higher is better, and it fails closed: any exception, timeout, NaN,
   wrong type or broken constraint is invalid, never a score. It is outside what you edit. Never
   read its hidden data, special-case its instances, or probe it to learn things about them.
2. **Your local harness**, written before the first candidate:
   - an instance generator that follows the problem statement (sizes, distributions, edge
     cases), with a separate set of seeds you never tune on;
   - a correctness oracle: the reference implementation, a brute force on small cases, or an
     exact constraint checker;
   - the same time limits as the real scorer, with margin.

   Check that the harness ranks two or three candidates the same way the scorer does. If it
   does not, fix the harness before you trust it.

Iterate on the harness; spend official scorer calls on candidates the harness already rates
well. Keep a log: one line per candidate, harness score, scorer score if any, kept or dropped,
why.

## 2. Get a strong first answer

Write the solution an expert would write first, make it correct on the oracle, and score it.
This is the **champion**.

## 3. Do not stop there: try other families

A correct, good answer is where the search starts, not where it ends.

1. List 3–5 **materially different approaches**: other algorithm families, other data
   structures, another decomposition of the problem. Variations of the champion's parameters do
   not count.
2. Build each one far enough to measure it on the harness.
3. Keep the best one or two as parents, alongside the champion.

## 4. Improve in rounds

Each round:

1. Look at the 2–3 best candidates so far, from worst to best, with their scores, and at what
   has already been tried and dropped.
2. Make 4–6 children, each one materially different change. Mix them: mostly targeted edits,
   about 1 in 3 a bigger rewrite, sometimes a crossover of the two best.
3. Before measuring, drop near-duplicates of earlier candidates.
4. Measure on the harness, then confirm the round's best with the official scorer.
5. **Stop** only when the official scorer calls are spent, or when at least half of them are
   spent and two rounds in a row have not beaten the best official score. Spend calls only on
   candidates the harness rates well; if none qualify, keep proposing. Every two rounds, write
   3–5 lines on what has worked and read them first.

After the last round, tune constants on the harness, confirm on the scorer, then score the
final pick on the **held-out** split once (3 times if the score is noisy).

## Output

- A table: baseline, first champion, final pick, with search and held-out scores.
- The final code, and in plain words why it is better.
- The approaches tried in step 3 and how each did.
- The candidate log.

## Do not

- Judge candidates by reading them. Only measurements count.
- Select and report on the same split.
- Tune on the harness seeds you set aside, or on the official scorer's instances.
- Stop because the answer is correct and good enough, while budget remains.
