"""Scripted profilers: does a tier tell a casual profile from a careful measurement, with no agent?

usage: nice -n 10 python3 -B measurers.py OUT [--tier old|hard|all] [--strategies S,S]
                                          [--rounds 3] [--force] [tasks ...]
       python3 -B measurers.py --summary OUT [--designed] [--shares shares.json]

Each (strategy, task) gets a fresh copy of the task folder in OUT/<strategy>/<task>/ and an
ANSWER.txt written there, so score_answers.py scores it like an agent's run.
- casual: one `python3 -m cProfile` run on the input you get without reading TASK.md's sizes (the
  generator's defaults, or the fixture a task ships with), then the top `tottime` row. A builtin
  or library row is charged to its biggest caller in the task's files; a row that names no
  component (main, the entry script's <module>) is skipped.
- casual-cum: the same profile, the task-file row with the largest `cumtime` that names a component.
- casual-prod: casual, on the input size and shape TASK.md states (tells size traps from
  profiler traps).
- careful: the bench's ablation (measure_shares.measure_size) at the stated input, --rounds
  rounds, every component named with its share, biggest first.
"""
import argparse
import json
import os
import pstats
import shutil
import subprocess
import sys

BENCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BENCH, "lab"))
import measure_shares as ms  # noqa: E402
import runner  # noqa: E402
import score_answers as sa  # noqa: E402

STRATEGIES = ("casual", "casual-cum", "casual-prod", "careful")


def tier_of(spec):
    return spec.get("tier", "old")


def copy_task(tid, d):
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(os.path.join(runner.TASKS, tid), d, ignore=shutil.ignore_patterns("__pycache__"))


