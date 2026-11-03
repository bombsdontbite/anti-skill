# Run 28: evolve's claim, scored once on a secret test seed

The night of 2026-11-02: 64 agents on claude-opus-5-5, each with the same brief (`TASK.md`), a
15-minute budget and the same 24-call scorer cap (`score`, logged in `calls.log`), on dedup and
cache, run one at a time in the interleaved order of `queue` (the runner's log of start times, `queue.log`, was not kept; each agent's wall time is `duration_ms` in its `agent.json`). No
agent failed or hit a limit.

| folders | arm | agents per task | skill text |
|---|---|---|---|
| `pl1`–`pl8` | plain Claude Code | 8 | none |
| `p9`–`p12` | N2, the evolve that ships | 4 | `../r27/arm-n2/SKILL.md` (see below for how the shipped text differs) |
| `q1`–`q8` | Q: N2 with a written backlog of 6–8 different approaches | 8 | `arm-q/SKILL.md` |
| `r1`–`r8` | R: Q plus a fixed end reserve in minutes | 8 | `arm-r/SKILL.md` |
| `s1`–`s4` | S: the scorer may be the search signal when calls are cheap | 4 | `arm-s/SKILL.md` |

**Shipped against tested.** `plugins/anti-skill/skills/evolve/SKILL.md` is N2 with one cut. N2's
"Other skills' files" paragraph tells the agent how to use a `scorer/` folder written by
make-scorer, which does not ship, so after this run the paragraph was cut to its
`profile/result.json` sentence, which now names profile-first as that file's source. With it went the Budget paragraph's clause on that folder, and the
Budget paragraph's "step 5" now reads "§4, item 5". No task here has a `scorer/` or `profile/`
folder, so the cut text never applied in these runs. Everything else, §4's stop rule included, is
N2's word for word.

Every final was first scored on the development seed (`*_dev.json`) and the arms were chosen
on it. Only then were the same finals scored on a secret test seed (`*_test.json`). Those files
record the seed only as its fingerprint, `secret:94f4ba725d15`; the seed itself is not in the
repository. dedup is the median of 5 interleaved timings per final, and cache, which reads no
clock, is scored once. The files also score older finals (r27c, r27, r27b, r15, r17) in the same
call; the figures below use r28's agents only.

Means per arm, and % against plain's mean on the same seed:

| arm | dedup dev | dedup **test** | cache dev | cache **test** |
|---|---|---|---|---|
| S | 84.7× | 85.3× (+21.2%) | 56.3% | 55.2% (+2.3%) |
| N2 | 82.1× | **82.3× (+16.9%)** | 56.7% | **55.6% (+3.0%)** |
| R | 80.3× | 81.1× (+15.2%) | 56.4% | 55.0% (+1.8%) |
| Q | 80.1× | 80.9× (+14.9%) | 56.2% | 55.2% (+2.2%) |
| plain | 70.3× | 70.4× | 54.9% | 54.0% |

Per agent on the test seed: N2's dedup finals run at 75.4–92.1× and plain's at 64.7–74.1×, so
every N2 agent beat every plain one. On cache the ranges overlap: N2 53.9–56.4%, plain
53.2–56.0%.

Wall time per agent (`duration_ms` in each `agent.json`): plain took 0.8–1.5 minutes on dedup
and 2.6–6.3 on cache, N2 6.2–9.4 and 7.6–9.9. Plain stops well inside its 15 minutes, so part of
the gap may be time spent rather than the method; a plain control made to use the whole budget
has not been run.

**Decision (on the dev seed):** Q and R beat N2 on neither task and are closed. S leads on dedup
but trails on cache with only 4 agents: a candidate for a larger round against N2, not a ship.
N2 stays. The test seed agrees with the dev seed on every ordering.

## Which file backs which README figure

- "82.3× against 70.4×", "16.9% faster": `dedup_test.json`, the means of `r28p9`–`r28p12`
  against `r28pl1`–`r28pl8` (the same medians, sorted, in `dedup_test.out`).
- "55.6% against 54.0%", "1.6 points, or 3.0% more hits": `cache_test.json` (and
  `cache_test.out`), the same agents.
- "4 evolve agents against 8 plain", the per-agent ranges and the wall times: the folders above.

Left out of the commit: the read audit's raw output, a queue backup and one binary profile dump,
which name this checkout's absolute path.
