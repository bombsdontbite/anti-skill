# profile-first: prior art (as of 2026-10-28)

Research pass on 2026-10-28 for the profile-first skill, web only, about 45 tool calls, nothing installed or run.
The question: before anything is sped up, can a small skill make Claude Code profile on realistic
inputs and name the real hot spots with their share of time, more often than plain Claude Code
does? In the stack it comes first: **profile-first → make-scorer (with bench-fairly) → evolve**.

Already covered elsewhere and not repeated here:
- [`research/make-scorer/prior_art.md`](../make-scorer/prior_art.md) §1.1 (CodSpeed skills) and §3
  (what agents do with "make it faster": the AIDev PR study, PIE's A/A noise, GSO hacks).
- [`research/bench-fairly/prior_art.md`](../bench-fairly/prior_art.md) §3 (how agents benchmark).

**Tags.**
- **[V]** read from the primary source (paper HTML, repo README, official docs) this session.
- **[S]** from a search summary or a secondary page only; check before quoting.
- **[U]** recalled, not re-read.

---

## 1. Profilers and their trade-offs

### 1.1 Python

| Tool | Kind | Overhead / distortion | Install | macOS without sudo | Import time | I/O wait | C extensions |
|---|---|---|---|---|---|---|---|
| **cProfile / pstats** (3.15: `profiling.tracing`, `cProfile` kept as alias) | Deterministic, every call event | Django test: **84%** overhead vs pyinstrument 30% [V, [pyinstrument](https://pyinstrument.readthedocs.io/en/latest/how-it-works.html)]; pystone 1.65× [S, Scalene README]. Inflates code with many small calls, which "might lead you to optimise the wrong part of your program" [V, same page] | Stdlib | Yes (in-process) | Only if the import runs under the profiler; no per-module split [U] | Counts as wall time inside the blocking call [U] | Builtins appear as one entry (`builtins` switch) [V, [docs](https://docs.python.org/3.15/library/profiling.tracing.html)]; time inside the extension is opaque; PerfAgent: cProfile "sees only Python-layer frames" [V] |
| **profiling.sampling** ("Tachyon", new in **3.15**, final released 2026-10-09 [S]) | Sampling, out-of-process | "virtually zero" on the target; `--blocking` slows it [V, [docs](https://docs.python.org/3.15/library/profiling.sampling.html)] | Stdlib (3.15+ only; profiler and target must be the same minor version) [V] | **No**: `task_for_pid()` needs root, the debugger entitlement, or SIP off [V]; also for `run`, per [pydevtools](https://pydevtools.com/handbook/reference/profiling-sampling.md) [S] | Startup is sampled like anything else | **Best of the set**: `--mode wall/cpu/gil/exception`; the docs' example shows a sleep at ~98% in wall mode and absent in cpu mode [V] | `--native` adds `<native>` frames [V] |
| **py-spy** | Sampling, out-of-process (Rust) | "extremely low overhead"; pauses target per sample unless `--nonblocking` [V, [README](https://github.com/benfred/py-spy)]; 1.0–1.08× [S, Scalene paper/README] | `pip install py-spy` (wheel) or a single binary [V] | **No**: "OSX always requires running as root"; SIP blocks `/usr/bin` Python even for root [V] | Sampled | Idle threads dropped by default, `--idle` keeps them; `--gil` [V] | `--native` [V]; `--subprocesses` [V]; CPython up to 3.15 [V] |
| **pyinstrument** | Statistical via `PyEval_SetProfile`, a reading every 1 ms [V] | 30% in the Django test [V]; long calls are "bunched up" at their end [V] | pip | Yes (in-process; inferred, the docs do not discuss it) [U] | Sampled if under the profiler | **Wall-clock by design**: DB, files and network count [V] | Not discussed [V]; time attributed to the calling Python frame [U] |
| **Scalene** | Sampling (signals), line + function [V, [README](https://github.com/plasma-umass/scalene)] | "typically no more than 10-20%"; README's own Pyperformance run shows 35% [V] | pip or conda [V] | README names no sudo need [V]; in-process [U] | — | **Splits Python / native / system time** [V] | Native time separated; memory, copy volume, NVIDIA GPU [V]; has built-in LLM "optimize this line" suggestions [V] |
| **yappi** | Tracing (deterministic) [V, [README](https://github.com/sumerc/yappi)] | "Fast"; no numbers [V]; 3.2–3.6× per Scalene paper [S] | pip | Yes | — | Wall or CPU clock selectable; asyncio/gevent-aware wall time per coroutine [V] | — |
| **line_profiler** | Deterministic per line, decorated functions only [V, [README](https://github.com/pyutils/line_profiler)] | Not stated [V]; 2.2× (paper) or 11.6× (README benchmark) [S] | pip, Python ≥ 3.10 [V] | Yes | — | — | — |
| **memray** | Allocation tracer, memory only [V, [README](https://github.com/bloomberg/memray)] | "slows the application only slightly", no numbers [V] | pip wheels, Linux and macOS only [V] | Yes [V: no sudo mentioned] | — | — | `--native` C/C++ frames [V] |
| **tracemalloc** | Allocation tracer, stdlib | More frames cost more memory and CPU [V, [docs](https://docs.python.org/3/library/tracemalloc.html)] | Stdlib | Yes | — | — | Hooks Python's allocators only; raw `malloc` in C is not seen unless the extension uses a domain [V + inference] |
| **`-X importtime`** | Per-module import timer, stdlib | Negligible [U] | Stdlib (3.7+) [V] | Yes | **The one tool for it**: self and cumulative time per module; `=2` (3.14+) marks cached imports [V, [docs](https://docs.python.org/3/using/cmdline.html)]; units are µs [U]; "may be broken in multi-threaded application" [V] | — | — |

**What follows for the skill.**
- **On this Mac, without sudo, the free options are in-process ones:** cProfile, `-X importtime`,
  tracemalloc (stdlib) and pyinstrument or Scalene (pip). The two best out-of-process samplers,
  py-spy and 3.15's Tachyon, need root on macOS [V]. On Linux they need nothing extra to launch a
  child [S].
- **The stdlib-only path is cProfile + `-X importtime` + wall timing.** cProfile's known bias is
  exactly the decoy this skill must survive: a loop of many cheap calls inflates under
  tracing [V]. So a cProfile ranking needs a cross-check that does not use the profiler (§4.2).
- **Wall vs CPU** is the I/O question. Only Tachyon (modes), yappi (clock type), pyinstrument
  (wall by design) and Scalene (system-time column) make it explicit [V].

### 1.2 The general family

| Tool | Platform and privileges | Notes |
|---|---|---|
| **perf** | Linux; unprivileged use needs `kernel.perf_event_paranoid` lowered or `CAP_PERFMON` [V, via samply README] | Python 3.12+ `-X perf`, 3.13+ `-X perf_jit` make Python frames visible; "only available on some platforms" [V, [cmdline docs](https://docs.python.org/3/using/cmdline.html)] |
| **samply** | macOS, Linux, Windows; single binary via install script or `cargo install` [V, [README](https://github.com/mstange/samply)] | 1 kHz; opens the Firefox Profiler locally. macOS: launching needs no setup; attaching needs `samply setup` (self-sign); **system `python` and `sleep` cannot be profiled** (signing blocks `DYLD_INSERT_LIBRARIES`). Off-CPU samples on macOS and Windows, on-CPU only on Linux [V]. No Python frame support documented [V] |
| **Instruments / `xctrace`** | macOS, ships with Xcode [U] | Time Profiler sampling; own processes without sudo [U] |
| **async-profiler** | JVM; Linux and macOS builds [V, [README](https://github.com/async-profiler/async-profiler)] | No safepoint bias; native and kernel frames [V]; mode support on macOS in a separate doc, not read [V] |
| **pprof** | Go: `runtime/pprof` and `net/http/pprof` built in; `go tool pprof` reads it [U] | CPU sampling at 100 Hz by default [U] |

**Profilers are themselves wrong, measurably.**
- Four Java profilers "disagree dramatically" on the hottest method; safepoint-biased sampling is
  the cause (Mytkowicz et al., PLDI 2010) [S, [abstract](https://evaluate.inf.usi.ch/node/5)].
- The 2023 re-test (Burchell, Larose, Kaleba, Marr, MPLR '23; async-profiler, Honest Profiler,
  JFR, JProfiler, perf, YourKit): one profiler names the same hottest method fairly reliably
  across 30 runs, but profilers "cannot reliably agree on the set of top 5 hottest methods"; a
  method's share varied **>15 percentage points** between runs for every profiler; JFR named
  **8 different** hottest methods across 30 runs of DeltaBlue [V, [post](https://stefan-marr.de/2023/09/dont-blindly-trust-your-profiler/)].
  Advice: do not rely on one profile.
- **Hot is not the same as payoff** (Coz, Curtsinger and Berger, SOSP 2015) [V, [ar5iv](https://ar5iv.arxiv.org/html/1608.03676)]:
  - SQLite: perf gave the three functions Coz flagged **0.15%** of runtime; fixing them gave a
    **25.6% ± 1.0%** speedup.
  - dedup: gprof gave the code 0.48%; the fix gave 8.95%.
  - ferret: gprof's output was "virtually unchanged" after a 21.27% speedup.
  - These are multithreaded C programs. In a single-threaded Python script share ≈ payoff is a
    much safer assumption, but not for code that waits on threads, processes or I/O [U, opinion].

---

## 2. Existing skills, plugins, MCP servers and prompts

| Item | What it does | Share of time? | Realistic input? | Import/setup split? | Evidence it works |
|---|---|---|---|---|---|
| **CodSpeed `codspeed-optimize`** ([SKILL.md](https://raw.githubusercontent.com/CodSpeedHQ/codspeed/main/skills/codspeed-optimize/SKILL.md)) [V] | "Measure first, optimize second"; the flamegraph "tells you where the time actually goes, and it's often not where you'd guess"; "Rank functions by self time. The top 2-3 are your targets"; "Never optimize based on intuition alone" | No: rank, no percentage | Via its setup skill's benchmarks | No | None published |
| **wshobson `python-performance-optimization`** ([SKILL.md](https://raw.githubusercontent.com/wshobson/agents/main/plugins/python-development/skills/python-performance-optimization/SKILL.md)) [V] | ~500 words; "Profile before optimizing"; names cProfile and py-spy; lists "Optimizing without profiling" as a pitfall | No | No | No | None |
| **ln-811-performance-profiler** ([skills.sh](https://skills.sh/levnikolaevich/claude-code-skills/ln-811-performance-profiler)) [S] | "Discover test → Baseline run → Static analysis → Deep profile → Performance map → Report"; 184 installs, 584 stars | Not stated | "from real data", unspecified | No | None |
| Dozens of marketplace "performance-profiler / perf-agent / performance-engineer" skills and subagents (tbhb/rig `profiling-practices`, claude-howto, zebbern, proflead's Codex `performance-trace-guide`, …) [S, search pages] | Same slogan: measure before optimising, then a tool list | Not found | Not found | Not found | None found |
| **Codeflash Claude Code plugin** ([usage guide](https://docs.codeflash.ai/claude-code-plugin/usage-guide)) [V] | `/optimize` runs `codeflash --subagent`; scope is **changed files, a file, a function or `--all`**: chosen by diff or by the user, not by a profile. `codeflash optimize script.py` traces a run and makes replay tests [S, docs] | No | Trace mode only | No | Vendor claims only |
| **Scalene's own AI button** [V, README] | LLM proposes an optimisation for a line or region the profile shows | Profile shows % | User's run | — | None published |
| **Scalene-MCP** (ptmorris05, pip `scalene-mcp`) [S, [glama](https://glama.ai/mcp/servers/@ptmorris05/scalene-mcp)]; **pyspy-mcp** (LBurny, `top_profile`) [S]; **Grafana mcp-grafana** Pyroscope tools (fetch profile, labels) [S] | Expose a profiler or a continuous-profiling store to the agent | Yes, raw | User decides | No | None; one promotional "38 min → 42 s triage" claim, unverifiable [S] |
| **PerfAgent** (research, [arXiv 2607.19653](https://arxiv.org/html/2607.19653)) [V] | py-spy at 100 Hz over a 10 s repeated workload; **setup samples discarded**; hot spots with stack, **share of samples**, library flag, self and total time; an LLM call condenses it; a controller intercepts "done", re-profiles, up to 5 rounds | **Yes** | Uses the task's workload | **Yes** (setup dropped) | §3; not packaged as a skill. A blog ports the idea to Codex CLI `PostToolUse` hooks [S, [post](https://codex.danielvaughan.com/2026/08/06/perfagent-profiler-guided-iterative-refinement-codex-cli-performance-optimization-postooluse-hooks/)] |

**What users say.** No measured user report was found of a profiling skill beating an agent
without one, or of Claude Code naming the wrong hot spot and a profile correcting it. Reddit and X
were not searchable. The nearest anecdote: Russ Poldrack (2026-08-04) asked his coding agent to
build examples of major Python bottlenecks, and "the bottlenecks didn't actually occur": the
patterns had been slow once, but current CPython had optimised them away [V, [post](https://russpoldrack.substack.com/p/code-profiling)].
An agent's sense of what is slow is a stale prior.

**Gap (evidence).** Every skill found says "profile first". None found asks for **each hot spot's
share of total time**, separates **import/startup** from steady state, demands **production-sized
inputs**, checks a ranking with a **second method**, or reports the **decoys it cleared**. The one
system that does most of this (PerfAgent) is a research harness, not a skill.

---

## 3. Evidence that developers and agents optimise the wrong place

### 3.1 Agents (all on real repositories with expert patches)

- **SWE-fficiency** (Ma et al., ICML 2026, 498 tasks in numpy, pandas, scipy and six others) [V, [arXiv 2511.06090](https://arxiv.org/html/2511.06090)]:
  - Agents reach "less than 0.23× the expert speedup"; best was Claude 4.5 Opus at 0.225×.
  - "over 68% of expert gains occur in functions the LM never edits".
  - Models "choose the wrong function" about **69–73% of the time** (mean ≈ 71%); function-level
    Expert-Relative Coverage 0.25–0.31; they pick the right *file* about 55–64% of the time
    (Table 9: Claude 3.7 Sonnet, GPT-5 Mini, Gemini 2.5 Flash, DeepSeek V3.1).
  - The paper does not report whether the agents profiled.
- **GSO** (Shetty et al., NeurIPS 2025, 102 tasks) [V, [arXiv 2505.23671](https://arxiv.org/html/2505.23671v3)]:
  - Best Opt@1 under 5%.
  - Working at the wrong abstraction level "contributes to 25-30% of agent failures"; O4-Mini
    shows lazy optimisation in nearly 30% of trajectories; bottleneck localisation is described
    qualitatively. Example: parallelising NumPy's `char.count` while ignoring the GIL and
    process overhead.
  - No profiler-use rate reported.
- **PerfAgent** (Deng et al., 2026, GPT-5.1) [V]:
  - Baselines "often either skip profiling entirely or reach for Python's built-in cProfile".
  - Agents "prematurely terminate optimizing after shallow speedups" and "overlook hotspots
    hidden inside native extensions".
  - **Ablation (hack-adjusted Opt@1):**

    | Variant | GSO | SWE-fficiency-Lite |
    |---|---|---|
    | OpenHands baseline | 19.6 | 26 |
    | **Profiler instructions in the prompt only** | **16.7** | **44** |
    | Loop with timing feedback | 29.4 | 46 |
    | + test feedback | 20.6 | 46 |
    | + profiler feedback | 34.4 | 57 |
    | Full PerfAgent | 39.2 | 74 |

  - The prompt-only row is the nearest published analogue of a skill: it **helped on
    SWE-fficiency-Lite (26 → 44) and hurt on GSO (19.6 → 16.7)**. Profiler feedback inside a loop
    helped on both.
- **AIDev performance PRs** (Peng et al., MSR '26) [V, [arXiv 2512.21757](https://arxiv.org/html/2512.21757v1)]:
  of validated agent PRs, **67.2% validated by static reasoning** (humans 44.9%), benchmarks 25%
  (humans 49%). The paper does not count profiler use or say whether PRs hit a bottleneck.
- **Codeflash** (vendor blog, 2026-02-26) restates SWE-fficiency: "Models frequently optimized the
  wrong functions entirely" [V as a claim, [post](https://www.codeflash.ai/blog-posts/hidden-cost-of-coding-agents)].
- **LLMs reading code vs reading a profile** (Bolet et al., [arXiv 2505.03988](https://arxiv.org/abs/2505.03988)):
  classifying GPU kernels as compute- or bandwidth-bound from source reached up to 64%, and 100%
  given explicit profiling data [S]. Different domain, same direction.

### 3.2 Humans and the "premature optimisation" literature

- **Knuth 1971**, "An empirical study of FORTRAN programs" (SP&E 1:105–133): the paper's main
  conclusion is the value of a program profile [S]. The famous "a few per cent of the code takes
  half the time" figure: a comp.compilers reading says most examples are near 50%, one at 90% [S].
  Not re-read.
- **Knuth 1974**, "Structured Programming with go to Statements": the "premature optimization"
  and "critical 3%" passage, and "the universal experience of programmers who have been using
  measurement tools has been that their intuitive guesses fail" [S: wording from a quotes page;
  the PDF scan could not be read here]. This is an expert's experience, not a measured rate.
- **Nistor, Jiang, Tan, MSR 2013** (Eclipse JDT, SWT, Mozilla): a large share of performance bugs
  are found **by code reasoning**, not by profiling or by users noticing [S]. A counterweight: static
  reading does find real performance bugs. It finds them; it does not rank them.
- **No controlled study was found** that measures how often human developers guess the hottest
  function correctly before profiling. The folklore is strong; the data is Coz's and the profiler
  studies' (§1.2), which show that even profiles mislead.

---

## 4. How to measure the skill

### 4.1 Existing datasets with labelled hot spots

| Source | Label | Fit | Cost here |
|---|---|---|---|
| **SWE-fficiency** [V] | Expert speedup mass per function, from the evaluators' function-level profiler before and after the gold patch: the closest thing to "true share" in a public set | Best real-world ground truth; its ERC metric is directly reusable | Heavy: per-task containers that build numpy/pandas/scipy. Not on this laptop |
| **GSO** [V] | Expert commit + performance test | Localisation only by diff overlap | Heavy, same reason |
| **SWE-Perf** ([arXiv 2507.12415](https://arxiv.org/abs/2507.12415)) [S] | 140 PRs with "target functions" | Function-level target labels | Heavy; a later audit reportedly found many reference speedups do not replicate across machines [S] |
| **Coz case studies** [V] | Profiler share vs measured payoff | Best illustration of "hot ≠ payoff" | C/C++, Linux; illustrative, not a benchmark |
| **Burchell et al. 2023** [S] | Ground truth by **injecting known slowdowns** into basic blocks | A method to copy, not a dataset | Java |

**Nothing found** in the shape the skill's benchmark needs: small, stdlib-only programs with a non-obvious hot spot,
a decoy, and a measured share.

### 4.2 Proposed benchmark (opinion; design)

**Ground truth by ablation, not by a profiler.** For each program, the true share of component C
is `1 − T(program with C replaced by a precomputed stub with the same output) / T(program)`.
Use the median of ≥5 interleaved runs on an idle machine, the bench-fairly rules. This avoids
circularity (scoring a profiler-using skill against a profiler's own answer) and dodges cProfile's
distortion. Burchell's inject-a-known-delay method gives a second check: add 50 ms to C and verify
that the measured share moves accordingly.

**Each task is one entry point, one realistic input description, one real hot spot and one
scary-but-cheap decoy.** Stdlib only, under 10 s per run, like loop-bench.

| # | Real hot spot (target share ≥ 50%) | Decoy that looks slow but is cheap (≤ 5%) | What it tests |
|---|---|---|---|
| 1 | **Import time**: a module-level table built at import, or a heavy import chain, in a CLI run once per call | Triple-nested loop over a 10×10×10 grid | `-X importtime`, startup vs steady state |
| 2 | **Serialisation**: `json.dumps(..., indent=2, sort_keys=True, default=handler)` of the result | Hand-written parser loop over the input | Time outside "the algorithm" |
| 3 | **Allocation**: `result = result + [x]` or `copy.deepcopy` per record in a helper | Regex match inside the main loop | Allocation hidden in a helper |
| 4 | **Hidden O(n²)**: `if x not in seen_list` or `list.pop(0)` inside `normalise()` | An obvious `for i … for j …` over a fixed 50-element list | The classic |
| 5 | **Input-size trap**: same as 4, but the O(n²) only dominates at the production size stated in the ticket; at the repo's toy fixture, the decoy dominates | Decoy dominates on the toy input | "Realistic inputs": profiling the fixture gives the wrong answer |
| 6 | **Logging**: a DEBUG-level handler writing and flushing per record, or eager f-string formatting of a large repr | `time.sleep(0)`-style "yield" calls, string formatting in the hot loop | Cost in a library call the code does not own |
| 7 | **Regex compiled per item with a dynamic pattern** (defeats the `re` cache) | `re.compile(CONSTANT)` inside a loop: cached by `re`, so cheap [U: cache size 512 in recent CPython, verify] | The agent "fixes" the cached compile and misses the dynamic one |
| 8 | **I/O wait**: a `subprocess.run` or `fsync` per batch | A CPU-heavy-looking pure-Python checksum | Wall vs CPU: a CPU-only view names the checksum |
| 9 | **Many tiny calls under cProfile**: real hot spot is one builtin-heavy call (`sorted` with a `key=lambda`) | A loop of 10⁶ trivial Python calls that cProfile inflates | Profiler distortion; needs a cross-check |
| 10 | Control: the obvious loop really is the hot spot | — | Guards against a skill that always says "not the loop" |

**Metrics, skill vs plain, same prompt "make this faster", same budget:**
1. **Top-1 hit**: the first hot spot named (or first edited, for plain) is the ablation's top
   component.
2. **Share error**: |named share − ablation share|, for the skill only (plain rarely states a share).
3. **Decoy edit rate**: did the run change the decoy?
4. **Downstream**: speedup after one fixed evolve or plain fix pass, held-out input, median of 5.
5. Tasks 5 and 10 are the anti-overfit checks: a skill that always distrusts the obvious, or
   always runs the bundled fixture, fails one of them.

Runs: 10 tasks × 2 arms × ≥3 seeds = 60 agent runs, each scored by a stdlib script. Light on CPU
except during the scoring runs, which must be on an idle machine.

---

## 5. Verdict

**Evidence.**
- Agents optimise the wrong function most of the time on real repositories: about 71% wrong
  function on SWE-fficiency, and over 68% of the expert gain lies in functions the agent never
  touches [V].
- Agents mostly validate by static reasoning [V], and when they profile they reach for cProfile,
  which misses native frames [V] and inflates many-small-call code [V].
- Profile feedback **inside a loop with the stop intercepted** roughly doubled expert-matching
  patches (GSO 19.6 → 39.2, SWE-fficiency-Lite 26 → 74) [V].
- **Profiler instructions in the prompt alone were mixed**: +18 points on one benchmark, −3 on the
  other [V]. A skill is closer to that row than to the full system, so "tell it to profile" is not
  enough on its own.
- Every published skill found already says "profile first" and none publishes a number [V/S].
  The slogan is a commodity; a measured result is not.
- Profilers disagree with each other and with themselves by >15 points of share [V], and a hot
  function is not always the payoff [V].

**Opinion.**
- There is room, but not for another "measure first" paragraph. The win has to come from things
  plain Claude Code and the existing skills do not do, which are exactly PerfAgent's ingredients
  minus the controller:
  1. **A runner script, not prose**: run the user's entry point on a production-sized input,
     drop setup, print a top-k table with **share of wall time and of CPU time**, plus a separate
     `-X importtime` line. Stdlib by default (cProfile + importtime + wall clock), and
     pyinstrument or Scalene if present. Never assume sudo on macOS.
  2. **A second method for the top candidate**: stub it and time end-to-end (the ablation in
     §4.2). This defeats cProfile's distortion and the "hot ≠ payoff" case at little cost.
  3. **The report before any edit**: hot spot, share, method, run-to-run spread, and the decoys
     it measured and cleared ("the nested loop: 2%").
  4. **A stop gate**: "done" only after re-profiling shows the named hot spot's share fell. This
     is the part of PerfAgent's gain a skill can imitate without a harness.
- The bar for shipping: on the §4.2 set, a higher top-1 hit rate and a lower decoy edit rate
  than plain over ≥3 seeds, **without losing task 10**. If plain Claude Code already profiles
  well on these tasks, the skill should be dropped with those numbers, as its brief says.
- Expected weak spot: if plain Opus already runs cProfile when asked, the skill's edge narrows to
  tasks 1, 5, 8 and 9 (import time, input size, I/O wait, profiler distortion). Those four are the
  ones to build first.
