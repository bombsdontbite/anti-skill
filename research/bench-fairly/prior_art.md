# Prior art for `bench-fairly` (as of 2026-10-28)

Scope: the planned bench-fairly skill. The skill answers "is B faster than A?" correctly: fresh processes, warm-up,
repeats and medians, A and B interleaved, a load check, the noise floor measured first, and a
"within noise" verdict when that is the honest answer. It should drive existing tools rather than
replace them. Our own motivating data: on the shared laptop, background agents and a game shifted
CPU-time ratios by 10–20%, and identical code scored 58 and 76 in two runs.

**Tags.** **[V]** checked against the primary page this session. **[S]** taken from a search
summary; the page itself was not read. **[U]** recalled and not re-checked, so verify before
quoting. **[L]** observed on the author's Mac this session with a trivial command.

**The local machine (2026-10-28) [L].** macOS on Apple silicon, 8 logical CPUs (4 performance and
4 efficiency, from `sysctl hw.perflevel0/1.logicalcpu`). Load average was about 2.1–2.4 while a
benchmark ran. Neither `hyperfine` nor `pyperf` is installed. `/usr/bin/time -l` prints
`instructions retired` and `cycles elapsed`, which gives a hardware-counter signal with no root
and no `perf`. The repo already has its own interleaved scorer:
`eval/loop-bench/heldout_compare.py` runs the finals round-robin under `nice -n 10` and takes
medians. That is the kernel of the method, written by hand.

---

## 1. Existing tools and their methods

| Tool | Warm-up | Process model | Outliers | A-vs-B statistics | Interleaves A/B? | Noise and frequency handling | Install |
|---|---|---|---|---|---|---|---|
| **pyperf** (Python) | 1 warm-up value per process, discarded; with a JIT, 10 [V] | 20 worker processes × 3 values = 60 values by default; `--fast` 10×2, `--rigorous` 40×3; loops calibrated so one value takes ≥100 ms [V] | Warns that "the benchmark result may be unstable", e.g. when the max is 39% above the mean [V] | `compare_to`: "Student's two-sample, two-tailed t-test" at 95%; non-significant rows are hidden or marked "not significant" [V] | **No.** Reference and changed runs are sequential (`--compare-to` runs one Python, then the other) [V] | `pyperf system tune`: governor to performance, min frequency to max, Turbo Boost off, irqbalance stopped, perf sample rate down, checks AC power and ASLR [V]. **Linux only**; macOS gets only a note about third-party Turbo tools [V]. Workers are pinned only if isolated CPUs exist [V] | `pip install pyperf`, pure Python [U] |
| **hyperfine** (any command) | `--warmup N` [V] | A fresh process per run; ≥10 runs, or enough for about 3 s [V]; `--prepare` before each run, `--setup` once [V] | "Statistical outlier detection to detect interference from other programs and caching effects" — a warning, not a removal [V] | Mean ± σ and a relative "× faster" line in the tool itself; significance only in the separate `scripts/welch_ttest.py` [V] | **No.** Commands "run and appear in input order", all of A's runs, then all of B's [V] | Corrects for shell spawn time; `-N` runs without a shell [V]. No load or frequency handling | **Single binary** (prebuilt release archives, `brew`, `cargo`) [V] |
| **asv** (Python suites over commits) | `warmup_time` 0.1 s (1 s on PyPy) [V] | A new process per benchmark per round; `rounds` = 2, `repeat` (1, 5, 10 s) when rounds > 1 [V] | — | `asv compare`/`continuous`: a change is shown above `--factor` 1.1 (10%) [V], plus a Mann-Whitney U test with `p_threshold` 0.002 when there are enough samples [S] | **Partly**: rounds are the outer loop, so benchmarks are interleaved across rounds [V], but two commits are still run as separate passes [U] | `asv machine` records the machine; no tuning of its own [V] | `pip install asv`; it builds environments per commit, which is heavy [U] |
| **Google Benchmark** (C++) | `--benchmark_min_warmup_time` [U] | In-process; `--benchmark_repetitions=N` [V] | Reports mean, median and stddev aggregates [U] | `tools/compare.py`: a Mann-Whitney U test, warning it needs "no less than 9" repetitions to be meaningful [V] | **Yes**: `--benchmark_enable_random_interleaving` shuffles repetitions across benchmarks; the docs claim about 40% lower run-to-run variance (Google Benchmark issue 1051, not checked) [V] | Prints a warning when CPU scaling is enabled [U] | A C++ library you build against; not single-binary |
| **criterion.rs** (Rust) | Runs 1, 2, 4… iterations until the warm-up time passes [V]; 3 s by default [U] | In-process linear sampling, iterations d, 2d … Nd [V]; 100 samples, 5 s by default [U] | Modified Tukey: 1.5 × IQR mild, 3 × IQR severe; warned about and kept [V] | Bootstrap CIs, and a t-test over bootstrapped T-scores against the saved previous run; changes inside the noise threshold are reported as noise [V]. Defaults: noise threshold 1%, significance 0.05 [U] | **No.** It compares against the previous run's saved baseline, so drift between runs goes straight into the verdict [V by design] | None | A Cargo dev-dependency |
| **JMH** (JVM) | 5 iterations × 10 s [S] | 5 forks, fresh JVMs; 5 measurement iterations × 10 s [S] | — | Score ± error, a 99.9% CI that "assumes normal distribution" [S]; no built-in A/B test | No | Fresh JVMs are its main defence; samples document dead-code elimination and constant folding (JMH Samples) [U] | A Maven project |
| **perf stat** (Linux) | — | `-r N` repeats the command, prints mean and "+- x%" spread [V]; `--pre` hook, `-D` delay [V] | — | None; you compare two outputs by eye | No | Hardware counters (instructions, cycles) vary less than wall time [U] | Linux kernel tool; **not available on macOS** |

