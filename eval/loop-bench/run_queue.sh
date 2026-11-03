#!/bin/zsh
# Runs loop-bench agents with `claude -p`, so a queue survives without a live session.
# usage: [JOBS=n] run_queue.sh <run>   reads runs/<run>/queue (lines: <cond>/<task> <arm> [model])
# <arm>: a SKILL.md to follow, a .txt whose text is added to the brief, or - for none.
# JOBS agents (default 1) run at once, started in queue order. Each start claims its entry with
# mkdir runs/<run>/.claims/<cond>__<task>, outside the workspace, removed when the agent ends; a
# claim left by a killed runner skips that entry until you rmdir it, once no agent runs there.
# Skips entries whose final.py exists; stops when runs/<run>/STOP exists. Waits while load > 6.
set -u
B=${0:A:h}; run=$1; R=$B/runs/$run; log=$R/queue.log; JOBS=${JOBS:-1}
[[ $JOBS == <1-> ]] || { echo "run_queue.sh: JOBS must be a whole number from 1, not '$JOBS'" >&2; exit 2; }
# A clean environment: started from inside the desktop app, claude inherits its child-session
# variables and tries the app's expired token instead of the CLI's own sign-in.
# No web, no GitHub, no reading the scorers or the bench README (they hold the test seeds and generators).
DENY=(WebSearch WebFetch 'Bash(gh *)' 'Bash(curl *)' 'Bash(wget *)' "Read(/$B/*/score.py)" "Read(/$B/_bench.py)" "Read(/$B/README.md)")
cl=(env -i HOME=$HOME USER=$USER LOGNAME=$USER PATH=$PATH TERM=xterm-256color LANG=en_US.UTF-8 claude)
typeset -A BASE
BASE=(dedup "about 1.0 (no call needed); one scorer run takes tens of seconds" speedup "about 1.0 (no call needed)"
      schedule "-1.0 (no call needed)" tsp "-1.0 (no call needed)" knapsack "1.0 (no call needed)"
      cache "0.365 (no call needed)" binpack "about -1.04 (no call needed)" coloring "-1.0 (no call needed)"
      regex "0.6405 (no call needed)")
$cl -p "Reply with the single word ok." --model claude-opus-5-5 --output-format json < /dev/null \
  > $R/probe.json 2> $R/probe.err
if ! python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1])).get("is_error", True))' $R/probe.json 2>/dev/null; then
  echo "$(date +%T) claude -p failed; see probe.json and probe.err; queue not started" | tee -a $log >&2
  exit 1
fi
# Marks a restart for eval/arms/progress.py, which otherwise cannot tell a killed agent from a running one.
(( JOBS > 1 )) && echo "$(date +%T) queue started, jobs=$JOBS" >> $log
mkdir -p $R/.claims
agent() {  # <entry> <workspace> <model> <brief> <claim>
  (cd $2 && nice -n 10 $cl -p "$4" --model $3 --permission-mode auto \
     --disallowedTools ${DENY[@]} --output-format json < /dev/null > agent.json 2> agent.err)
  local rc=$?
  echo "$(date +%T) done $1 exit=$rc final=$([[ -f $2/final.py ]] && echo yes || echo no)" >> $log
  rmdir $5 2>/dev/null
}
pids=()
while read -r entry skill model; do
  [[ -z $entry || $entry == \#* ]] && continue
  while (( $#pids >= JOBS )); do
    alive=(); for p in $pids; do kill -0 $p 2>/dev/null && alive+=($p); done; pids=($alive)
    (( $#pids >= JOBS )) && sleep 1
  done
  [[ -e $R/STOP ]] && { echo "$(date +%T) STOP file found" >> $log; break; }
  w=$R/$entry; t=${entry:t}
  [[ -f $w/final.py ]] && { echo "$(date +%T) skip $entry (final.py exists)" >> $log; continue; }
  while (( $(sysctl -n vm.loadavg | awk '{print int($2)}') > 6 )); do sleep 60; done
  # Claims live outside the workspace, so the agent's folder holds nothing earlier runs lacked.
  c=$R/.claims/${entry//\//__}
  if ! mkdir $c 2>/dev/null; then
    echo "$(date +%T) skip $entry (claimed: $c exists)" >> $log; continue
  fi
  model=${model:-claude-opus-5-5}
  # The arm is the only difference between conditions: a skill file to follow, a text file whose
  # content is added as-is (a nudge), or "-" for nothing (plain).
  case $skill in
    -) arm="" ;;
    *.txt) arm=" $(cat $skill)" ;;
    *) arm=" Read $skill and follow it; it and the files beside it are the only files outside that folder you may read." ;;
  esac
  brief="Work only in $w/ and read no other file outside it. Read TASK.md and candidate_baseline.py there and solve the task as well as you can.${arm} You may score candidates with ./score <absolute-path-to-file>: it scores the search split, hard budget of 24 calls. The baseline's search score is ${BASE[$t]}. The final score is taken later on instances you have not seen. Put your final answer in final.py. The laptop is shared: run at most one Python process at a time, always with \`nice -n 19\`, keep each local run under about 20 seconds, nothing in parallel or in the background. Report your final search score and calls used."
  # jobs=N goes last on the line, so readers of the one-at-a-time format still match.
  echo "$(date +%T) start $entry on $model ($(sysctl -n vm.loadavg))$( (( JOBS > 1 )) && echo " jobs=$JOBS")" >> $log
  if (( JOBS > 1 )); then
    agent $entry $w $model $brief $c & pids+=($!)
  else
    agent $entry $w $model $brief $c
  fi
done < $R/queue
wait
echo "$(date +%T) queue finished" >> $log
# The deny list cannot stop `cat` in Bash, so every queue ends with a read of the agents' own transcripts.
python3 $B/audit_reads.py --runs ${${run#r}%%[a-z]*}-${${run#r}%%[a-z]*} --out $R/audit.json 2>&1 | tail -1 | sed "s/^/$(date +%T) audit: /" >> $log
