# profile-first-bench: the measuring stick

A benchmark that scores an agent's answer to "where does the time go, and how much?", for the
`profile-first` skill (design in `research/profile-first/prior_art.md`,
section 4.2). It holds no skill. It holds eighteen small stdlib-only Python programs, each with a
real hot spot that is not the obvious one next to a decoy that looks slow but is cheap; stubs that
remove one component at a time; a script that measures each component's true share by ablation;
a scorer; and scripted profilers that check a tier separates a casual profile from a careful
measurement without running an agent.

Ten tasks (t01–t10) are the original tier. Eight (t11–t18) are the **hard tier** (below): on
seven of them one cProfile run, read the usual way, names the wrong component.

## Layout

| Path | What | Agent sees it? |
|---|---|---|
| `tasks/tNN/` | `app.py` (+ helpers), `gen_input.py`, `TASK.md`, data it ships with | **yes**, a copy of one folder |
| `lab/manifest.json` | per task: kind, command, input sizes, components with role, location and keywords | no |
| `lab/stubs/tNN.py` | one stub per component | no |
| `lab/stubkit.py`, `lab/harness.py` | stub kinds; runs a program with one stub in, as a fresh process | no |
| `lab/runner.py` | work copies, commands, one timed run (shared by the scripts below) | no |
| `lab/build_assets.py` | writes `t01/vocab.txt` and `t05/fixtures/sample.csv` (fixed seeds) | no |
| `smoke.py` | tiny inputs: every task runs, every stub prints the real output, no leak | no |
| `measure_shares.py` | the ablation measurement; writes `shares.json` | no |
| `stub_cost.py` | times a replay stub's own load and replayed calls, which a share leaves out | no |
| `shares.json` | ground truth, once measured | no |
| `score_answers.py`, `test_score_answers.py` | the scorer and its tests | no |
| `measurers.py`, `test_measurers.py` | scripted casual and careful profilers, scored by `score_answers.py` | no |

Nothing in a task folder switches a stub on: the programs are plain programs. The harness
imports a work copy of the program as a module, patches one function (or, for an import,
the module itself), then calls `main()`. The agent gets **a copy of one task folder in a fresh
directory outside this repository**, never a path into it. `.work/` holds work copies and is
ignored by git.

## The original ten tasks

Roles: **hot** is the designed hot spot (target share ≥ 50%), **decoy** looks slow and should
cost ≤ 5%, **other** is a real but minor part. `top` in `shares.json` is whatever the measurement
says is biggest; the scorer uses that, not the design.

| Task | Kind | Hot | Decoy | Other |
|---|---|---|---|---|
| t01 | import time | `spelling.py` builds a table of every one-edit variant (~1M) at import | `confusion_cube`: triple loop over 10×10×10 | `correct_queries` |
| t02 | serialisation | `write_report`: `json.dump` to a stream (the pure-Python encoder) with `default=` | `parse_duration`: hand-written char loop | `load_orders` |
| t03 | allocation | `snapshot`: `copy.deepcopy` per event | `classify`: regex match in the main loop | `load_events` |
| t04 | hidden O(n²) | `unique_in_order`: `if x not in seen_list` | `similarity_matrix`: nested loop over 50 tags | `normalise_tags` |
| t05 | input-size trap | `match_deliveries`: `list.index` + `del` over open shipments | `build_rate_grid`: 300×200 grid, fixed cost | `load_rows` |
| t06 | logging | DEBUG `logging` to a file, three records per transaction | `make_key`: f-string per transaction | `apply_rules` |
| t07 | regex per item | `mentions`: `re.search` with a pattern per product name (1,600 > the `re` cache) | `parse_ticket`: `re.compile(CONSTANT)` per line, cached | `load_customers` |
| t08 | I/O wait | `save_batch`: SQLite commit every 5 rows | `luhn_ok`: pure-Python checksum | `parse_rows` |
| t09 | profiler distortion | `pack`: one `lzma.compress` call at preset 9e on the raw capture | `normalise_all`: 250k tiny `clamp()` calls for a 1/16-rate preview, inflated by cProfile | `histogram` |
| t10 | control | `find_duplicates`: the obvious all-pairs loop really is it | none | `shingle_all`, `load_listings` |

