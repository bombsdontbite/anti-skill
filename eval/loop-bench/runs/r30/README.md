# Runs 30, 30s and 30f: evolve on Sonnet and Fable, cache only so far

Does evolve help on the other two models? cache's score reads no clock, so these ran while the
laptop was in use, two agents at a time (the runner's `JOBS=2`). The brief names the skill
file ("Read <skill> and follow it"), so the model's own routing does not decide the arm. The
dedup half of run 30 is timed and still owed.

| run | model | arms (6 agents each) | skill text |
|---|---|---|---|
| `r30` | claude-sonnet-5-5 | `e1`–`e6` evolve, `p1`–`p6` plain | `arm-evolve/SKILL.md`, the shipped evolve |
| `r30s` | claude-sonnet-5-5 | `s1`–`s6` S | `arm-s/SKILL.md`, the same text as `../r29/arm-s` |
| `r30f` | claude-fable-5-1 | `e1`–`e6` evolve, `p1`–`p6` plain | `arm-evolve/SKILL.md`, the shipped evolve |

r30's queue first carried the pre-cut N2 text, with the make-scorer paragraph that was cut before
release. It was swapped for the shipped text before any agent started. In r30f, 7 of the 12 agents
were cut by a plan limit and re-run from a fresh workspace by the night guard.

## Results (cache hit rate; scored once per seed)

| model | seed | evolve | plain | difference | p |
|---|---|---|---|---|---|
| Sonnet | dev | 55.2% (53.6–56.4) | 51.3% (40.6–56.1) | +7.7% | 0.021 |
| Sonnet | **test** | **53.7% (52.1–55.3)** | **50.0% (42.3–53.0)** | **+7.4%** | 0.002 |
| Sonnet, S | dev | 54.4% (52.9–55.5) | 51.3% | +6.2% | 0.074 |
| Sonnet, S | test | 52.4% (47.7–55.0) | 50.0% | +4.8% | 0.131 |
| Fable | dev | 55.5% (55.1–55.9) | 55.7% (54.0–56.3) | −0.4% | 0.68 |
| Fable | test | 54.4% (52.1–55.2) | 52.6% (47.5–55.6) | +3.4% | 0.073 |

The test seed here is `test_seed`, the one run 28 reported on. No choice is made from these runs.
p is a one-sided exact permutation test on the difference of means.

- **Sonnet:** evolve helps, more than on Opus (+3.0% in run 28). One plain final is far below the
  rest (42.3% on test); without it, the gap is about +4%.
- **Sonnet stops early even with the skill.** Evolve agents took 3.2–10.9 minutes, most of them
  about 5 of the 15 and 6–8 of the 24 calls, saying more variants did not help. S did not change
  that (2.1–5.3 minutes) and is not better than N2 on Sonnet (−2.5% on test, p = 0.85).
- **Fable:** no clear benefit. Plain Fable already works long (6.0–15.1 minutes, 6–17 calls), so
  the early stop evolve is built against hardly happens. The test seed's +3.4% rests mostly on one
  weak plain final (47.5%).

## Files

`cache_{dev,test}.json` in each folder. r30s's files score r30's finals beside its own. The read audits
flagged nothing in r30 or r30s. In r30f, 35 flags matched only agents' own files: `harness.py
--heldout`, and `local_bench.py`, which matched the `_bench.py` pattern. None read the scorer or a seed.
