"""Score several finals of one task on a held-out seed, interleaved, and print each median.

usage: heldout_compare.py <task> <reps> label=path [label=path ...]
                          [--seed S | --seed-file F] [--out file.json]
Interleaving puts machine-load drift on every column alike; compare only columns of one call.
The default seed, run 2's, is the development seed: variants were chosen on it, so it cannot
report a claim. --seed-file reads a secret test seed that no selection has seen; only its
fingerprint is printed or written.
"""
import hashlib
import argparse
import json
import os
import statistics
import subprocess

B = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("task")
ap.add_argument("reps", type=int)
ap.add_argument("finals", nargs="+")
g = ap.add_mutually_exclusive_group()
g.add_argument("--seed", default="anti-skill-heldout-r2")
g.add_argument("--seed-file")
ap.add_argument("--out")
a = ap.parse_args()

finals = dict(f.split("=", 1) for f in a.finals)
seed, seed_label = a.seed, a.seed
if a.seed_file:
    seed = open(os.path.expanduser(a.seed_file)).read().strip()
    if len(seed) < 16:
        raise SystemExit("the test seed must be at least 16 characters")
    seed_label = "secret:" + hashlib.sha256(seed.encode()).hexdigest()[:12]
env = dict(os.environ, LOOP_BENCH_TEST_SEED=seed)
runs = {k: [] for k in finals}
for _ in range(a.reps):
    for k, p in finals.items():
        p = p if os.path.isabs(p) else os.path.join(B, p)
        out = subprocess.run(["nice", "-n", "10", "python3", "score.py", p, "--split", "test"],
                             cwd=os.path.join(B, a.task), env=env, capture_output=True, text=True,
                             timeout=900).stdout
        r = json.loads(out.strip().splitlines()[-1])
        runs[k].append(r["score"] if r.get("valid") else None)
res = {k: {"runs": v, "median": statistics.median([x for x in v if x is not None]) if any(
    x is not None for x in v) else None, "invalid": sum(x is None for x in v)} for k, v in runs.items()}
for k, r in sorted(res.items(), key=lambda kv: -(kv[1]["median"] or -1e18)):
    print(f"{k:12} median {r['median']}  invalid {r['invalid']}  runs {r['runs']}")
if a.out:
    json.dump({"task": a.task, "seed": seed_label, "reps": a.reps, "finals": finals,
               "results": res}, open(a.out, "w"), indent=1)