- **t05** ships `fixtures/sample.csv` (200 rows) and states the production size (40,000 rows) in
  `TASK.md`; `gen_input.py` defaults to the sample's size. On the sample the fixed-cost grid
  dominates; at production size the quadratic match does. `measure_shares.py` measures both.
- **t06** reads its log level from `ENGINE_LOG_LEVEL`, default `DEBUG`. Setting it is a fair way
  for an agent to measure the logging cost; the true share is at the default.
- **t08**'s hot spot is a commit per batch, partly waiting on the disk, so t08 is the one task
  scored by wall time (`"clock": "wall"` in the manifest); its CPU shares are kept beside.
- **t10** guards against a skill that always says "not the loop".

## The hard tier (t11–t18)

The original ten do not separate a careful profiler from a casual one: one cProfile run on the
shipped input, read off its top row, names the measured top component in 9 of 10 (it misses only
t05, the input-size trap). A hard task is one where that casual reading names the wrong
component and an ablation at the input `TASK.md` states names the right one. Each is built on a
way cProfile's report and the real cost come apart, and each keeps the bench's rules: a plain
program, checkable output, a share measured by ablation, nothing in the folder naming the answer.

| Task | Kind | Hot (share) | What a casual profile names instead (share) | Why the profile misleads |
|---|---|---|---|---|
| t11 | lazy iterator | `addresses`: returns `ADDRESS.finditer(text)`, a backtracking pattern (97%) | `domain_counts`, which loops over the matches (decoy, 2%) | the C iterator's scan runs inside the consumer's frame, so its time is the consumer's `tottime` |
| t12 | GC retention | `AuditTrail.add`: keeps every priced basket, 1.6M dicts (61%) | `price_basket`, which allocates them (7%) | the cyclic collector fires where the allocation happens; it is walking the retained heap |
| t13 | exit handler | `save_cache`, registered with `atexit`: `json.dumps(indent=1)` of the 355k-entry cache (70%) | `load_cache` (3%, a lower bound: below) | cProfile stops when the script returns, before exit handlers run |
| t14 | child process | `start_indexer`: `Popen` of `indexer.py`, the tokenizer (96%) | `read_postings`, which waits on its pipe (decoy, 0%) | the parent sees only the wait, charged to whoever calls `communicate()` |
| t15 | profiler overhead | `pack`: one `bz2.compress(raw, 9)` call (64%) | `coverage`: 12.5M calls to a tiny `ink()` (32%) | cProfile's per-call cost inflates the tiny calls about 7×, past the one C call |
| t16 | input-shape trap | `drop_resends`: `in` on a per-merchant list (88%) | `load_rows` (2%) | the generator's default spreads 60,000 payments over 15,000 merchants; production is ~20 merchants, same row count |
| t17 | spread cost | `markup.py`: nine passes, each its own row, none over about 12% of the profile (62%) | `reading_stats`, one row (25%) | the hot spot is a module, not a row: no single line of the report is the biggest |
| t18 | control | `find_overlaps`: the pairwise loop really is it (70%) | — | a lazy `csv.reader` feeds it, but it is cheaper (6%, a lower bound: below); guards against "always blame the producer" |

Shares are medians of 7 rounds on the 2026-11-02 measurement (`shares.json`): all eighteen tasks in
one `measure_shares.py --force` run, about 08:38–08:49, under the current launch (`env.harness_flags`
is `-P -s -S`, with `PYTHONHASHSEED=0`) and the fast recording read, on this laptop with only the
Claude app open (1-minute load 1.9–3.2, 0.46–0.79 per performance core; t16 started just above
the 0.75 refusal line). All eight hard tasks meet the hot ≥ 50% and decoy ≤ 5% targets, with no
flag: no CI wider than 10 points, no load above 1.0 per performance core. Against the
2026-11-01 measurement of the hard tier (taken under `-I`, the laptop in use) no top component
and no decoy verdict moved, and no share moved by more than 5 points (t12 `load_events` −4.9,
t17 `slug_table` −4.2).

