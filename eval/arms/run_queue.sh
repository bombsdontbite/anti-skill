#!/bin/zsh
# Runs one arms run's agents one at a time with `claude -p`. Generalised from
# eval/loop-bench/run_queue.sh: the brief comes from each agent's BRIEF.txt, and a queue line may
# name a load condition, which wraps the agent in load.py (bench-fairly).
# usage: run_queue.sh <run-root>   (setup_arms.sh copies this file to <run-root>/.harness/)
#   .harness/queue lines: <id> <case> <arm> <repeat> [<condition> <seed>]; the agent works in <id>/<case>.
# Skips agents whose agent.json is a finished run. A failed run's agent.json is kept as
# agent.error.<n>.json and STOP is touched, so a usage limit or a lost sign-in halts the queue; an
# agent started before starts again from the pristine case. Stops when <run-root>/STOP exists.
# Waits while the 1-minute load is above LOAD_MAX.
set -u
R=${1:?usage: run_queue.sh <run-root>}; R=${R:A}; H=$R/.harness; log=$H/queue.log
model=${MODEL:-$(<$H/MODEL)}; loadmax=${LOAD_MAX:-$(<$H/LOAD_MAX)}; maxusd=${MAX_USD:-$(<$H/MAX_USD)}
lnice=${LOAD_NICE:-$(cat $H/LOAD_NICE 2>/dev/null || echo 10)}
lcores=${LOAD_CORES:-$(cat $H/LOAD_CORES 2>/dev/null || echo 2)}
# A clean environment: started from inside the desktop app, claude inherits its child-session
# variables and tries the app's expired token instead of the CLI's own sign-in.
cl=(env -i HOME=$HOME USER=$USER LOGNAME=$USER PATH=$PATH TERM=xterm-256color LANG=en_US.UTF-8)
# The same flags for the probe and every agent in both arms.
flags=(--model $model --permission-mode auto --max-budget-usd $maxusd
       --disallowedTools WebSearch WebFetch 'Bash(gh *)' 'Bash(curl *)' 'Bash(wget *)'
       --output-format json)

finished() {  # <agent.json>: a run that ended, or one stopped at the cost cap
  python3 -c 'import json,sys
r = json.load(open(sys.argv[1]))
sys.exit(0 if r.get("is_error") is False or r.get("subtype") == "error_max_budget_usd" else 1)' $1 2>/dev/null
}
set_aside() {  # <agent-dir>: keeps a failed run's output; prints its number
  local n=1
  while [[ -e $1/agent.error.$n.json ]]; do (( n++ )); done
  mv $1/agent.json $1/agent.error.$n.json
  [[ -e $1/agent.err ]] && mv $1/agent.err $1/agent.error.$n.err
  echo $n
}

$cl claude -p "Reply with the single word ok." $flags < /dev/null > $H/probe.json 2> $H/probe.err
if ! python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1])).get("is_error") is not False)' $H/probe.json 2>/dev/null; then
  echo "$(date +%T) claude -p failed; see .harness/probe.json and probe.err; queue not started" | tee -a $log >&2
  exit 1
fi
echo "$(date +%T) queue started on $model, load gate $loadmax, cap \$$maxusd" >> $log
while read -r id c arm rep cond seed; do
  [[ -z $id || $id == \#* ]] && continue
  [[ -e $R/STOP ]] && { echo "$(date +%T) STOP file found" >> $log; break; }
  A=$R/$id; w=$A/$c
  if [[ -e $A/agent.json ]]; then
    if finished $A/agent.json; then echo "$(date +%T) skip $id (finished)" >> $log; continue; fi
    echo "$(date +%T) $id: unfinished agent.json kept as agent.error.$(set_aside $A).json" >> $log
  fi
  if [[ -e $A/.started ]]; then
    for f in $A/*(DN); do
      case ${f:t} in BRIEF.txt|.started|agent.error.*) ;; *) rm -rf $f ;; esac
    done
    cp -R $R/.pristine/$c $w && mkdir $A/tmp
    if [[ $arm == skill ]]; then for s in $H/skills/*(/N); do cp -R $s $A/${s:t}; done; fi
    echo "$(date +%T) restart $id from the pristine case" >> $log
  fi
  while sysctl -n vm.loadavg | awk -v m=$loadmax '{exit !($2 > m)}'; do sleep 60; done
  touch $A/.started
  agent=($cl TMPDIR=$A/tmp claude -p "$(<$A/BRIEF.txt)" $flags)
  echo "$(date +%T) start $id ${cond:+under $cond }($(sysctl -n vm.loadavg))" >> $log
  if [[ -n ${cond:-} ]]; then
    # Start the queue un-niced: load.py's workers then sit at the run's LOAD_NICE, the agent at 10.
    (cd $w && python3 $H/load.py --condition $cond --seed $seed --nice $lnice --cores $lcores \
       --max-secs 7200 --log $w/LOAD.json -- nice -n 10 $agent < /dev/null > $A/agent.json 2> $A/agent.err)
  else
    (cd $w && nice -n 10 $agent < /dev/null > $A/agent.json 2> $A/agent.err)
  fi
  rc=$?
  if finished $A/agent.json; then
    echo "$(date +%T) done $id exit=$rc" >> $log
  else
    echo "$(date +%T) error $id exit=$rc: kept as agent.error.$(set_aside $A).json; STOP touched" >> $log
    touch $R/STOP; break
  fi
done < $H/queue
if [[ -e $R/STOP ]]; then echo "$(date +%T) queue stopped" >> $log; else echo "$(date +%T) queue finished" >> $log; fi
