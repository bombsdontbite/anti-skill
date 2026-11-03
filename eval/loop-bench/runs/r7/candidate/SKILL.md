---
name: evolve
description: Improves code against an automatic score by a propose → score → improve loop with a local test harness and a held-out check. Use when a coding problem has a measurable target (speed, a benchmark, a quality metric, a test-suite-backed objective) and the user wants the best solution, not the first one; or when the user asks for an AlphaEvolve-, FunSearch- or autoresearch-style search.
---

# evolve

A loop where a model proposes and an automatic evaluator scores finds better code than the first
correct answer. What decides the result is **a fast local harness that ranks like the scorer**,
and **not stopping at the first correct answer**. This loop is built around both.

## 1. Two evaluators and a budget

1. **The official scorer**: the user's, or one you write and freeze before the first candidate.
   It returns validity and a number, higher is better, and it fails closed: any exception,
   timeout, NaN, wrong type or broken constraint is invalid, never a score. You do not edit it,
   read its hidden data or instances, special-case them, or probe it to learn about them.
   Before the first candidate, find what it rejects (allowed dependencies, banned constructs,
   output format, resource limits) in the task and its checks, and stay inside it: a call
   rejected for a rule is a wasted call.
2. **The budget**: scorer calls or a time box. If the user gives none, set one and say it.
3. **Your local harness**, written before the first candidate:
   - an instance generator that follows the problem statement (sizes, distributions, edge
     cases), with a separate set of seeds you never tune on. If the metric has no split, hold
     part of it out; if you cannot, say the result is not held-out;
   - a correctness oracle: the reference implementation, a brute force on small cases, or an
     exact constraint checker;
   - the scorer's limits, with margin, and its way of measuring: what the clock includes, CPU or
     wall time, cold or warm, how many repeats.

**Measure the noise once**: score the same candidate two or three times on the scorer and on the
harness. A gap smaller than that spread is not a result, and not a reason to stop either: repeat
on the harness (median of 3–5) and look for a bigger change.

**Then check the harness.** It must rank candidates the way the scorer does on gaps larger than
the noise. Write down what the generator assumes (sizes, mix, how often each kind occurs) and what
it never produces. If the rankings disagree, suspect the input regime first, and fix the
generator to follow the statement; never fit it to the scorer's outputs or copy its instances.

Iterate on the harness; spend scorer calls on candidates it already rates well. Keep a log: one
line per candidate, harness score, scorer score if any, kept or dropped, why.

## 2. Get a strong first answer

Write the solution an expert would write first, make it correct on the oracle, and score it.
This is the **champion**.

## 3. Do not stop there: try other families

1. List 3–5 **materially different approaches**: other algorithm families, other data
   structures, another decomposition of the problem. Variations of the champion's parameters do
   not count.
2. Build each one far enough to measure it on the harness.
3. Keep the best one or two as parents, alongside the champion.
4. **Ceiling check.** The task is at its ceiling only if the families land within noise of each
   other **and** the champion is within noise of a bound: a known optimum, the scorer's maximum,
   or one you can compute (a relaxation, an exact solve of small instances). Without a bound,
   tied families are not a ceiling. At the ceiling, tune constants once and go to the held-out
   step.

## 4. Improve in rounds

Each round:

1. Look at the 2–3 best candidates so far, from worst to best, with their scores, and at what
   has already been tried and dropped.
2. Make 4–6 children, each one materially different change. Mix them: mostly targeted edits,
   about 1 in 3 a bigger rewrite, sometimes a crossover of the two best.
3. Before measuring, drop near-duplicates of earlier candidates.
4. Measure on the harness, then confirm the round's best with the official scorer.
5. Every two rounds, write 3–5 lines on what has worked and read them first.

**Stop only when the budget is spent or at the ceiling.** Two rounds without a gain beyond the
noise mean: re-check the harness against the scorer, profile the champion and attack its hottest
part, or try a new family from step 3.

After the last round, tune constants on the harness, confirm on the scorer, then score the
final pick on the **held-out** split once (3 times if the score is noisy).

## Output

- A table: baseline, first champion, final pick, with search and held-out scores.
- The final code, and in plain words why it is better.
- The approaches tried in step 3 and how each did.
- The candidate log.
- Limits: the inputs the pick assumes, where it breaks, what its tricks cost in readability.

## Do not

- Judge candidates by reading them. Only measurements count.
- Select and report on the same split.
- Tune on the harness seeds you set aside, or on the official scorer's instances.
- Stop because the answer is correct and good enough, or because gaps are within noise, while
  budget remains.