`stub_cost.py t18 t11 t13 t14 t15 t16 t17` (2026-11-02, 00:08, load 3.3) timed every stubkit replay
of those tasks on its own; t12 and t01–t10 have not been timed. Two stubs cost far more than the
share they leave:
- **t18** `open_sheet`: 16.7 points of the run against a 6.2% share. Its stub loads all ~600k
  recorded rows and rebuilds each as a tuple, about what the C csv parser costs; with the stub's
  cost added the parse is about 23%, near the 28–30% agents measured. The 6.2% is a lower bound.
- **t13** `load_cache`: 11.6 points against 2.6%, so about 14%. Also a lower bound.

Every other timed replay stub costs 3.1 points or less (t16 `load_rows` 3.1, the rest ≤ 0.5).
Neither understated component is a top or a decoy, and with its stub's cost added each stays far
below its task's top (about 23% against 70%; about 14% against 70%). t12 `load_events`
measures −12% (CI −16 to −6), which says its stub costs more than the loading it replaces.

- **t13** reads `geocache.json` and writes `geocache.next.json`, so every run sees the same cache.
- **t16** has a `toy` entry (the generator's defaults); its top there is `load_rows`, which the
  manifest's `toy.top` records and `measure_shares.py` checks.
- **t12**'s `price_basket` stub keeps the dicts and replays only their nets, packed as int64: a
  recording of 1.6M dicts cost more than pricing them.
- The hard tier's stubs use two more kinds (`lab/stubkit.py`): **ReplayAfter** still runs
  `before(*args)` (drain the iterator, wait for the child) so the work an input carries is not
  cut, then returns the recording; **ReplayLazy** records what a consumer pulls from a lazy
  iterator. The harness now saves recordings from an exit handler registered before `main()`, so
  a function that runs from `atexit` (t13) is recorded too.

### Proof without agents: scripted profilers

`measurers.py` plays four strategies and writes an `ANSWER.txt` per task, scored by the real scorer:

```bash
nice -n 10 python3 -B measurers.py OUT --strategies casual,casual-cum,casual-prod   # seconds
nice -n 10 python3 -B measurers.py OUT --strategies careful     # ablation, minutes; refuses when busy
python3 -B measurers.py --summary OUT                           # top-1 per strategy and tier
```

- **casual**: `python3 -m cProfile` on the input you get without reading `TASK.md`'s sizes (the
  generator's defaults, or a shipped fixture), then the top `tottime` row. A library row is read
  by what it says first (json, logging, bz2); a builtin or library row that names no component
  is charged to its biggest caller in the task's files; rows that name no component (`main`, the
  entry script's `<module>`) are skipped.
- **casual-cum**: the same profile, the task-file row with the biggest `cumtime`.
- **casual-prod**: casual on the input `TASK.md` states, to tell size traps from profiler traps.
- **careful**: the bench's ablation at the stated input, 3 rounds instead of 7.

Profiles from 2026-11-02 (00:08, load 3.3), this laptop, Python 3.15.2, scored against the
2026-11-02 `shares.json` (the same result as against the 2026-11-01 one, whose tops are the same):

| Strategy | Original ten (top-1) | Hard tier, all eight | Hard tier, seven traps (no t18) | Misses |
|---|---|---|---|---|
| casual (`tottime`) | 90% | 12% | 0% | t05; t11–t17 |
| casual-cum (`cumtime`) | 80% | 12% | 0% | t05, t06; t11–t17 |
| casual-prod (stated input, `tottime`) | 100% | 25% | 14% | t11–t15, t17 |
| careful (ablation, 3 rounds) | 100% | 100% | 100% | none |

On the original tier only the input-size trap (t05) fools the casual reading, which is why
agents scored near 100% there. On the hard tier the casual reading misses every trap and keeps
the control; reading the stated input fixes only t16, so the other six are profiler traps, not
size traps. The careful strategy is the bench's own method with fewer rounds, so its 100% says
the truth is stable at 3 rounds, not that ablation is the only way to find it.

## Ground truth by ablation

The true share of component C is `1 − T(C stubbed) / T(nothing stubbed)` over the whole fresh
process, start-up included: how much faster the run gets if C costs nothing. `TASK.md` gives the
agent that definition in wall-clock time. T is the child process's CPU time (user + system, from
its rusage), except for t08, where it is wall time. Nine of the programs are one CPU-bound
process, so on an idle machine their CPU time is their wall time less a few milliseconds, and
unlike wall time it does not grow while the process waits for a core. Both clocks are recorded
for every task, and a CPU-timed task whose two shares differ by more than 5 points is flagged.
No profiler is involved, so a profiler-using skill is not scored against a profiler's own answer.