**What none of them does by default.** None of them checks machine load and refuses to measure.
None measures the A/A noise floor first. Only Google Benchmark (inside one binary) and asv (across
benchmarks, not across commits) interleave. hyperfine and pyperf, the two tools the skill's brief names,
both run A and then B, which is exactly the order in which a game starting halfway through biases
the verdict.

**No system install needed:** pyperf (`pip`, pure Python) and hyperfine (one static binary from
GitHub releases). On macOS the useful half of pyperf is its process model and statistics. `system
tune` does not apply.

### Direct prior art: agent skills that already do this

- **bendrucker/claude, `performance:benchmark`** (about 125 lines plus a `compare.ts` helper)
  [V, [SKILL.md](https://raw.githubusercontent.com/bendrucker/claude/main/plugins/performance/skills/benchmark/SKILL.md),
  [listing](https://www.skillsdirectory.com/skills/bendrucker-benchmark)]. It is very close to
  what the skill's brief describes:
  - arms in separate worktrees, each run once before the comparison;
  - **interleaved short hyperfine rounds in rotating order**, pooled;
  - load average recorded per round, and rounds flagged above 2× the core count;
  - an **A/A test until the arms tie**, with its ±MAD taken as the resolvable change;
  - a permutation test at α = 0.1, starred only if the effect is also ≥ 3%; unstarred means a tie
    "however large they look"; a dagger when a side has fewer than 4 runs;
  - "Back-to-back hyperfine invocations carry drift between them";
  - `/usr/bin/time -l` and work counts as fast signals.

  It needs `bun`. **No evaluation of verdict accuracy is published** (the listing shows 17 stars and
  a security scan only) [V].
- **akillness/jeo-skills, `hyperfine-benchmarking`**: warm-up 3 and min-runs 10, "prefer relative
  speedup and confidence ranges over single-run claims". No interleaving, no noise floor and no
  verdict rule. No evaluation [V,
  [page](https://claudeskills.info/zh/skills/akillness/jeo-skills/hyperfine-benchmarking/)].
- **levnikolaevich `ln-840-benchmark-compare`** compares agent setups (MCP on or off), not code
  speed. It is not relevant [V].

Sources: [pyperf system](https://pyperf.readthedocs.io/en/latest/system.html) ·
[pyperf runner](https://pyperf.readthedocs.io/en/latest/runner.html) ·
[pyperf run_benchmark](https://pyperf.readthedocs.io/en/latest/run_benchmark.html) ·
[pyperf analyze](https://pyperf.readthedocs.io/en/latest/analyze.html) ·
[hyperfine](https://github.com/sharkdp/hyperfine) ·
[hyperfine scripts](https://github.com/sharkdp/hyperfine/tree/master/scripts) ·
[asv writing benchmarks](https://asv.readthedocs.io/en/stable/writing_benchmarks.html) ·
[asv attributes](https://asv.readthedocs.io/en/stable/benchmarks.html) ·
[asv commands](https://asv.readthedocs.io/en/stable/commands.html) ·
[asv _stats](https://asv.readthedocs.io/en/stable/autoapi/asv/_stats/index.html) ·
[GB random interleaving](https://github.com/google/benchmark/blob/main/docs/random_interleaving.md) ·
[GB tools/compare.py](https://github.com/google/benchmark/blob/main/docs/tools.md) ·
[criterion analysis](https://bheisler.github.io/criterion.rs/book/analysis.html) ·
[JMH Defaults.java 1.27](https://code.yawk.at/org.openjdk.jmh/jmh-core/1.27/org/openjdk/jmh/runner/Defaults.java) ·
[perf-stat(1)](https://man7.org/linux/man-pages/man1/perf-stat.1.html)

---

## 2. Published guidance on pitfalls

- **Mytkowicz, Diwan, Hauswirth, Sweeney, "Producing Wrong Data Without Doing Anything Obviously
  Wrong!", ASPLOS 2009** [S,
  [paper](https://users.cs.northwestern.edu/~robby/courses/322-2013-spring/mytkowicz-wrong-data.pdf),
  [DOI](https://doi.org/10.1145/1508244.1508275)]. The size of the UNIX environment and the link
  order bias "does -O3 beat -O2?" enough to flip the conclusion. This held on every architecture
  tested, with both gcc and icc, and on most (or all; the two abstracts differ) SPEC CPU2006 C
  programs. Fixing the stack start address made the effect vanish, which identifies the cause as
  memory layout. Of 133 recent papers surveyed, none adequately considered this bias. Remedies:
  setup randomization and causal analysis.
  *For the skill:* run A and B from the same directory, with the same environment and the same
  argument lengths. Paths such as `./a_fast_version/` against `./b/` change the environment size.
- **Curtsinger & Berger, STABILIZER, ASPLOS 2013** [S,
  [pdf](https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf)]. Re-randomizing code,
  stack and heap layout during a run makes execution times close to Gaussian. Measured that way,
  -O3 over -O2 is "indistinguishable from random noise". The tool is unmaintained (LLVM 3.1). The
  lesson that survives: a few-percent difference in a native binary can be pure layout.
- **Barrett, Bolz-Tereick, Killick, Mount, Tratt, "Virtual Machine Warmup Blows Hot and Cold",
  OOPSLA 2017** [S, [arXiv](https://arxiv.org/abs/1602.00602),
  [summary](https://blog.acolyer.org/2017/11/07/virtual-machine-warmup-blows-hot-and-cold/)].
  Only about 30–44% of (VM, benchmark) pairs consistently reached a steady state (the percentage
  differs between versions of the paper). Almost half showed more than one performance pattern on
  the same machine. Their advice is about 10 process executions. Follow-up:
  [Tratt 2022](https://tratt.net/laurie/blog/2022/more_evidence_for_problems_in_vm_warmup.html).
  *For the skill:* "discard the first N iterations" is an assumption to check, not a rule. Fresh
  processes matter more than in-process iterations.
- **Tratt, "Minimum times tend to mislead when benchmarking" (2019)** [V,
  [post](https://tratt.net/laurie/blog/2019/minimum_times_tend_to_mislead_when_benchmarking.html)].
  The minimum assumes noise only ever slows a program down. With randomized hash seeds, the runs of
  one Rust program varied about 6–7×, and the minimum hid the typical case. Report the
  distribution and a confidence interval, not one number.
- **The counterview: Chen & Revels, "Robust benchmarking in noisy environments" (BenchmarkTools.jl,
  2016)** [V for the abstract, [arXiv](https://arxiv.org/abs/1608.04295)]. A noise model built
  from environmental fluctuations, and an estimator "insensitive to the highly nonideal statistics".
  The minimum-based estimator is [U]. Python's own `timeit` docs also say "the min() of the result
  is probably the only number you should be interested in" [V]. *The two schools disagree; the
  skill should report the median and a CI, and show the minimum only alongside them.*
- **Kalibera & Jones, "Rigorous Benchmarking in Reasonable Time", ISMM 2013** [S,
  [kar.kent.ac.uk/33611](https://kar.kent.ac.uk/33611/)]. Repetition happens at several levels:
  iterations, VM invocations and rebuilds. Spend the budget where the variance is, and report an
  effect size with a CI. Georges, Buytaert, Eeckhout, "Statistically Rigorous Java Performance
  Evaluation", OOPSLA 2007, is the older standard reference [U].
- **Randomized interleaving.** Abedi & Brecht, "Conducting Repeatable Experiments in Highly
  Variable Cloud Computing Environments", ICPE 2017 [S,
  [pdf](https://research.spec.org/icpe_proceedings/2017/proceedings/p287.pdf)]: **Randomized
  Multiple Interleaved Trials (RMIT)**. Single trials and back-to-back consecutive trials, the
  usual practice, can reach the wrong conclusion because the trial order changes the conclusion.
  Bulej et al., "Duet Benchmarking", ICPE 2020 [S, [arXiv](https://arxiv.org/abs/2001.05811)] go
  further and run A and B **simultaneously** on the same machine, so shared interference hits both.
  The reported accuracy gains are about 5× on average for ScalaBench/DaCapo and about 37× for SPEC
  CPU 2017. Laaber, Scheuner, Leitner, EMSE 2019 [S,
  [record](https://research.chalmers.se/en/publication/511491)]: cloud CV ranged from 0.03% to
  above 100%. With test and control on the same instances in randomized order, slowdowns of ≤ 10%
  were detectable with high confidence.
- **Python specifics.**
  - `timeit` "temporarily turns off garbage collection during the timing" [V,
    [docs](https://docs.python.org/3/library/timeit.html)]. Code that allocates looks faster than it
    will run. Enable it with `gc.enable()` in setup.
  - `timeit` runs in one process, so ASLR, hash-seed and layout effects are frozen into a single
    draw. pyperf's 20 processes exist "to reduce the effect of random factors like randomized
    address space layer (ASLR)" [V]. Victor Stinner's notes list as noise sources `PYTHONHASHSEED`,
    environment variables and arguments, Turbo Boost and frequency, code placement in the L1i
    cache, and the advice "sometimes, it helps to reboot" [V,
    [notes](https://vstinner.readthedocs.io/benchmark.html)].
  - Import time and interpreter start-up dominate short scripts. Timing `python script.py` with
    hyperfine measures start-up plus imports (`python -X importtime` breaks it down) [U]. pyperf
    has a `command` mode for exactly this [U].
- **Laptops and Apple silicon** [S].
  - Thermal throttling of up to about 16% single-thread on an M4 after a heavy run, and results
    that move with the surface the laptop rests on
    ([PassMark forum](https://forums.passmark.com/performancetest/58298-apple-m4-chips?p=60151)).
  - Placement on P or E cores changes completion time substantially
    ([Eclectic Light](https://eclecticlight.co/2022/10/05/making-the-most-of-apple-silicon-power-2-core-capabilities/)).
  - There is no user-level frequency pinning on macOS; pyperf's own docs check AC power because
    "the CPU speed can change when the battery level becomes too low" [V].
  - *Inference:* on this Mac interleaving is not optional, because nothing else is available. CPU
    time from `getrusage` and `instructions retired` from `/usr/bin/time -l` [L] are useful
    secondary signals. Instructions do not see cache or frequency effects, so they confirm a
    wall-time verdict but cannot replace it.

---

## 3. How LLM coding agents benchmark today (evidence)

- **Agents validate less often than humans.** "How Do Agents Perform Code Optimization?" (AIDev
  dataset, 324 agent and 83 human performance PRs): **45.7%** of agent-authored performance PRs
  include explicit performance validation, against **63.6%** for human PRs (p = 0.007) [V for the
  abstract, [arXiv 2512.21757](https://arxiv.org/abs/2512.21757)]. The abstract does not say how
  good the validation was.
- **Even hyperfine on commodity hardware produces false speedups.** PIE (Shypula et al., ICLR
  2024) benchmarked **500 pairs of identical programs** with hyperfine. The mean "speedup" was
  1.12× (sd 0.36), and the top 5% of pairs showed **1.91×**. That is why they moved to the gem5
  simulator [V, [arXiv 2302.07867 §2](https://arxiv.org/html/2302.07867)]. *This is an A/A test
  on a large scale, and it shows that a good tool used naively is not enough.*
- **The repeat discipline comes from humans, not agents.** Dan Luu (2026): one run gave 1.027 vs
  0.987, a second run reversed it, and 50 runs gave 1.03 vs 1.01. The run-to-run sd was **7.5%**,
  larger than the gap between conditions. He reran the slow outliers on a quiet machine because of
  "noise on the box" [V, [post](https://danluu.com/ai-coding/)]. (These are agent runs scored on
  speed, not timing of one function, but the noise lesson is the same.)
- **Agent-run benchmarking anecdotes.** Max Woolf (2026) had the agent use criterion to judge
  "statistically significant or just noise". He still needed a rule "NEVER run benchmarks in
  parallel" after Opus 4.5 did so and invalidated results. He also saw gamed speedups (a
  "34,500x" from disabling the physics engine, and cut training epochs) [V,
  [post](https://minimaxir.com/2026/09/agentic-iteration/)].
- **Kernel benchmarks show the same failure, louder.** KernelBench lists timing bugs where
  computation and timing run on different CUDA streams. A robust re-check of Sakana's AI CUDA
  Engineer cut the aggregate speedup from 3.13× to 1.49×, and KernelBench-Verified reports an
  identity function "speedup" of 374× [S,
  [KernelBench v0.1](https://scalingintelligence.stanford.edu/blogs/kernelbenchv01),
  [Kernel Contracts](https://arxiv.org/pdf/2604.22032),
  [KB-Verified](https://www.alphaxiv.org/abs/2607.16241)]. That is mostly correctness gaming, which
  is out of scope for bench-fairly, but it argues for a "same output?" check before timing.
- **Optimization benchmarks measure carefully; the agents inside them are not asked to.** GSO
  (NeurIPS 2025) reports < 5% OPT@1 and names "lazy optimization" and misdiagnosed bottlenecks [S,
  [arXiv 2505.23671](https://arxiv.org/abs/2505.23671)]. Its harness does the repeats; whether the
  agents' own trajectories time anything properly is not stated in what I read.
- **Not found:** a study that logs what a coding agent does when asked "is B faster than A?",
  whether it uses single `timeit` calls, how many repeats it runs, or whether it compares numbers
  across sessions. Our own runs (58 vs 76 on identical code; 10–20% ratio drift under load) are the
  only direct data, and they come from our scorer, not from plain Claude's choices. **The baseline
  behaviour of plain Claude Code is an open question that the eval in §4 must measure first.**

---

## 4. Measuring the skill: known-ratio pairs and synthetic load

**Existing methods (not datasets for agents):**
- **A/A tests** for the false-positive rate: PIE's 500 identical pairs [V], Abedi & Brecht and Duet
  [S], and Laaber 2019's false-change analysis [S].
- **Injected slowdowns of known size:** Laaber & Leitner, MSR 2018, injected slowdowns into the
  public API methods of 10 Java and Go libraries and scored a suite by the fraction it found (10% to
  100%) [S, [record](https://research.chalmers.se/en/publication/501018)]. Busy-wait injection at
  10%, 50% and 250% of a component's runtime appears in
  [arXiv 2408.08148](https://arxiv.org/pdf/2408.08148) [S].
- **Stopping by detectability:** "Stop When It Matters" (TT-MDE, ASE 2026, Distinguished Paper)
  stops a microbenchmark once a target slowdown is detectable, or declares it undetectable in the
  budget, because "a benchmark can appear stable while still being unable to reliably detect a real
  performance regression" [V for the news item,
  [UWaterloo](https://uwaterloo.ca/electrical-computer-engineering/news/performance-testing-research-earns-acm-distinguished-paper)].
  That is the formal version of "within noise".

**No existing dataset scores an agent's verdicts.** The design below is assembled from the methods
above and is my proposal.

1. **Pairs with known ratios.** Write one kernel per language (Python first) whose work scales
   linearly with a parameter, so B = A × {1.00, 1.03, 1.10, 2.00} in instructions. Confirm the
   true ratio once, on an idle machine, with a long pyperf run or `instructions retired`. Use at
   least two kernel shapes (CPU-bound arithmetic, and allocation-heavy so GC matters), and A/B
   pairs where the faster one is A as often as B.
2. **Make the answer unguessable from the source.** If the agent can read `range(1030)` against
   `range(1000)`, it will reason instead of measure. Read the parameter from an opaque data file,
   or ship two byte-identical scripts with different inputs. Name the arms neutrally (`x`, `y`) and
   randomize which is which.
3. **Load conditions:**
   - (a) idle;
   - (b) steady background load (N busy-loop processes at a fixed duty cycle);
   - (c) **drifting load that starts partway through**, which is the condition that punishes
     sequential A-then-B runs;
   - (d) load on the E cores only versus all cores.

   The load generator must log its schedule so each verdict can be matched to the load it ran under.
4. **Verdict scoring.** Three outcomes: B faster, A faster, within noise. The 1.00 pairs are
   correct only as "within noise" (this is the A/A rate). The 2.00 pairs are correct only with the
   right sign. For the 1.03 and 1.10 pairs, a sign error is wrong and "within noise" is
   acceptable; detecting 1.03 under load is a bonus, not a requirement. Count separately:
   - sign errors (the worst outcome);
   - false claims on the 1.00 pairs;
   - missed 2× differences;
   - wall-clock cost.

   A claimed magnitude whose CI excludes the true ratio is a fourth failure type.
5. **Arms and size.** Plain Claude Code against the skill, same prompt ("is y faster than x?"),
   same time budget. Every pair × load cell several times, interleaved across arms so our own eval
   is not biased by drift. A first pass at 4 ratios × 3 loads × 3 repeats × 2 arms = 72 agent
   runs. Size it against the machine-load rule: one heavy run at a time, and the load generator
   counts as one.
6. **Measure plain first.** If plain Claude Code already reaches for hyperfine with warm-up and
   gets the 1.00 and 2.00 cases right, the skill's room is only in conditions (c) and (d), and the
   eval should concentrate there.

---

## 5. Verdict

**Evidence:**
- The two named tools do not interleave A and B, check load, measure an A/A floor, or say "within
  noise" by rule. hyperfine runs A's runs and then B's [V]. pyperf runs the reference and then the
  change, and its `system tune` is Linux-only [V].
- Naive use of a good tool still lies: identical programs under hyperfine showed 1.91× in the top
  5% of 500 pairs [V].
- Interleaving and randomized order are the published fix for drifting interference, and running
  A and B simultaneously is stronger still [S].
- Agents validate performance claims less often than humans (45.7% vs 63.6%) [V].
- A public skill already does almost exactly what the skill's brief describes: bendrucker's
  `performance:benchmark`, with interleaved hyperfine rounds, an A/A floor, a permutation test and a
  3% minimum effect [V]. It has **no published accuracy evaluation**.

**Opinion:**
- "Just use pyperf/hyperfine" does not solve the problem; it solves the timing loop. The errors
  that matter here are in the protocol around the tool:
  - order (sequential runs under drift);
  - the noise floor (no A/A, so every 5% looks real);
  - the verdict (reading a mean difference as a win);
  - reusing a number from a different session.
- That protocol fits in a short skill, so there is room. But the room is narrow: the skill must
  beat a plain Claude that may already use hyperfine with `--warmup`. The likely win is in drifting
  load and on the 1.00 and 1.03 pairs, not on the 2× pair.
- Because bendrucker's skill exists, the honest framing is **"evaluate first, build second"**. Run
  §4 with plain Claude, with bendrucker's skill (it needs `bun`, so ask before installing), and with
  a minimal bench-fairly. Ship ours only if it beats both, or if it beats plain and is materially
  simpler (no `bun`, Python stdlib only).

**Minimum content, if built** (each item answers an observed failure):
1. **Same output first**: A and B produce the same result on the input, or there is nothing to
   time.
2. **Same conditions**: one working directory and one environment for both arms, fresh processes,
   and no comparison with numbers from another session or an earlier run.
3. **Load gate**: read the load average and the core count, record them per round, and wait or
   refuse above a threshold. Check AC power on a laptop.
4. **A/A first**: run A against A in the same harness, and report its spread as the resolvable
   change.
5. **Interleave**: rounds of A, B, B, A (or randomized), with several fresh processes per arm per
   round. Use hyperfine per round, or pyperf workers, or a stdlib loop like
   `heldout_compare.py`.
6. **Statistic and rule**: the median ratio with a bootstrap CI (or a Mann-Whitney or permutation
   p-value). Claim "faster" only if the CI excludes 1 **and** the effect exceeds the A/A spread;
   otherwise say "within noise" and give the number of runs that would be needed.
7. **Report shape**: the ratio, its CI, the A/A floor, the per-round load, the run count, the tool
   and its version. Never a single number.

Optional extras: `instructions retired` as a cross-check on macOS, GC enabled for Python
microbenchmarks, and a duet mode (A and B running simultaneously) as an experiment for the shared
laptop, where it may beat interleaving.
