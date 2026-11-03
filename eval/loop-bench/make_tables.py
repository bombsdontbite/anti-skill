"""Write every loop-bench measurement into temp/measurements.md (percentages) and temp/measurements.csv.

usage: make_tables.py   Reads runs/process_metrics.json and every runs/*/*heldout*.json; runs nothing.
A held-out result is compared with plain Claude Code scored in the same session, since levels move
between sessions on timed tasks. temp/ is gitignored: the tables are for reading, not for git.
"""
import csv
import glob
import json
import os
import re
import statistics

B = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(B))
OUT = os.path.join(ROOT, "temp")

LABEL = {("r1", "evolve"): "evolve v1", ("r1", "iter"): "plain", ("r2", "evolve"): "evolve v2", ("r2", "iter"): "plain",
         ("r3", "evolve3"): "v3", ("r4", "evolve31"): "v3.1", ("r5", "evolve2rep"): "evolve v2", ("r6", "evolve21"): "v2.1",
         ("r7", "candidate"): "v2.2", ("r8", "candidate"): "v2.3", ("r8", "candidate2"): "v2.3", ("r8", "shipped2"): "evolve v2",
         ("r9", "candidate"): "v2.4", ("r9", "candidate2"): "v2.4", ("r9", "candidate3"): "v2.4", ("r9", "sonnet"): "v2 on Sonnet",
         ("r10", "candidate"): "v2.5", ("r10", "candidate2"): "v2.5", ("r11", "candidate"): "v2.6", ("r11", "candidate2"): "v2.6",
         ("r12", "plain"): "plain", ("r12", "plain2"): "plain", ("r12", "nudge"): "nudge", ("r12", "nudge2"): "nudge",
         ("r12", "evolve"): "evolve v2", ("r12", "evolve2"): "evolve v2"}
VARIANT = {k: f"variant {k.upper()}" for k in ("c", "d", "e", "f", "g", "h", "j", "l", "m", "n")}
VARIANT["p"] = "variant N2"
VARIANT["mx"] = "variant M, take your time"
ARM_OVERRIDE = {"r18c": "variant H"}  # its folders are named g5, g6, but the queue gave them arm H


def label(run, cond):
    if (run, cond) in LABEL:
        name = LABEL[(run, cond)]
        return name + " (old brief)" if not same_brief(run) and name in ("plain", "evolve v2") else name
    if run in ARM_OVERRIDE:
        return ARM_OVERRIDE[run]
    if same_brief(run):
        for prefix, name in (("plain", "plain"), ("nudge", "nudge"), ("v2", "evolve v2")):
            if cond.startswith(prefix):
                return name
        return VARIANT.get(cond.rstrip("0123456789"), cond)
    return cond


def same_brief(run):
    """Runs 12 and later give every arm the same brief, so their plain agents are the control."""
    return int(re.match(r"r(\d+)", run).group(1)) >= 12


HIGHER_BETTER = {"cache", "dedup", "speedup", "knapsack", "regex"}  # the rest are negated costs; higher is still better
PLAIN_FINAL = "runs/r2/iter/{t}/final.py"


def pct(a, b):
    """How much better a is than b, in percent, for scores where higher is better (negatives allowed)."""
    if a is None or b in (None, 0):
        return None
    return (a - b) / abs(b) * 100


def run_of(path):
    return path.split("/")[1]


def is_same_brief_plain(path):
    run, cond = path.split("/")[1:3]
    return same_brief(run) and cond.startswith("plain")