Stub kinds (`lab/stubkit.py`):
- **Replay**: a recording run saves the function's return values with `marshal`; stubbed runs
  return them in order without running the function. With `fake_module`, the module is never
  imported (t01).
- **ReplayWrite**: the same for a function whose whole effect is text written to a stream (t02).
- **Replace**: a hand-written equivalent that is much cheaper, such as `dict.fromkeys` for the
  list-membership dedupe, or one commit at the end instead of one per batch (t08 commits the tail
  after the loop, so the stored rows are the same).
- **Hook**: a global switch before import (t06: `logging.disable(logging.DEBUG)`; `engine.log` is
  a debug log, not output).

Every stubbed run must print byte-for-byte what the real program prints; both scripts check it.

Every run (`lab/runner.py`) gets an env of only `PATH` and `PYTHONHASHSEED=0`, so string hashing,
and with it the order of a set of strings, is the same on every run. The harness starts with
`-P -s -S`: `-I` would also imply `-E`, which drops `PYTHONHASHSEED`. `plain` is the user's own
command, `python3 app.py`, in the same env; unlike the harness it imports `site`, so `plain`
against `none` includes that start-up (a few milliseconds), and the share's denominator leaves it
out.

## Smoke check (run 2026-10-28)

```bash
nice -n 19 python3 -B smoke.py          # all ten; tiny inputs, one run per variant
```

Result on 2026-10-28: all ten tasks run, all 30 stubs and the plain runs print the same output as
the real program, and no task file mentions a stub, a switch or the answers. The machine was in
use, so the run times it printed are not a measurement. Two observations from those runs shaped
the defaults:
- t01's import took about 1 s per run, as designed.
- t08 took about 0.09 s for 60 commits, about 1.5 ms per commit, so the default became 6,000 rows.

The first measurement (2026-10-30, not committed) found five runs under 0.5 s, so the defaults
grew to bring each to about 0.7–1.3 s on the same laptop: t01's vocabulary from 2,400 to 6,000
words (`lab/build_assets.py`), t07 from 8,000 to 24,000 tickets, t08 from 6,000 to 20,000 rows
(about 0.25 ms per commit there), t09 from 800,000 to 4,000,000 samples. It also found t03's hot
share under 0.5 and t09's decoy near 0.18, at any size:
- **t03**: about half of the rest of the run was the cyclic GC walking an audit trail that kept
  every snapshot. The trail is now the latest 2,000 snapshots, summarised as they are taken, and
  the default is 40,000 events over 300 SKUs (more lots per item, so each copy is deeper).
- **t09**: one tiny call per sample costs about a quarter of lzma's time per sample, so no size
  brings the decoy under 5%. The archive is now the raw 16-bit capture, and the levels are a
  preview at 1/16 of the rate, which leaves about 250k calls.

## Verifying the shares later

On an idle machine, nothing else heavy running:

```bash
cd eval/profile-first-bench
python3 -B smoke.py                      # stubs still match; a few seconds
python3 -B measure_shares.py             # all tasks; about 10-15 min, one process at a time
python3 -B measure_shares.py t05 t08     # or some tasks; merges into shares.json
python3 -B stub_cost.py t18              # each replay stub's own cost, in points of the run
```

