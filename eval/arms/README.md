# Arms: plain Claude Code against a skill, on a measuring stick

The harness that runs a skill (profile-first, which ships, and the drafts make-scorer and
bench-fairly) against plain Claude Code, each on its own stick. Each stick has
`eval/<stick>/arms/` with `setup_arms.sh`, `judge.sh` and a README giving the order of commands.
This folder holds what they share:

| File | What |
|---|---|
| `common.sh` | sourced by every `setup_arms.sh`: the run root, the skill copy at a commit, one folder per agent under a random id, the queue, the briefs check, the run's README |
| `run_queue.sh` | the queue runner, generalised from `eval/loop-bench/run_queue.sh` |
| `progress.py` | where a queue is, read-only: agents done, the one running, the load gate or STOP, the median per agent and an estimate of the time left |
| `audit.py` | cost, result subtype and cap hits per agent and arm from `agent.json`, and the leak check over each agent's transcript |

## A run

`setup_arms.sh <run>` builds `~/aruns/<run>/` (or `$ARMS_ROOT/<run>/`), outside the repository.
Every agent sees that path in its brief, so setup refuses one that names an arm, the stick or a
skill; a neutral run name (`run-a`) gives nothing away.

```
.harness/                  everything about the run, none of it in an agent's folder:
  STICK MODEL MAX_USD LOAD_MAX [LOAD_NICE LOAD_CORES]   what the run is; the queue reads them
  README.md                skill commits, counts, estimated cost, both briefs, the queue
  queue                    <id> <case> <arm> <repeat> [<condition> <seed>], one agent a line
  skills/<name>/           the skill as tested, from `git archive` of the commit in README.md
  run_queue.sh [load.py]   copied, so no process names the repository
  queue.log probe.json     written by the queue
.pristine/<case>/          the cases as given, for restarting an interrupted agent
<id>/                      one agent, a random id: BRIEF.txt, <case>/ (its working folder), tmp/ (its TMPDIR)
                           and, in the skill arm only, <name>/ with SKILL.md, the skill's own copy
STOP                       touch it to pause; the queue touches it on a failed run
```

- **The arms differ in one line.** The skill arm's brief is the plain brief with one line put
  first, which points to its copy of the skill (`skill_line` in each `setup_arms.sh`). Setup
  checks every pair: the briefs with the agent's own path masked differ in that line only, no
  plain agent has a SKILL.md, and no name in a skill agent's folder says "skill" besides SKILL.md.
- **Pairs.** Each case runs in both arms the same number of times (`REPS`, default 2), and the
  queue alternates which arm goes first, so a queue stopped halfway leaves matched pairs.
- **Isolation is a folder, a brief and a few denied tools.** An agent sees a copy of its case
  outside the repository and is told to read nothing outside its own folder. Both arms run with
  WebSearch, WebFetch and `gh`, `curl` and `wget` in the shell denied: through them the repository,
  answer files included, is one request away. It still has a shell, so `judge.sh` runs
  `audit.py`, which flags any tool call that names the repository, a stick's answer files or the
  harness, an absolute path outside the agent's folder, `~` or `$HOME`, `find /`, or `gh`,
  `curl`, `wget`, `ps`, `pgrep` or `kill`. Read a flagged agent's calls before trusting its score.
- **Both arms load the same user-level skills and plugins** (`~/.claude`). None of them is an
  anti-skill skill.

## The queue

`zsh ~/aruns/<run>/.harness/run_queue.sh ~/aruns/<run>`, un-niced (each agent runs at nice 10):

- probes the sign-in with one `claude -p` call (about $0.08) with the agents' own flags, and
  stops if it fails;
- runs agents one at a time: `claude -p "$(<BRIEF.txt)"` in a clean `env -i`, `--permission-mode
  auto`, `--max-budget-usd $MAX_USD`, the denied tools, `--output-format json`, from the agent's
  case folder, TMPDIR the agent's `tmp/`;
- waits before each while the 1-minute load is above `LOAD_MAX`;
- skips an agent whose `agent.json` is a finished run: `is_error` false, or stopped at the cap
  (`error_max_budget_usd`, counted per arm in the audit);
- on any other result keeps the output as `agent.error.<n>.json`, logs it and touches `STOP`, so
  a usage limit or a lost sign-in halts the queue instead of running through it. Remove STOP and
  run it again to resume: an agent with `.started` is restored from `.pristine/` (and its skill
  copy from `.harness/skills/`) and starts again.

`python3 eval/arms/progress.py ~/aruns/<run>` shows where the queue is while it runs; it writes
nothing, and reads a loop-bench run (`eval/loop-bench/runs/<run>`, with a night's `guard.log`) too.
Done is what the runner would skip (a finished `agent.json`, a loop-bench `final.py`) plus the log's
`done` lines. The running agent is the log's last `start`, so a queue killed without a last line
still shows one running; a loop-bench queue run with `JOBS=N` shows every `start` not yet `done`,
back to its last `queue started` line.

`MODEL`, `LOAD_MAX`, `LOAD_NICE`, `LOAD_CORES` and `MAX_USD` (default 4, the same for both arms)
are written at setup and can be overridden in the environment.

## Counts and cost (defaults; one agent ≈ $1–2)

| Stick | Cases | Arms × repeats | Agents | Estimate | Wall, one at a time |
|---|---|---|---|---|---|
| make-scorer | 5 tasks | 2 × 2 | 20 | $30–60 (the skill arm runs make-scorer, then evolve, ≈ $2–4 each) | 7–12 h |
| bench-fairly | 32 cases, one load condition per case and repeat | 2 × 2 | 128 | $130–260 | 11–21 h |
| profile-first | 10 tasks | 2 × 2 | 40 | $40–80 | 7–13 h |

A pilot first is cheap: `TASKS=dedup REPS=1` (or `CASES=c07 REPS=1`, `TASKS=t04 REPS=1`) makes
two agents, enough to read both transcripts and see that the brief, the skill path and the judge
work end to end.
