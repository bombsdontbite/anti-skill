# loop-bench

Nine optimisation tasks with automatic scorers, for testing whether a propose → score → improve
loop beats a one-shot answer and best-of-N sampling. Python 3 standard library only,
deterministic seeds. A baseline scores in 0.1–3.7 s (dedup about 9 s); a candidate that spends
its whole time allowance keeps a run under about 10 s.

This README is for whoever runs the experiment. The agent under test gets a task's `TASK.md`,
`candidate_baseline.py` (and `regex/train_examples.json`), and the output of
`score.py --split train`. It must not read `score.py` or this file: the scorer holds the test
seeds and the instance generators.

## Tasks

- `binpack` — online bin-packing priority function `priority(item, bins)`; score = −mean(bins / ⌈Σ sizes ÷ capacity⌉) over 15 instances of 2,000 items from three size distributions.
- `tsp` — `solve(points)` tour for 200 points, 1 s per instance; score = −mean(tour / nearest-neighbour tour) over 8 instances (uniform and clustered).
- `cache` — `Cache(capacity).access(key) -> bool`; score = mean hit rate over 6 traces of 30,000 requests (hot sets with scans, loops, phases, a mix, recency, shifting loops).
- `speedup` — a faster `usage_report(sessions, windows)` (rate-weighted interval overlap per window, plus a count); score = reference CPU time / candidate CPU time on 4 inputs of 5,000 × 400; invalid on any differing output.
- `schedule` — `schedule(jobs, m)` on identical machines with releases, deadlines and weights, 1 s per instance; score = −mean(weighted tardiness / EDF's) over 8 instances of 200 jobs.
- `regex` — `PATTERN` for a hidden family of date-like strings; score = accuracy under `re.fullmatch` − 0.001 × pattern length (train 200+200 examples, test 1,000+1,000 from another seed).
- `knapsack` — `solve(values, weights, capacities)` for a 0/1 knapsack with 2 or 3 resource limits, 1 s per instance; score = mean(value / value-density greedy's value) over 8 instances of 300–500 items (uncorrelated, weakly and strongly correlated, value tied to weight plus noise; tightness 0.25/0.5/0.75).
- `coloring` — `color(n, edges)` proper colouring, 1 s per instance; score = −mean(colours / largest-degree-first greedy's colours) over 8 graphs of 150–400 nodes (sparse, medium and dense G(n,p), two geometric, near-bipartite, two with a hidden k-partition), labels shuffled.
- `dedup` — a faster `near_duplicates(records)`: every pair whose word sets have Jaccard ≥ 0.8; score = median reference CPU time / median candidate CPU time over 3 alternating fresh runs on 2 inputs of 3,000 records (Zipf-vocabulary titles, short records); invalid on any missing, extra or repeated pair.

## Scoring

```bash
cd eval/loop-bench/<task>
nice -n 10 python3 score.py <candidate.py> [--split train|test]   # default: train
```

One JSON line: `{"valid": bool, "score": float, "detail": {...}}`, higher is better. An invalid
run scores `-1e9` and says why in `detail.error`. `train` is what a loop may optimise on; `test`
uses different seeds and is for the final report only. To score on a set nobody has ever seen,
set `LOOP_BENCH_TEST_SEED=<any string>` with `--split test`.

Two seeds, two jobs. `anti-skill-heldout-r2` is the development seed: skill variants are
chosen on it, so its numbers cannot be a claim. A claim is scored once on a secret test seed
that no selection has seen: `heldout_compare.py ... --seed-file <file>`, which records only the
seed's fingerprint. The seed lives outside the repo; a new release uses a new one.

What the scorers guard against (`_bench.py`):

- the candidate runs in a fresh process in an empty temp dir (`python3 -P -s -S`, with an env of
  only `PATH` and `PYTHONHASHSEED=0`, so string hashing is the same on every run), with a time
  limit per instance or per run and a hard timeout on the whole process;
- a static check rejects imports outside a small stdlib list (math, random, heapq, bisect,
  collections, itertools, functools, operator, array, re, string, typing, time, statistics,
  dataclasses, copy, fractions, decimal, enum), `open`/`eval`/`exec`/`getattr` and friends, dunder
  attributes and dunder names inside strings, and files over 100 KB;
- a candidate may define only the dunders honest code uses (`__init__`, comparisons, `__hash__`,
  the container methods, `__repr__`, `__str__`). Any other dunder bound by `def`, `class`,
  `import ... as`, `except ... as`, a match capture, a parameter or `global` is refused:
  a module `__getattr__`, `__del__`, `__init_subclass__`, `__set_name__` or `__getattribute__`
  would run its code implicitly, after the checks;
- module internals (`random._os`, `typing.sys`) are refused by name on any object, because an
  alias, an argument or a container hides which module an attribute is read from. The
  names are every module an allowed module holds that is not itself allowed, and every private
  of an allowed module, read from the running Python. namedtuple's `_replace`, `_asdict`,
  `_make`, `_fields` and `_field_defaults` stay allowed, and so do a candidate's own private
  attributes;
- `open` and the file, process and descriptor functions of `os` (`write` and `dup` included, so
  nothing reaches fd 1) are disabled at run time; the candidate's stdout goes to stderr, so
  printing cannot forge a result;
- outputs are re-checked in the parent: binpack replays every decision, tsp checks the
  permutation, schedule checks releases, overlaps and completeness, speedup compares every
  output with the reference's, cache verifies after every miss that `store` holds only keys
  really requested and within capacity, and counts a hit only if the key was really cached;
  knapsack recomputes value and every resource load from its own copy of the instance and
  rejects repeated or out-of-range indices, coloring checks every edge against its own edge list
  and the range of every colour, dedup compares the sorted pairs with the reference's on the
  timed inputs (every run) and on 70 correctness tests (whitespace, case, repeats, the exact
  0.8 boundary, empty records, dense tiny vocabularies);
- regex matches apart from the candidate: the candidate's process only hands over
  `PATTERN`, a `str` of at most 2,000 characters, and a second process that never imports the
  candidate compiles and matches it, both within one 10 s budget, so a catastrophic pattern is
  still invalid. That second process is the guard. The candidate's process also compares `re`
  with a snapshot taken before the import, which only turns a plain forged run into "invalid"
  rather than the 0.5 of its empty pattern; code that runs later, such as a module
  `__getattr__`, gets past it and still scores as the pattern it hands over. That forge is
  refused statically by the dunder rule above, so `test_scorers.py` also scores it with the static check opened
  in its own process, which fails if matching moves back beside the candidate. Before, a candidate
  that replaced `re.compile` with its own Python check and set `PATTERN = ""` scored up to 1.0,
  above every honest pattern; no committed candidate did, and every one rescores exactly as
  before;
- knapsack, coloring and dedup take their clocks before the candidate is imported, so a
  candidate that reassigns `time.perf_counter` or `time.process_time` changes nothing; dedup
  also counts the candidate's import CPU time and turns its result into a list inside the timed
  region, so a generator or work done at import does not escape the clock.

Known gaps. Every scorer that times the candidate takes its clock before importing it, and
builds the result inside the timer: knapsack, coloring, dedup, tsp, schedule, speedup. tsp and
schedule did this only from 2026-10-28; before that a generator could search past their 1 s
per-instance limit. Every final scored since passes with its real time under the limit, so no
past result changes. binpack and cache read no clock and bound the whole run with an alarm;
regex bounds its two processes with one 10 s budget and names the phase that ran out.
`test_scorers.py` keeps the old exploits invalid or under 3×. On speedup these are a reference
copy with `time.process_time = lambda: 0.0`, once 2,142,043×, and a generator, once 47,942×. On
tsp and schedule it is a lazy search. speedup does not count import time, which matters only to
a candidate that hard-codes answers; the test seeds defeat that.

Regenerate the baselines (two runs per split, checks they agree, writes `<task>/baseline.json`):

```bash
nice -n 10 python3 make_baselines.py [task ...]   # about a minute; dedup is most of it
nice -n 10 python3 regex/score.py --write-train   # only if the regex generator changes
```

## Running a queue

`run_queue.sh <run>` runs the agents listed in `runs/<run>/queue` with `claude -p`, one at a
time. `JOBS=2 run_queue.sh <run>` runs two at once, still started in queue order, behind the same
load gate (no start while the 1-minute load is above 6) and the same STOP file (no new start; the
agents already running finish). With `JOBS` above 1 the log opens with `queue started, jobs=N` and
every start line ends in `jobs=N`; with `JOBS=1` the log is as it always was. Two agents at once
add timing noise to the CPU-timed tasks (speedup, dedup): measure it before comparing a paired
run with a one-at-a-time one.

Before it starts an agent the runner claims the entry with
`mkdir runs/<run>/.claims/<cond>__<task>` and removes the claim when the agent ends, so no entry
runs twice, even when the queue lists it twice or two runners read one queue. Claims live outside
the workspaces, so an agent's folder holds nothing earlier runs' agents did not see. Only a killed
runner leaves a claim behind; its entry is then logged `skip <entry> (claimed: …)`. Check that no
agent still works there (`pgrep -f "Work only in <workspace>/"`), run
`rmdir runs/<run>/.claims/<cond>__<task>` and start the queue again. A guard that deletes and
rebuilds a limit-cut workspace must remove that claim too: deleting the workspace leaves it.

`python3 ../arms/progress.py runs/<run>` says where a queue is, naming every running agent, and
`test_run_queue.py` runs the runner itself on a fake `claude`.

## Baselines

| task | baseline | train | test | run time |
|---|---|---|---|---|
| binpack | best fit | −1.036581 | −1.035200 | 0.4 s |
| tsp | nearest neighbour | −1.000000 | −1.000000 | 0.1 s |
| cache | LRU | 0.365194 | 0.359467 | 0.6 s |
| speedup | the reference itself | 1.003 / 1.002 | 1.004 / 1.002 | 3.2–3.7 s |
| schedule | earliest deadline first | −1.000000 | −1.000000 | 0.1 s |
| regex | `\d{4}-\d{2}-\d{2}` | 0.640500 | 0.637500 | 0.1 s |
| knapsack | value-density greedy | 1.000000 | 1.000000 | 0.4 s |
| coloring | largest degree first | −1.000000 | −1.000000 | 0.8 s |
| dedup | the reference itself | 0.998 / 0.979 | 1.000 / 1.028 | 40 s under load* |

Every score repeats exactly on a second run except `speedup` and `dedup` (two runs shown),
which are CPU-time ratios: about ±0.3 % on the speedup baseline and ±3 % on a fast candidate;
dedup's baseline repeats within ±3 % (measured under load).

\* The three new rows were measured on 2026-10-27 with the machine busy: in the same
conditions speedup's baseline took 15 s against the 3.2–3.7 s above, and dedup's reference took
2.9 times speedup's, so on a quiet machine a dedup baseline run is about 9 s and a fast
candidate's about 5 s.

Sanity points measured while building the scorers (not targets, and not to be shown to the agent
under test): first fit −1.0401 on binpack train; a time-capped 2-opt −0.858 on tsp train; an SLRU
cache 0.404; a sort-and-prefix-sum `usage_report` ≈ 30×; an ATC dispatch rule −0.347 on
schedule; a fully correct date pattern of 135 characters 0.865 on regex test; greedy plus a
0.8 s drop-and-refill local search 1.0085 on knapsack train; DSATUR −0.863 on coloring train;
an inverted index with prefix and size filters ≈ 64× on dedup train.
