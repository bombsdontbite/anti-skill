#!/bin/zsh
# usage: setup_run.sh <run-name>   — makes runs/<run>/<cond>/<task>/ workspaces
# CONDS and TASKS (space-separated) override the defaults.
set -eu
B=${0:A:h}; run=$1
for cond in ${=CONDS:-bon iter evolve}; do for t in ${=TASKS:-binpack tsp cache speedup schedule regex}; do
  w=$B/runs/$run/$cond/$t; mkdir -p $w
  cp $B/$t/TASK.md $B/$t/candidate_baseline.py $w/
  [[ -f $B/$t/train_examples.json ]] && cp $B/$t/train_examples.json $w/
  sed -i '' "s#python3 score.py \([^ ]*\) --split train#./score \1#" $w/TASK.md
  [[ $cond == bon ]] && sed -i '' 's#Score a candidate with `./score \([^`]*\)`.#(Candidates are scored later, not by you.)#' $w/TASK.md
  if [[ $cond != bon ]]; then
    cat > $w/score <<SH
#!/bin/zsh
# Scores a candidate on the search split. Budget: 24 calls; every call is logged.
set -eu
log=\${0:A:h}/calls.log; n=\$( [[ -f \$log ]] && wc -l < \$log | tr -d ' ' || echo 0 )
if (( n >= 24 )); then echo '{"valid": false, "error": "budget of 24 scorer calls used up"}'; exit 2; fi
cand=\${1:A}; out=\$(cd $B/$t && nice -n 10 python3 score.py "\$cand" --split train)
echo "\$(date +%s) \${1:t} \$out" >> \$log; echo "\$out"
SH
    chmod +x $w/score
  fi
done; done
echo made runs/$run
