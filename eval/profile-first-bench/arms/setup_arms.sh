#!/bin/zsh
# usage: setup_arms.sh <run>   makes ~/aruns/<run>/<id>/ per agent and .harness/queue.
# TASKS, REPS, PF_REF (the skill's commit), MODEL, MAX_USD and LOAD_MAX override the defaults.
# Refuses to start unless shares.json has an entry for every task, measured on today's task files,
# with a clock, and without an error: agent runs belong after the measurement they are scored against.
STICK=profile-first
source ${0:A:h:h:h}/arms/common.sh
B=${0:A:h:h}
tasks=(${=TASKS:-t01 t02 t03 t04 t05 t06 t07 t08 t09 t10})
[[ -n ${NO_SHARES_OK:-} ]] || python3 -B - $B $tasks <<'EOF' || exit 2
import json, os, sys
B, tids = sys.argv[1], sys.argv[2:]
sys.path.insert(0, os.path.join(B, "lab"))
from runner import task_digest  # noqa: E402
p = os.path.join(B, "shares.json")
if not os.path.exists(p):
    sys.exit(f"no {p}: run measure_shares.py first (arms/README.md)")
data = json.load(open(p))["tasks"]
bad = [f"{t}: not measured" for t in tids if t not in data]
for t, e in sorted(data.items()):
    if "error" in e or "error" in e.get("toy", {}):
        bad.append(f"{t}: {e.get('error') or e['toy']['error']}")
    elif e.get("task_digest") != task_digest(t):
        bad.append(f"{t}: measured on other task files (digest {e.get('task_digest')}, now {task_digest(t)})")
    elif "clock" not in e:
        bad.append(f"{t}: measured by wall time alone, before CPU-time shares")
if bad:
    sys.exit("shares.json cannot score this run; measure again:\n  " + "\n  ".join(bad))
EOF

skill_line() {
  print -r -- "Read $1/profile-first/SKILL.md and follow it for this task; its scripts are in that folder."
}
brief_body() {
  print -r -- "The task is in $2/: read TASK.md there and do what it asks. Read no file outside $1/. Keep your work in $2/ (temporary files may go in \$TMPDIR). The laptop is shared: run one process at a time, nothing in parallel or in the background. Nobody will answer questions during this run."
}

arms_begin $1 1.5
skill_at ${PF_REF:-HEAD} profile-first
for rep in {1..${REPS:-2}}; do
  for i in {1..$#tasks}; do
    t=$tasks[i]
    order=(plain skill); (( (i + rep) % 2 )) && order=(skill plain)
    for arm in $order; do agent_add $arm $rep $t $B/tasks/$t; done
  done
done
arms_finish 1 2 "Agents time things, so the queue belongs on the machine \`shares.json\` was measured on, idle
(the gate waits for a 1-minute load ≤ $GATE). TMPDIR is \`<agent>/tmp\` in both arms. Judge
with \`eval/profile-first-bench/arms/judge.sh $run\`."
