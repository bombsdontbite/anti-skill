"""Quality against agent time: what each agent would have handed in had it stopped at minute M.

usage: time_curve.py <task> [--minutes 5,10,15,20] [--out file.json]
For every same-brief run (12+) of the task, the pick at minute M is the candidate with the best
search score among the scorer calls made by then (the baseline if none). Picks are scored on the
held-out seed; a pick whose file changed after its call is flagged, since the file on disk is not
what was scored. Timed tasks must be run on an idle machine.
"""
import argparse
import glob
import json
import os
import re
import subprocess

B = os.path.dirname(os.path.abspath(__file__))
SEED = "anti-skill-heldout-r2"

ap = argparse.ArgumentParser()
ap.add_argument("task")
ap.add_argument("--minutes", default="5,10,15,20")
ap.add_argument("--out")
a = ap.parse_args()
mins = [int(m) for m in a.minutes.split(",")]
cache = {}


def heldout(path):
    if path not in cache:
        o = subprocess.run(["nice", "-n", "10", "python3", "score.py", path, "--split", "test"], cwd=f"{B}/{a.task}",
                           env=dict(os.environ, LOOP_BENCH_TEST_SEED=SEED), capture_output=True, text=True,
                           timeout=900).stdout
        r = json.loads(o.strip().splitlines()[-1])
        cache[path] = r["score"] if r.get("valid") else None
    return cache[path]


rows = []
for aj in sorted(glob.glob(f"{B}/runs/r*/*/{a.task}/agent.json")):
    d = os.path.dirname(aj)
    run, cond = d.split("/")[-3:-1]
    if int(re.sub(r"\D", "", run)) < 12 or not os.path.getsize(aj) or not os.path.exists(f"{d}/final.py"):
        continue
    j = json.load(open(aj))
    t0 = os.path.getmtime(aj) - j["duration_ms"] / 1000
    calls = []
    for line in open(f"{d}/calls.log"):
        t, name, rest = line.split(" ", 2)
        r = json.loads(rest)
        if r.get("valid"):
            calls.append((int(t), name, r["score"]))
    row = {"run": run, "cond": cond, "minutes": round(j["duration_ms"] / 60000, 1), "final": heldout(f"{d}/final.py"),
           "at": {}, "changed_after_call": []}
    for m in mins:
        by = [c for c in calls if c[0] - t0 <= m * 60]
        if not by:
            row["at"][m] = heldout(f"{B}/{a.task}/candidate_baseline.py")
            continue
        t, name, _ = max(by, key=lambda c: c[2])
        hits = [p for p in glob.glob(f"{d}/**/{name}", recursive=True) if "__pycache__" not in p]
        if not hits:
            row["at"][m] = None
            continue
        p = min(hits, key=len)
        if os.path.getmtime(p) > t + 2:
            row["changed_after_call"].append(m)
        row["at"][m] = heldout(p)
    rows.append(row)
    print(json.dumps(row), flush=True)
if a.out:
    json.dump(rows, open(a.out, "w"), indent=1)