def write_answer(d, lines, note):
    with open(os.path.join(d, "ANSWER.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(d, "MEASURE.json"), "w", encoding="utf-8") as f:
        json.dump(note, f, indent=2)


def profile(tid, spec, gen, args, d):
    """Copy, generate, one cProfile run; returns the stats dict and the copy's real path."""
    copy_task(tid, d)
    if gen is not None:
        subprocess.run([sys.executable, "gen_input.py", *gen], cwd=d, check=True,
                       stdout=subprocess.DEVNULL, timeout=600)
    subprocess.run([sys.executable, "-m", "cProfile", "-o", "prof.out", spec["entry"], *args], cwd=d,
                   check=True, stdout=subprocess.DEVNULL, timeout=600)
    return pstats.Stats(os.path.join(d, "prof.out")).stats, os.path.realpath(d)


def task_frame(key, root):
    path = key[0]
    if path == "~" or path.startswith("<"):
        return None
    full = os.path.realpath(os.path.join(root, path))
    return os.path.relpath(full, root) if full.startswith(root + os.sep) else None


def owner(key, stats, root):
    """The first frame in the task's files on the path to key, following the biggest caller."""
    seen = set()
    while key not in seen:
        seen.add(key)
        rel = task_frame(key, root)
        if rel:
            return key, rel
        callers = stats.get(key, (0, 0, 0, 0, {}))[4]
        if not callers:
            return None
        key = max(callers, key=lambda c: callers[c][3])
    return None


def located(key, rel):
    name = key[2]
    return f"{rel}:<module>" if name == "<module>" else f"{rel}:{key[1]} {name}"


def pick(stats, root, spec, comp_spans, col):
    """(where, component, share) for the first row by column col (2 tottime, 3 cumtime) that names
    a component. tottime rows outside the task's files are charged to their biggest caller there;
    cumtime only reads rows in the task's files."""
    total = sum(v[2] for v in stats.values()) or 1
    for key in sorted(stats, key=lambda k: -stats[k][col]):
        share = round(100 * stats[key][col] / total, 1)
        rel = task_frame(key, root)
        if col == 2 and not rel:
            # A library or builtin row is read as what it says first (logging, json, bz2) ...
            where = library_label(key)
            comp = sa.match(where, spec, comp_spans)
            if comp:
                return where, comp, share
            found = owner(key, stats, root)  # ... else charged to the task code that called it
        else:
            found = (key, rel) if rel else None
        if not found:
            continue
        where = located(*found)
        comp = sa.match(where, spec, comp_spans)
        if comp:
            return where, comp, share
    return None, None, None


def library_label(key):
    path, line, name = key
    if path == "~":
        return name
    return f"{'/'.join(path.split(os.sep)[-2:])}:{line} {name}"


def casual_input(spec):
    toy = runner.sizes(spec, tiny=False)
    by = {label: (gen, args) for label, gen, args in toy}
    return by.get("toy", by["prod"])


def run_casual(out, tid, spec, strategies):
    comp_spans = sa.spans(tid, spec)
    inputs = {"shipped": casual_input(spec), "stated": (spec["gen"], spec["args"])}
    plans = [(s, size, col) for s, size, col in (("casual", "shipped", 2), ("casual-cum", "shipped", 3),
                                                  ("casual-prod", "stated", 2)) if s in strategies]
    profiles = {}
    for strat, size, col in plans:
        key = "shipped" if inputs[size] == inputs["shipped"] else size
        gen, args = inputs[key]
        if key not in profiles:
            profiles[key] = profile(tid, spec, gen, args, os.path.join(out, ".profiles", key, tid))
        stats, root = profiles[key]
        where, comp, share = pick(stats, root, spec, comp_spans, col)
        d = os.path.join(out, strat, tid)
        copy_task(tid, d)
        how = f"cProfile {'tottime' if col == 2 else 'cumtime'}, input {' '.join(gen) if gen else ' '.join(args)}"
        write_answer(d, [f"hotspot: {where} | {share}% | {how}"] if where else [],
                     {"strategy": strat, "input": [gen, args], "where": where, "component": comp,
                      "share_of_profile": share})
        print(f"{strat:12s} {tid}: {comp}  ({where}, {share}%)", flush=True)


def run_careful(out, tid, spec, rounds):
    d = os.path.join(out, "careful", tid)
    copy_task(tid, d)
    res = ms.measure_size(tid, spec, "careful", spec["gen"], spec["args"], rounds, f"{tid}-careful")
    if "error" in res:
        raise SystemExit(f"{tid}: {res['error']}")
    shares = {c: v["share"]["median"] for c, v in res["components"].items()}
    ranked = sorted(shares, key=lambda c: -shares[c])
    lines = []
    for c in ranked[:5]:
        if c == ranked[0] or shares[c] >= 0.02:
            lines.append(f"hotspot: {where_of(spec, c)} | {100 * shares[c]:.1f}% | ablation, {rounds} rounds")
    for c, cs in spec["components"].items():
        if cs["role"] == "decoy" and shares[c] < 0.05:
            lines.append(f"cleared: {where_of(spec, c)} | {100 * shares[c]:.1f}% | ablation, {rounds} rounds")
    write_answer(d, lines, {"strategy": "careful", "rounds": rounds, "shares": shares, "top": res["top"],
                            "cpu_secs": res["cpu_secs"], "load_avg": res["load_avg"]})
    print(f"{'careful':12s} {tid}: {res['top']}  {json.dumps({c: round(s, 3) for c, s in shares.items()})}",
          flush=True)


def where_of(spec, comp):
    for w in spec["components"][comp]["where"]:
        if "func" in w:
            return f"{w['file']}:{w['func']}"
    w = spec["components"][comp]["where"][0]
    return f"{w['file']}:<module>" if set(w) == {"file"} else w["file"]


def summary(out, designed, shares_path):
    m = runner.manifest()
    truth = sa.truths(m, shares_path, designed)
    table = {}
    for strat in sorted(os.listdir(out)):
        root = os.path.join(out, strat)
        if strat.startswith(".") or not os.path.isdir(root):
            continue
        for tid in sorted(os.listdir(root)):
            d = os.path.join(root, tid)
            if tid not in m["tasks"] or not os.path.exists(os.path.join(d, "TASK.md")):
                continue
            if tid not in truth:
                raise SystemExit(f"{d}: no measured share for {tid}; measure it or pass --designed")
            r = sa.score_run(d, tid, m["tasks"][tid], truth[tid], 10.0)
            tier = tier_of(m["tasks"][tid])
            table.setdefault(strat, {}).setdefault(tier, []).append((tid, bool(r.get("top1"))))
    print("strategy\ttier\ttop1\truns\tmisses")
    for strat, tiers in table.items():
        for tier in sorted(tiers):
            rows = tiers[tier]
            hits = sum(h for _, h in rows)
            print(f"{strat}\t{tier}\t{100 * hits / len(rows):.0f}%\t{len(rows)}\t"
                  + ",".join(t for t, h in rows if not h))
    return table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("tasks", nargs="*")
    ap.add_argument("--tier", choices=["old", "hard", "all"], default="all")
    ap.add_argument("--strategies", default=",".join(STRATEGIES))
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--max-load-per-core", type=float, default=0.75)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--designed", action="store_true")
    ap.add_argument("--shares", default=os.path.join(BENCH, "shares.json"))
    a = ap.parse_args()
    if a.summary:
        summary(a.out, a.designed, a.shares)
        return
    strategies = a.strategies.split(",")
    unknown = set(strategies) - set(STRATEGIES)
    if unknown:
        raise SystemExit(f"unknown strategies {sorted(unknown)}")
    cores = ms.perf_cores()
    load = os.getloadavg()[0]
    if "careful" in strategies and load / cores > a.max_load_per_core and not a.force:
        raise SystemExit(f"load {load:.2f} on {cores} performance cores; wait, or --force")
    runner.lower_priority()
    m = runner.manifest()["tasks"]
    ids = a.tasks or sorted(t for t in m if a.tier == "all" or tier_of(m[t]) == a.tier)
    for tid in ids:
        run_casual(a.out, tid, m[tid], strategies)
        if "careful" in strategies:
            run_careful(a.out, tid, m[tid], a.rounds)


if __name__ == "__main__":
    main()
