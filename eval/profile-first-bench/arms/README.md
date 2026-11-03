# profile-first arms

Plain Claude Code against profile-first on the ten original tasks, two repeats each: **40 agents,
about $40–80, 7–13 h**. Shared harness: `eval/arms/README.md`. For the hard tier, set
`TASKS="t11 t12 t13 t14 t15 t16 t17 t18"` (32 agents).

- **Both arms** get a copy of `tasks/<task>/` and the same brief: do what `TASK.md` asks, keep
  work in the folder, temporary files in `$TMPDIR` (the agent's own `tmp/`), one process at a time.
- **The skill arm** also gets `profile-first/` (`plugins/anti-skill/skills/profile-first/` at
  `HEAD`, or at the commit in `PF_REF`) and one line first: read the skill and follow it.

## On an idle machine, in this order

The shares come first: the agents are scored against them, on this machine and these task files.
`setup_arms.sh` refuses to start unless `shares.json` has every task, each measured on the task
files as they are now (its `task_digest`), with the clock it was timed on (`clock`), and none with an `error`.

```bash
cd "$(git rev-parse --show-toplevel)" && git fetch origin
uptime                                                   # measure_shares.py refuses above 0.75 per P core
cd eval/profile-first-bench
python3 -B smoke.py                                      # stubs still match; a few seconds
python3 -B measure_shares.py                             # 10–15 min; read every flag it prints
cd ../..
```

A flag (the run outside 0.5–3 s, a hot share below 0.5, a decoy above 0.05, a wide CI) means a
task gets retuned and measured again, in a change of its own, before any agent runs. Retuning
changes the task's digest, and the scorer then refuses the old shares. With no flags left, commit
`shares.json`, then:

```bash
zsh eval/profile-first-bench/arms/setup_arms.sh run-c    # refuses on a missing, stale or failed share
less ~/aruns/run-c/.harness/README.md
nohup zsh ~/aruns/run-c/.harness/run_queue.sh ~/aruns/run-c \
  > ~/aruns/run-c/.harness/nohup.out 2>&1 &              # the gate waits for a load ≤ 1.5
tail -f ~/aruns/run-c/.harness/queue.log
zsh eval/profile-first-bench/arms/judge.sh run-c         # after "queue finished"; seconds
```

`judge.sh` stages each agent's top-level `TASK.md` and `ANSWER.txt` and its `.py` files, then
runs `score_answers.py` with one root per arm. The summary has its report (per task and in
total, per arm and all), the pairs where only one arm's first hot spot was the top component,
cost and cap hits per arm, the Python and machine `shares.json` was measured on beside the judge's, and leak
flags. `DESIGNED=1` scores against the designed hot spots instead, for a dry run only. Commit
`runs/<run>/` with its judge summary.

## What this run cannot tell apart

- **Unmatched items score as misses.** Read `unmatched` in the summary before trusting a low
  score (`../README.md`, Known limits).
- **The prompt already asks for measurement**, so plain is a stronger baseline than "make it
  faster".
- **The skill's stop gate is not exercised.** The task stops at the report, before any edit.
