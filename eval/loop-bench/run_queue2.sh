#!/bin/zsh
# Runs loop-bench agents one at a time with `claude -p`, so a queue survives without a live session.
# usage: run_queue.sh <run>   reads runs/<run>/queue (lines: <cond>/<task> <arm> [model])
# <arm>: a SKILL.md to follow, a .txt whose text is added to the brief, SKILL.md+extra.txt for both, or - for none.
# Skips entries whose final.py exists; stops when runs/<run>/STOP exists. Waits while load > 6.
set -u
B=${0:A:h}; run=$1; R=$B/runs/$run; log=$R/queue.log
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
while read -r entry skill model; do
  [[ -z $entry || $entry == \#* ]] && continue
  [[ -e $R/STOP ]] && { echo "$(date +%T) STOP file found" >> $log; break; }
  w=$R/$entry; t=${entry:t}
  [[ -f $w/final.py ]] && { echo "$(date +%T) skip $entry (final.py exists)" >> $log; continue; }
  while (( $(sysctl -n vm.loadavg | awk '{print int($2)}') > 6 )); do sleep 60; done
  model=${model:-claude-opus-5-5}
  # The arm is the only difference between conditions: a skill file to follow, a text file whose
  # content is added as-is (a nudge), or "-" for nothing (plain).
  case $skill in
    -) arm="" ;;
    *.md+*.txt) arm=" Read ${skill%%+*} and follow it; it and the files beside it are the only files outside that folder you may read. $(cat ${skill#*+})" ;;
    *.txt) arm=" $(cat $skill)" ;;
    *) arm=" Read $skill and follow it; it and the files beside it are the only files outside that folder you may read." ;;
  esac
  brief="Work only in $w/ and read no other file outside it. Read TASK.md and candidate_baseline.py there and solve the task as well as you can.${arm} You may score candidates with ./score <absolute-path-to-file>: it scores the search split, hard budget of 24 calls. The baseline's search score is ${BASE[$t]}. The final score is taken later on instances you have not seen. Put your final answer in final.py. The laptop is shared: run at most one Python process at a time, always with \`nice -n 19\`, keep each local run under about 20 seconds, nothing in parallel or in the background. Report your final search score and calls used."
  echo "$(date +%T) start $entry on $model ($(sysctl -n vm.loadavg))" >> $log
  (cd $w && nice -n 10 $cl -p "$brief" --model $model --permission-mode auto \
     --disallowedTools ${DENY[@]} --output-format json < /dev/null > agent.json 2> agent.err)
  rc=$?
  echo "$(date +%T) done $entry exit=$rc final=$([[ -f $w/final.py ]] && echo yes || echo no)" >> $log
done < $R/queue
echo "$(date +%T) queue finished" >> $log
# The deny list cannot stop `cat` in Bash, so every queue ends with a read of the agents' own transcripts.
python3 $B/audit_reads.py --runs ${${run#r}%%[a-z]*}-${${run#r}%%[a-z]*} --out $R/audit.json 2>&1 | tail -1 | sed "s/^/$(date +%T) audit: /" >> $log
