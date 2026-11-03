# Trigger results

The source of each row in the "Does it load when it should?" table of [RESULTS.md](../../RESULTS.md).
`claude plugin eval` writes its runs to `results/`, which is not committed. Four runs' raw output
was kept, and a compact copy of each is committed (every run of every case with its graders, turns
and cost; prompts are in the case folders, local paths and trace paths are cut):

| Count | Committed raw output |
|---|---|
| Fable 5.1, profile-first's requests | [`results-2026-11-02-fable-profile-first.json`](results-2026-11-02-fable-profile-first.json) |
| Fable 5.1, evolve's near misses | [`results-2026-11-02-fable-evolve-near-misses.json`](results-2026-11-02-fable-evolve-near-misses.json) |
| Fable 5.1, profile-first's near misses | [`results-2026-11-02-fable-profile-first-near-misses.json`](results-2026-11-02-fable-profile-first-near-misses.json) |
| Sonnet 5.5, profile-first's near misses | [`results-2026-11-02-sonnet-profile-first-near-misses.json`](results-2026-11-02-sonnet-profile-first-near-misses.json) |

Every other count below, and the Sonnet breakdown after the table, was written down by hand when
its run finished; that run's raw output was not kept, so it cannot be re-read here. Every run is 3
runs per case, `--ablation none --scaffold`, one model per run (`--model`, or the account default
for Opus). A row "of N" counts runs, not cases: 14 should-trigger cases give 42 runs and 13 near
misses give 39, unless the run stopped at its cost cap.

| Model | Skill | Its requests | Near misses | Date | Source |
|---|---|---|---|---|---|
| Opus 5.5 | evolve | 42 of 42 (100%) | 0 of 39 (0%) | 2026-11-01 | The suite's first full run, 2026-11-01, Claude Code 2.1.280, 162 runs of both skills' cases; repeated unchanged the same day with the profile-first 0.5.1 description. |
| Opus 5.5 | profile-first | 41 of 42 (98%) | 0 of 39 (0%) | 2026-11-01 | The run of 2026-11-01 on the profile-first 0.5.1 description, the one that sends pasted code to the skill. Before it, the suite's first run that day had 36 of 42 (86%) and 0 of 39. A re-run on the 0.5.2 text the same day: 41 of 42, and 0 of 35 near misses before its cost cap. |
| Fable 5.1 | evolve | 40 of 42 (95%) | 0 of 39 (0%) | 2026-11-02 | Its requests: the run of 2026-11-02 that measured both skills on Sonnet and Fable, stopped at its cost cap. Near misses: a run of evolve's 13 near misses alone the night of 2026-11-02 (Claude Code 2.1.280, $8.66); 4 of its runs used all 3 turns and 1 timed out at 180 s without loading the skill, which the suite counts as a pass. |
| Fable 5.1 | profile-first | 41 of 42 (98%) | 0 of 39 (0%) | 2026-11-02 | The kept run: started 2026-11-02 10:14 UTC, Claude Code 2.1.280, plugin 0.5.3, profile-first's cases only; it stopped at its cost cap ($15) after 18 cases, $14.41, with no plan-limit errors. Its profile-first description is the shipped one; the body has been reworded in a few places since. Near misses: a run of profile-first's 13 near misses alone the night of 2026-11-02 ($11.30); 14 runs used all 3 turns and 1 timed out at 180 s without loading the skill, which the suite counts as a pass. |
| Sonnet 5.5 | evolve | 3 of 42 (7%) | 0 of 39 (0%) | 2026-11-02 | The Sonnet and Fable run of 2026-11-02. |
| Sonnet 5.5 | profile-first | 38 of 39 (97%) | 1 of 34 (3%) | 2026-11-02 | Its requests: the same Sonnet run, stopped at its cost cap. Near misses: a run of profile-first's 13 near misses alone the night of 2026-11-02 ($3.30); 5 of its 39 runs were cut by a plan limit and are not counted. The one load was `profile-skip-09-jvm-gc`, a question about JVM garbage-collection pauses. |

