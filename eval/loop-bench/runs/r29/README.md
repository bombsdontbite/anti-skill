# Run 29: S against N2, with a same-budget nudge control, on a fresh secret test seed

40 agents on claude-opus-5-5, each with the same brief (`TASK.md`), a 15-minute budget and the
same 24-call scorer cap (`score`, logged in `calls.log`), on dedup and cache, one at a time in the
interleaved order of `queue` (the runner's log of start times, `queue.log`, was not kept; each agent's wall time is `duration_ms` in its `agent.json`). The first 19 ran on the afternoon of
2026-11-02, the other 21 on the night of 2026-11-03, from the same queue. No agent failed or hit a
limit.

| folders | arm | agents per task | skill text |
|---|---|---|---|
| `n1`–`n8` | N2, the evolve that ships | 8 | `arm-n2/SKILL.md` (equal to `plugins/anti-skill/skills/evolve/SKILL.md` as it ships) |
| `s1`–`s8` | S: N2 plus four changes (the scorer may be the search signal when calls are cheap) | 8 | `arm-s/SKILL.md` |
| `u1`–`u4` | the nudge: plain plus one line, no skill | 4 | `nudge.txt`: "Do not stop at the first answer that works; keep improving it while the scorer budget lasts." |

r29 has no plain arm of its own. The plain baseline is run 28's eight plain finals per task
(`../r28/pl1`–`pl8`, the same brief, model, budget and harness), rescored here on both seeds.

## How the choice was made

The rule was written down and posted before the run started, with the script that applies it
(`decide_r29.py`, its output in `decision.out`). In short:

- the choice between S and N2 is made on the development seed only;
- S replaces N2 only if, with at least 6 agents per arm, it is ahead on dedup with a one-sided
  exact permutation p ≤ 0.10, and trails N2 on cache by at most 0.4 points;
- the secret test seed is read once, after the choice, to report each arm against plain and the
  shipped arm against the nudge.

The test seed is new for this run (`~/.config/anti-skill/test_seed_r29`, recorded in the score files
only as its fingerprint); no earlier selection has seen it.

**Decision: N2 stays.** On dedup, S was 0.4% behind N2 on the dev seed (p = 0.54). On cache it was
0.5 points ahead, within the rule.

## Results

Means per arm (dedup: median of 5 interleaved timings per final; cache: scored once, it reads no
clock), and the range across agents.

| arm | dedup dev | dedup **test** | cache dev | cache **test** |
|---|---|---|---|---|
| N2 (ships) | 86.5× (76.4–94.6) | **88.1× (77.8–96.7)** | 56.3% (54.9–57.2) | **55.1% (53.8–56.2)** |
| S | 86.1× (69.6–97.3) | 87.9× (71.1–98.8) | 56.8% (56.2–57.2) | 55.7% (54.4–56.3) |
| nudge | 79.3× (74.0–87.9) | 80.7× (75.0–90.0) | 56.0% (54.6–56.9) | 55.0% (54.1–55.9) |
| plain (r28's finals) | 70.3× (64.3–73.6) | 71.3× (65.6–74.5) | 54.9% (53.7–57.0) | 54.4% (53.5–55.3) |

On the test seed, against plain (one-sided exact permutation test on the difference of means):

| | dedup | cache |
|---|---|---|
| N2 (ships) | **+23.4%**, p < 0.001; every N2 agent beat every plain one | **+1.5%**, p = 0.022 |
| S | +23.1%, p < 0.001 | +2.4%, p = 0.002 |
| nudge | +13.1%, p = 0.002 | +1.2%, p = 0.075 |
| **N2 against the nudge** | **+9.1%, p = 0.063: beats it** | **+0.2%, p = 0.40: not separated** |

What this says:

- **On dedup, evolve beats both plain and the nudge.** About half of its gain over plain is
  what one line asking for more effort also buys; the other half is the method.
- **On cache, the gain over plain is small,** and the nudge gets about as much. That task does not
  separate evolve from simply working longer.
- **The nudge does make plain work longer.** It took 7–13 minutes on cache (plain: 2.6–6.3 in run
  28) but only 1.5–7.2 on dedup.

Wall time per agent (`duration_ms`):
- dedup: N2 5.4–11.1 minutes, S 5.7–11.1, nudge 1.5–7.2;
- cache: N2 6.2–13.6, S 5.3–9.8, nudge 7.3–12.9.

## Files

- `dedup_{dev,test}.json`, `cache_{dev,test}.json`: every final's median per seed (`heldout_compare.py`).
- `decision.out`: the pre-registered rule's output.
- `decide_r29.py`: the rule as a script.
- `arm-*`, `nudge.txt`: the texts the agents were given.

The read audit flagged one call. In it, `s1/dedup` wrote its own held-out stress file
(`stress_ho.py`) in its workspace; it read neither the scorer nor the seeds.

Left out of the commit: the audit's raw output, a queue backup and the STOP marker. They name this
checkout's absolute path or are run state.
