"""Score every task's baseline twice per split, check the runs agree, write <task>/baseline.json.

Usage: nice -n 10 python3 make_baselines.py [task ...]
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = ["binpack", "tsp", "cache", "speedup", "schedule", "regex", "knapsack", "coloring",
         "dedup"]
# speedup's and dedup's scores are CPU-time ratios, so two runs agree only within timing noise.
TOLERANCE = {"speedup": 0.05, "dedup": 0.05}


def untimed(res):
    """The result without wall-clock fields, which differ between identical runs."""
    return {k: v for k, v in res["detail"].items() if "time" not in k}, res["score"]


def score(task, split):
    d = os.path.join(HERE, task)
    t0 = time.perf_counter()
    out = subprocess.run([sys.executable, "score.py", "candidate_baseline.py", "--split", split],
                         cwd=d, capture_output=True, text=True, timeout=300)
    return json.loads(out.stdout.strip().splitlines()[-1]), time.perf_counter() - t0


def main():
    tasks = sys.argv[1:] or TASKS
    ok = True
    for task in tasks:
        entry = {}
        for split in ("train", "test"):
            (a, ta), (b, tb) = score(task, split), score(task, split)
            tol = TOLERANCE.get(task, 0.0)
            same = a["valid"] and b["valid"] and abs(a["score"] - b["score"]) <= tol
            if tol == 0.0:
                same = same and untimed(a) == untimed(b)
            ok = ok and same
            entry[split] = {"valid": a["valid"], "score": a["score"],
                            "repeat_score": b["score"], "agree": same,
                            "wall_s": round(max(ta, tb), 2), "detail": a["detail"]}
            print(f"{task:9s} {split:5s} {a['score']:>10.6f} {b['score']:>10.6f} "
                  f"{'same' if same else 'DIFFERENT'} {max(ta, tb):.2f}s")
        entry["note"] = ("score is a CPU-time ratio; repeats agree within 0.05"
                         if task in TOLERANCE else "deterministic: repeat runs are identical")
        with open(os.path.join(HERE, task, "baseline.json"), "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
            f.write("\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
