#!/bin/zsh
# usage: judge.sh <run>   scores ~/aruns/<run> after its queue finished. Writes
# <run>/judge/summary.json and copies the light part of the run to eval/profile-first-bench/arms/runs/<run>/.
# score_answers.py reads only the staged copy: each agent's top-level TASK.md and ANSWER.txt and its
# .py files (for the changed-file report), so a scratch copy of the task cannot be scored as a run.
# DESIGNED=1 scores against the designed hot spots, for a dry run before shares.json exists.
set -eu
B=${0:A:h:h}; E=${B:h}; run=${1:?usage: judge.sh <run>}
R=${ARMS_ROOT:-$HOME/aruns}/$run; H=$R/.harness; J=$R/judge; S=$J/stage
[[ $(<$H/STICK) == profile-first ]] || { echo "$R is not a profile-first run" >&2; exit 2; }
rm -rf $S; mkdir -p $S; : > $J/excluded.txt
while read -r id t arm rep rest; do
  [[ -n $id ]] || continue
  d=$arm/r$rep-$t
  [[ -f $R/$id/agent.json ]] || { echo "$d ($id) not run" >> $J/excluded.txt; continue; }
  mkdir -p $S/$d/$t
  rsync -a --prune-empty-dirs --include=/TASK.md --include=/ANSWER.txt --exclude=TASK.md --include='*/' \
    --include='*.py' --exclude='*' $R/$id/$t/ $S/$d/$t/
done < $H/queue
roots=(); for arm in plain skill; do if [[ -d $S/$arm ]]; then roots+=($S/$arm); fi; done
python3 -B $B/score_answers.py $roots ${DESIGNED:+--designed} --json $J/answers.json

python3 -B $E/arms/audit.py $R > $J/audit.json
python3 -B - $R $B/shares.json <<'EOF'
import json, os, platform, sys
R, shares = sys.argv[1], sys.argv[2]; J = os.path.join(R, "judge")
au = json.load(open(os.path.join(J, "audit.json")))
audit = {a["agent"]: a for a in au["agents"]}
scores = json.load(open(os.path.join(J, "answers.json")))
stage = os.path.join(J, "stage")
report = {os.path.relpath(k, stage) if k != "ALL" else k: v for k, v in scores["report"].items()}
runs = {os.path.relpath(os.path.dirname(r["run"]), stage): r for r in scores["runs"]}
envs = ({t: v.get("env") for t, v in json.load(open(shares))["tasks"].items()}
        if os.path.exists(shares) else "no shares.json: scored with --designed")
here = {"python": platform.python_version(), "machine": platform.machine()}
pairs = {"both_top1": 0, "only_plain": 0, "only_skill": 0, "neither": 0}
for d, r in runs.items():
    s = runs.get("skill/" + d[6:]) if d.startswith("plain/") else None
    if s:
        p, q = bool(r.get("top1")), bool(s.get("top1"))
        pairs["both_top1" if p and q else "only_plain" if p else "only_skill" if q else "neither"] += 1
out = {"stick": "profile-first", "run": os.path.basename(R), "report": report,
       "paired_top1": pairs, "audit_by_arm": au["by_arm"],
       "shares_env": envs, "judge_env": here,
       "excluded": open(os.path.join(J, "excluded.txt")).read().splitlines(),
       "leak_flagged": sorted(k for k, a in audit.items() if a.get("leak_flags")),
       "agents": [{"agent": k, **{x: runs.get(k, {}).get(x) for x in ("task", "status", "top1", "topk",
                   "top1_share_error", "decoy_named", "decoy_cleared", "unmatched", "modified")},
                   **{x: a.get(x) for x in ("id", "ran", "is_error", "subtype", "usd", "minutes", "turns")}}
                  for k, a in audit.items()],
       "notes": ["report: score_answers.py per arm root and ALL",
                 "audit_by_arm: cost, cap hits (error_max_budget_usd) and set-aside failures per arm",
                 "unmatched items score as misses: read them before trusting a low score (stick README)",
                 "shares_env should match judge_env and the machine the agents ran on",
                 "leak_flagged: read judge/audit.json before trusting those runs"]}
json.dump(out, open(os.path.join(J, "summary.json"), "w"), indent=1)
print(json.dumps({"paired_top1": pairs, "audit_by_arm": au["by_arm"], "excluded": len(out["excluded"])},
                 indent=1))
EOF
O=${ARMS_COPY:-$B/arms/runs/$run}; mkdir -p $O
rsync -a --max-size=1m --exclude tmp/ --exclude .pristine/ --exclude stage/ --exclude __pycache__ \
  --exclude .started $R/ $O/
echo "summary: $J/summary.json; light copy in $O"