def held_out_index():
    """path -> (session file, median, plain median in that session); the newest session wins.
    A same-brief run (12+) is compared with the mean of the same-brief plain agents in the session,
    an older run with run 2's plain final."""
    idx = {}
    for f in sorted(glob.glob(f"{B}/runs/*/*heldout*.json"), key=os.path.getmtime):
        d = json.load(open(f))
        task, res, finals = d["task"], d["results"], d["finals"]
        old = [res[k]["median"] for k, p in finals.items() if p == PLAIN_FINAL.format(t=task) and res[k]["median"] is not None]
        new = [res[k]["median"] for k, p in finals.items() if is_same_brief_plain(p) and res[k]["median"] is not None]
        for k, p in finals.items():
            ref = (statistics.mean(new) if new else None) if same_brief(run_of(p)) else (old[0] if old else None)
            idx[p] = (os.path.relpath(f, B), res[k]["median"], ref)
    return idx


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(open(f"{B}/runs/process_metrics.json"))
    idx = held_out_index()
    plain_cost = {}
    for r in rows:
        if same_brief(r["run"]) and r["cond"].startswith("plain") and "usd" in r:
            plain_cost.setdefault(r["task"], []).append((r["usd"], r["seconds"]))
    table = []
    for r in rows:
        path = f"runs/{r['run']}/{r['cond']}/{r['task']}/final.py"
        sess, ho, plain_ho = idx.get(path, (None, None, None))
        if r["task"] == "cache" and r.get("cache_heldout") is not None:  # deterministic: one scoring is exact
            ho, sess = r["cache_heldout"], "process_metrics (cache, re-scored)"
            r12p = [x["cache_heldout"] for x in rows if x["task"] == "cache" and same_brief(x["run"]) and x["cond"].startswith("plain")
                    and x.get("cache_heldout") is not None]
            plain_ho = statistics.mean(r12p) if r12p else None  # plain under the same brief
        pc = plain_cost.get(r["task"])
        pu = statistics.mean(u for u, _ in pc) if pc else None
        ps = statistics.mean(s for _, s in pc) if pc else None
        table.append({
            "task": r["task"], "run": r["run"], "cond": r["cond"], "skill": label(r["run"], r["cond"]),
            "held_out": ho, "vs_plain_pct": pct(ho, plain_ho),
            "session": sess, "budget_used_pct": round(r["calls"] / 24 * 100), "wasted_calls": r["invalid_calls"],
            "usd": r.get("usd"), "minutes": round(r["seconds"] / 60, 1) if r.get("seconds") else None,
            "usd_vs_plain_pct": pct(-r["usd"], -pu) if r.get("usd") and pu else None,
            "time_vs_plain_pct": pct(-r["seconds"], -ps) if r.get("seconds") and ps else None,
            "train_to_heldout_pct": r.get("cache_gap_pct"),
        })
    with open(f"{OUT}/measurements.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0]))
        w.writeheader()
        w.writerows(table)

    def f(v, plus=True):
        return "—" if v is None else (f"{v:+.1f}%" if plus else f"{v:.1f}")

    lines = ["# Every loop-bench measurement", "",
             "Built by `eval/loop-bench/make_tables.py` from the runs in `eval/loop-bench/runs/`. To rebuild:",
             "`python3 eval/loop-bench/make_tables.py`.", "",
             "- **vs plain**: how much better the held-out result is than plain Claude Code scored in the same",
             "  session. Runs 12 and later (one brief for every arm) are compared with the mean of the plain agents",
             "  under that brief; earlier timed tasks with run r2. Cache is deterministic, so it is compared with the",
             "  plain agents of every run from 12 on. Plus is better.",
             "- **Cost and time vs plain**: against the plain agents of runs 12 and later on the same task. Minus is",
             "  cheaper or faster, plus is dearer or slower. Only runs through `claude -p` (r8 and later) have them.",
             "- **Budget**: the share of the 24 scorer calls the agent spent.",
             "- **Train → held-out**: how much lower the held-out score is than the training one (cache only: it is deterministic).", ""]
    for task in sorted({t["task"] for t in table}):
        rs = [t for t in table if t["task"] == task]
        lines += [f"## {task}", "", "| Run | Skill | vs plain | Budget | Cost vs plain | Time vs plain | Train → held-out |",
                  "|---|---|---|---|---|---|---|"]
        for t in sorted(rs, key=lambda t: (-(t["vs_plain_pct"] if t["vs_plain_pct"] is not None else -1e9))):
            cost = f(-t["usd_vs_plain_pct"]) if t["usd_vs_plain_pct"] is not None else "—"
            tm = f(-t["time_vs_plain_pct"]) if t["time_vs_plain_pct"] is not None else "—"
            lines.append(f"| {t['run']}/{t['cond']} | {t['skill']} | {f(t['vs_plain_pct'])} | {t['budget_used_pct']}% | {cost} | {tm} | "
                         f"{f(t['train_to_heldout_pct'])} |")
        lines.append("")
    open(f"{OUT}/measurements.md", "w").write("\n".join(lines) + "\n")
    print(f"wrote {OUT}/measurements.md and measurements.csv: {len(table)} rows")


if __name__ == "__main__":
    main()
