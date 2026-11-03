---
name: evolve
description: Improves code against an automatic score by a propose → score → improve loop with a local test harness and a held-out check. Use when a coding problem has a measurable target (speed, a benchmark, a quality metric, a test-suite-backed objective) and the user wants the best solution, not the first one; or when the user asks for an AlphaEvolve-, FunSearch- or autoresearch-style search. Spends about 15 minutes by default (about 5 if asked to be quick, no time limit if told to take its time). Not for problems without an automatic score, or when any correct answer will do.
---

# evolve

Loops where a model proposes and an automatic evaluator scores (FunSearch, AlphaEvolve) have
produced genuinely new solutions. At the scale a session can afford, simple
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

**Other skills' files.** If `profile/result.json` (from profile-first) lists `hot_spots`, aim the
first answer at the first.

**Budget.** If the user named no time, search for about 15 minutes (use them; do not stop sooner) or
until the scorer calls are spent, whichever comes first. If they ask you to be brief with your time
("a quick look", "just a first pass"), about 5 minutes: this is about your time, not the code's
speed; keep the harness and the held-out check, and do fewer families and rounds. If they tell you
to take as long as needed ("take your time", "overnight", "as long as it takes"), no time limit:
search until the calls are spent, and write `minutes left: none`. If the wording is unclear or
mixed, use the default. Say at the start which budget you are using and how to change it, note the
start time, and check it every round. If the user gave no number of calls, propose one large enough
to fill the time budget, from how long and how much one call takes (with no time limit, as many as
the cost allows), say it, and start without waiting; report it at the end. Keep back a reserve for
the end: the calls and minutes for tuning constants, one confirm on the scorer, and the held-out
scoring; the `calls left` and `minutes left` of §4, item 5, count what remains after it. The only
exceptions to that item's stop rule are a scorer error and a score already at its maximum (a
pass-rate score at 100%, or a known bound met); a correct candidate is not that.

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
5. **Stop** only when the budget is spent. Keep `calls left: N, minutes left: M` as the first
   line of the candidate log and update it after every call: while both are above zero you are
   not done. When ideas run out, go back to step 3 and build a family you have not tried. Every two
   rounds, write 3–5 lines on what has worked and read them first.

After the last round, tune constants on the harness, confirm on the scorer, then score the
final pick on the **held-out** split once (3 times if the score is noisy).

## Output

- A table: baseline, first champion, final pick, with search and held-out scores.
- Time spent and scorer calls used, of the budget and mode you announced at the start.
- The final code, and in plain words why it is better.
- The approaches tried in step 3 and how each did.
- The candidate log.

## Do not

- Judge candidates by reading them. Only measurements count.
- Select and report on the same split.
- Tune on the harness seeds you set aside, or on the official scorer's instances.
- Stop because the answer is correct and good enough, while budget remains.
