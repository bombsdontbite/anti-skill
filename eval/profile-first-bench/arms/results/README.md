# profile-first against plain Claude Code: judge results

The judge's output for the two runs behind the README's profile-first figures and for the hard-tier
pilot, copied from each run's `judge/` folder with the local path prefix cut (`stage/plain/...` and
`stage/skill/...` are the staged answers). No transcripts, briefs or profiles are here:
`summary.json` is the report and `answers.json` holds each agent's scored items as
`score_answers.py` parsed them from `ANSWER.txt`. Each run's `profile-first/` is the skill text its
skill arm was given, with its scripts: the commits it was copied from are not in this repository's
history.

run-c1 and run-c2: the ten original tasks (`t01`–`t10`), two repeats each, plain and skill arm, so **40
agents per run**, claude-opus-5-5, the same machine and the same `shares.json` (measured
2026-10-30), set up with `setup_arms.sh` and scored with `judge.sh`.

| run | date | skill text | plain: top-1 hit, top-1 share error, mean share error, decoys cleared | skill: the same |
|---|---|---|---|---|
| `run-c1` | 2026-11-01 | [an earlier text](run-c1/profile-first/SKILL.md), before a review's fixes | 100%, 6.4 pp, 7.0 pp, 88.9% | 100%, 1.4 pp, 2.0 pp, 94.4% |
| `run-c2` | 2026-11-01 | [the method that ships](run-c2/profile-first/SKILL.md) | 100%, 9.7 pp, 9.0 pp, 94.4% | 100%, 1.5 pp, 1.5 pp, 94.4% |

The figures are `report.plain.total` and `report.skill.total` in each `summary.json`.

## How the README's figures are made

The README compares the shipped text's 20 runs (run-c2's skill arm) with all 40 plain runs
(both runs' plain arms):

- **Top hot spot named:** 100% against 100%, a tie (`top1_hit`; `paired_top1` shows all 20
  pairs in each run found it in both arms).
- **Error in the top hot spot's share:** 1.5 against 8.1 percentage points (the mean of 6.4 and
  9.7), 81% smaller. Against run-c2's own plain arm alone it is 1.5 against 9.7.
- **Mean share error over every part named:** 1.5 against 8.0 points (the mean of 7.0 and 9.0),
  also 81% smaller.
- **Decoys cleared:** 94% against 89–94%, about equal.

run-c1's skill arm ran an earlier text and is not in the claim; it scored 1.4 and 2.0 points,
so the review's fixes cost nothing measurable.

## What to read before trusting them

- Every `leak_flagged` entry is the path heuristic (`/usr/bin/time`, scratch files, `ps`); the
  harness flags it for a reader, and no run was excluded (`excluded` is empty).
- Unmatched items score as misses (`unmatched_items`); see `../../README.md`, Known limits.
- On these ten tasks one casual profile already finds the top spot 9 times in 10, so the top-1
  tie says little. The hard tier (`t11`–`t18`) has one pilot, [`run-c3`](run-c3/summary.json),
  2026-11-01: 8 agents per arm on [the same text as run-c2](run-c3/profile-first/SKILL.md). There
  the skill **did not beat plain**: it tied on the top spot (62.5% each), had about the same top-1
  share error (7.8 against 7.7 points) and a larger mean share error (25.2 against 15.9 points),
  and cleared fewer decoys (75% against 87.5%). It also put the top spot anywhere in its list
  less often (`topk_hit` 62.5% against 87.5%) and named a decoy as a hot spot more often
  (`decoy_named` 25% against 12.5%).
- After run-c2 the shipped text gained a rule for code that cannot be run here (pasted code) and
  a description to match, and three passages were reworded: the copies of step 3, how a speed-up
  is timed, and the closing line on what to run next. Every benchmark task runs, so the pasted-code
  rule is not exercised here, but the text measured is not byte for byte the text that ships.