## Sonnet and evolve

Which skill loaded on evolve's 14 requests, 3 runs each, on Sonnet 5.5, 2026-11-02, once the
`fired-*` graders recorded which skill loaded when the expected one did not:

| Loaded | Runs |
|---|---|
| evolve | 3 of 42 (only the request that names AlphaEvolve) |
| profile-first | 9 of 42 (the three speed requests, 3 of 3 each) |
| nothing | 30 of 42 |

A description that leads with the user's own words ("get the score up", "find the best
heuristic") was measured on the same 42 runs on 2026-11-02 and did not ship: evolve 3 of 42
again, profile-first 11, nothing 28. Hence the README's advice to name evolve on
Sonnet. That `/evolve` expands to `/anti-skill:evolve` and injects the skill was checked with
`claude -p --model sonnet --plugin-dir` on 2026-11-02, when the Sonnet and Fable rows were added
to the README.

## The pasted-code cases

`profile-fire-05-log-script` and `profile-fire-10-feature-extractor` (tag `pasted-code`) also
grade the reply: no hot spot named, no share or speed-up claimed, no rewrite, and a measuring step
given. In the kept Fable run the skill loaded on 5 of their 6 runs. Of those 5, the reply passed
every check in 3, and in 2 named no hot spot, share or speed-up but gave no measuring step. The run
where it did not load named a likely hot spot and wrote a rewrite. The run used the share grader
as it was before it was changed to accept a conditional phrase ("if X takes most of the time");
that grader failed none of these replies.

## The suite and how to run it

This folder holds 54 requests, written as a user would: for each skill, 14 that should load it and
13 near misses that should not (explain this code, fix this bug, write tests, a question about
profilers, a refactor for readability); 10 of the 54 are in Russian. Each case passes when the
`Skill` tool is called with that skill's name within the first 3 turns, or, for a near miss, is
not.

It also holds 48 cases for the draft skills make-scorer and bench-fairly (tags `make-scorer` and
`bench-fairly`); they run only with those skills merged into the plugin, and have no numbers here
until the skills ship.

To run it from the repository root, one skill at a time (it uses your own Claude Code credential
and stops at the `--max-cost-usd` cap; on Fable, profile-first's cases alone reached it). Each
`--case` pattern matches only that skill's 27 cases, so the draft skills' cases never run:

```
claude plugin eval . --eval-dir eval/triggers --case 'evolve-*' --ablation none --scaffold --no-publish --max-cost-usd 15
claude plugin eval . --eval-dir eval/triggers --case 'profile-*' --ablation none --scaffold --no-publish --max-cost-usd 15
```

- The suite lives outside the plugin so that installing anti-skill installs only the skills.
  `--eval-dir` cannot leave its target, so the target is the repository root, and each case names
  the plugin under test with `plugins: [../../../plugins/anti-skill]`.
- `--ablation none`: the default also runs every case without the plugin, which doubles the cost
  and reports a `Skill` check as display-only.
- `--scaffold` copies `eval/triggers/_fixture/` (a small slow Python report and its benchmark)
  into the cases that name `report.py`.
- `--case <glob>` (matched against the case folder's name) or `--tag <tag>` runs part of it (each
  case is tagged with its skill's name and `should-trigger` or `should-not-trigger`); the night
  runs of 2026-11-02 used `--case 'evolve-skip-*'` and `--case 'profile-skip-*'`. `--runs 1` for a
  quick look.
- Cross-fire: every case also records whether each other shipped skill loaded (graders
  `fired-evolve` and `fired-profile-first`, whose explanation reads `Skill called Nx`), so a
  request that loads the wrong skill reads as a cross-fire, not a plain miss. They take `min: 0`
  and weight 0.001 (the tool has no zero weight), so they never change a pass rate.