Per task and input size: a fresh work copy, the input generated from the fixed seed, one
recording run, one check run per variant, then `--rounds` rounds (default 7, at least 5) in which
every variant (`none`, `plain`, each component) runs once as a fresh process in a shuffled order.
It lowers its own priority to nice 19, and refuses to start when the 1-minute load per performance
core (`hw.perflevel0.logicalcpu` on Apple silicon, else every logical CPU) is above
`--max-load-per-core` (0.75), unless given `--force`. CPU time removes the wait for a core, not
the core: a process that lands on an efficiency core runs more slowly and spends more CPU time,
which is likelier once the performance cores are taken. Per component, `shares.json` holds
`share` (on the task's clock), `share_cpu` and `share_wall`, each the median of the per-round
shares, the IQR and a bootstrap 95% CI, and the raw values. `plain` against `none` shows the
harness's own overhead. Each task entry also records the Python version, the machine, and a
digest of the task folder; the scorer refuses shares measured on other task files, and shares
with no `clock` (measured by wall time alone, before 2026-10-30).

**Flags** are printed and stored per task when a design target is missed: the run outside
0.5–3 s on the task's clock, the hot share below 0.5, the hot spot not the top component, a decoy
above 0.05, a CI wider than 10 points, CPU and wall shares more than 5 points apart, a load above
1.0 per performance core during the task, or (t05) the decoy not on top at the toy size. A flagged
task is retuned with its `gen_input.py` default (and the size `TASK.md` states), then measured
again. Retuning changes the digest, so the old shares stop being accepted.

## Running an agent

```bash
B=$(git rev-parse --show-toplevel)/eval/profile-first-bench
RUN=/tmp/pf-runs/plain-r1                # one folder per arm and repeat
mkdir -p "$RUN" && cp -R "$B/tasks/t04" "$RUN/"
cd "$RUN/t04" && claude -p "$(cat TASK.md)"
```

Both arms get the same `TASK.md`. Agent runs that time things belong on the machine `shares.json`
was measured on, idle, one at a time. Three repeats per task and arm make 60 runs.

## Scoring

The agent writes `ANSWER.txt` (the format is in every `TASK.md`):

```
hotspot: <file>:<function name, line number, or <module>> | <share>% | <how measured>
cleared: <file>:<function name, line number, or <module>> | <share>% | <how measured>
```

```bash
python3 -B score_answers.py /tmp/pf-runs/plain-r1 /tmp/pf-runs/skill-r1 [--json scores.json]
python3 -B score_answers.py some/dir --designed   # dry run before shares.json exists
python3 -B test_score_answers.py                  # the scorer's tests
```

Every folder under a root that holds a `TASK.md` is one run; its folder name is the task id. Each
root is reported per task and in total, then all roots together.

**Matching a line to a component**, in order:
1. the location's head, right after `file:`: a line number there inside a component's function
   (the innermost one winning; `app.py` if no file is given), or a function a component owns;
2. a function a component owns named anywhere later in the location;
3. a `line N` anywhere in the location, inside a component's function;
4. a bare helper file or `<module>` for an import component;
5. the component whose keywords appear most often in the location, when exactly one does.

Anything else is **unmatched**: naming `main` is a miss. Library frames such as
`json/encoder.py` or `logging/__init__.py` match by keyword. The head comes first because it is
what the agent chose to name, and the text after it is context: `app.py:f (consumed at line 21)`
names `f`, and `app.py:35 (before g)` names line 35, wherever line 21 or `g` sit.

**A component over several lines.** An agent may split one component into several `hotspot:`
lines (a loop and the grouping before it, or each pass of a module). The component's stated share
is then the **sum** of those lines' shares. `TASK.md` asks where the time goes, biggest first,
each line's share being how much faster the run would be without it: a breakdown into parts, and
the parts of one component together are the agent's estimate of that component. Taking the
best-matching line instead would pick, by the truth, among the agent's own numbers, and reward
listing more slices. A sum can still be moved by slices, but only by shares the agent states and
that add up. A line whose words and numbers all appear in one earlier line of the same component
(a part listed after a whole that names it, or a repeat) is not a new part and is left out of the
sum (`repeat` in `--json`). A whole listed after its parts, or a part that names its own lines,
is still counted twice: the format gives no way to tell a part from a sibling.

`top1_hit` is the first line, as it was registered before any agent ran: the task asks for the
biggest item first. `top1_by_sum_hit` is the component with the largest summed share, the same
estimate the share errors use. They differ for an answer that splits the top component into
lines each smaller than another component, and both are reported.

| Metric | Meaning |
|---|---|
| `top1_hit` | the first `hotspot:` line is the measured top component; missing and invalid answers count as misses |
| `top1_by_sum_hit` | the component with the largest summed share (a tie is none) is the measured top component |
| `topk_hit` | the top component is among the `hotspot:` lines |
| `top1_share_error_pp` | on a top-1 hit, that component's summed share minus the measured one, absolute, in percentage points |
| `mean_share_error_pp` | the same over every component the `hotspot:` lines name with a share |
| `decoy_named` | the decoy's summed share on `hotspot:` lines is ≥ `--decoy-threshold` (10%), or a line names it with none |
| `decoy_cleared` | a `cleared:` line names the decoy |
| `unmatched_items` | lines that matched no component; read them in `--json` |

For t05 and t16 it also prints how many first hot spots named the toy-size top. A changed `.py` file in a
run folder is reported, not disqualifying (the task asks for no change before measuring).
**Fails closed:** an unknown task id, a task with no measured share, shares from other task
files, or a root with no runs exits with an error.

## Known limits

- **Retuning.** Sizes are tuned to this laptop. Expect to retune some defaults on another
  machine, the likeliest being t08 (fsync speed), t09 (lzma speed, and the decoy's 5% is tight
  there), t04 and t05 (the quadratic's constant). t02's run is at the floor: 0.49 s of CPU on
  2026-11-02, flagged as just under 0.5 s.
- **A stub is cheap, not free.** Replay still loads its recording and Replace still runs an
  equivalent, so a share is understated by what the stub costs, most for the bulk-loading "other"
  components. `stub_cost.py` times a stubkit replay's load and its replayed calls on their own,
  though not the extra garbage collection a loaded recording causes during the run. Its
  2026-11-02 numbers are in the hard tier's section; two minor shares there are lower bounds.
- **Shares do not add up.** Ablations interact, and some components contain others (t02
  `load_orders` calls the decoy `parse_duration`; t01 `correct_queries` calls `spelling.correct`).
  Interpreter start-up is in every run and in no component.
- **Machine- and version-bound.** The truth holds for the Python and the machine it was measured
  on: fsync on APFS (t08), the `re` cache sizes of 3.15 (512/256; t07), lzma speed (t09). Score
  agent runs against shares measured on the machine they ran on.
- **The answer can leak.** An agent that can read this repository (a path into it, or GitHub)
  can read `lab/` and `shares.json`. Give it only the copied folder.
- **Matching is a heuristic.** An answer naming a spot the manifest does not model, or in words
  the keywords miss, scores as unmatched. Check `unmatched` in `--json` before trusting a low score.
- **One task per kind**, so a skill can overfit them; t05, t10 and t18 are the only
  anti-overfit checks.
- **t01–t10 were re-measured with the fast read** on 2026-11-02. `Ctx.load` reads a
  recording in one go and then `marshal.loads` it; it used to call `marshal.load` on the open
  file, about 7x slower, which made bulk-loading "other" components measure negative (t05
  `load_rows` −0.11, now +0.02; t03 `load_events` −0.06, now +0.02). No top component and no
  decoy verdict changed.
- **The prompt already asks for measurement.** Both arms are told to find and quantify before
  changing anything, so plain is a stronger baseline than "make it faster" from the prior-art note.
- **Not built:** the downstream metric (speed-up after one fix pass on held-out input), and
  Burchell's second check (inject a known delay into a component and confirm its share moves by it).
