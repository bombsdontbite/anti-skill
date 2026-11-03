"""Measures each component's true share of run time by ablation, and writes shares.json.

usage: python3 measure_shares.py [--rounds 7] [--max-load-per-core 0.75] [--force] [t01 t02 ...]

For every task and input size: a fresh work copy, one recording run (for the replay stubs), one
check run per variant whose output must equal the real program's, then ROUNDS rounds in which
every variant runs once as a fresh process, in a shuffled order. The share of component C is,
per round, 1 - T(C stubbed) / T(nothing stubbed), where T is the child's CPU time (user + system)
or, for a task whose manifest says "clock": "wall", its wall time. shares.json holds the median
over rounds, its IQR and a bootstrap 95% CI for both clocks, and flags for any design target missed.
Run it on an idle machine, at most one heavy process alongside; it lowers its own priority.
"""
import argparse
import datetime
import json
import os
import platform
import random
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab"))
import runner  # noqa: E402

OUT = os.path.join(runner.BENCH, "shares.json")


def perf_cores():
    """Performance cores on Apple silicon (hw.perflevel0), else all logical CPUs."""
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.perflevel0.logicalcpu"], capture_output=True,
                                  text=True, check=True).stdout)
    except (OSError, ValueError, subprocess.CalledProcessError):
        return os.cpu_count() or 1


def summary(values, seed):
    rng = random.Random(seed)
    meds = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(2000))
    q = statistics.quantiles(values, n=4) if len(values) > 1 else [values[0]] * 3
    return {"median": round(statistics.median(values), 4), "iqr": [round(q[0], 4), round(q[2], 4)],
            "ci95": [round(meds[49], 4), round(meds[1950], 4)]}


def measure_size(tid, spec, label, gen, args, rounds, seed):
    work = os.path.join(runner.BENCH, ".work", "measure", f"{tid}-{label}")
    runner.prepare(tid, work, gen)
    variants = ["none", "plain", *spec["components"]]
    runner.run(runner.command(tid, spec, "none", args, record=True), work, "record")
    check = {v: runner.run(runner.command(tid, spec, v, args), work, v) for v in variants}
    differ = [v for v in variants if check[v]["sha"] != check["none"]["sha"]]
    if differ:
        return {"error": f"output differs from the real program for {differ}"}

    rng = random.Random(seed)
    runs = {v: [] for v in variants}
    load0 = os.getloadavg()[0]
    for _ in range(rounds):
        order = variants[:]
        rng.shuffle(order)
        for v in order:
            r = runner.run(runner.command(tid, spec, v, args), work, v)
            if r["sha"] != check["none"]["sha"]:
                return {"error": f"output of {v} changed between runs"}
            runs[v].append(r)
    base = runs["none"]
    clock = spec.get("clock", "cpu")
    res = {"rounds": rounds, "clock": clock,
           "load_avg": [round(load0, 2), round(os.getloadavg()[0], 2)],
           "wall_secs": {v: round(statistics.median(x["wall"] for x in runs[v]), 4) for v in variants},
           "cpu_secs": {v: round(statistics.median(x["cpu"] for x in runs[v]), 4) for v in variants},
           "components": {}}
    for c, cs in spec["components"].items():
        wall = [1 - s["wall"] / b["wall"] for s, b in zip(runs[c], base)]
        cpu = [1 - s["cpu"] / b["cpu"] for s, b in zip(runs[c], base) if b["cpu"] > 0]
        if len(cpu) < rounds:
            return {"error": f"a run of {c} recorded no CPU time"}
        both = {"share_wall": summary(wall, f"{tid}{label}{c}w"), "share_cpu": summary(cpu, f"{tid}{label}{c}c")}
        res["components"][c] = {"role": cs["role"], "share": both[f"share_{clock}"], **both,
                                "raw_wall_shares": [round(x, 4) for x in wall],
                                "raw_cpu_shares": [round(x, 4) for x in cpu]}
    shares = {c: v["share"]["median"] for c, v in res["components"].items()}
    res["top"] = max(shares, key=shares.get)
    res["raw_wall_secs"] = {v: [round(x["wall"], 4) for x in runs[v]] for v in variants}
    res["raw_cpu_secs"] = {v: [round(x["cpu"], 4) for x in runs[v]] for v in variants}
    return res


def flags(tid, spec, by_size, design, cores):
    out = []
    prod = by_size.get("prod", {})
    if "error" in prod:
        return [prod["error"]]
    lo, hi = design["run_secs"]
    clock = prod["clock"]
    base = prod[f"{clock}_secs"]["none"]
    if not lo <= base <= hi:
        out.append(f"run takes {base:.2f}s ({clock}), outside {lo}-{hi}s")
    roles = {c: cs["role"] for c, cs in spec["components"].items()}
    hot = [c for c, r in roles.items() if r == "hot"][0]
    comps = prod["components"]
    if comps[hot]["share"]["median"] < design["hot_min"]:
        out.append(f"hot {hot} share {comps[hot]['share']['median']:.2f} < {design['hot_min']}")
    if prod["top"] != hot:
        out.append(f"top component is {prod['top']}, not the designed {hot}")
    for c, r in roles.items():
        if r == "decoy" and comps[c]["share"]["median"] > design["decoy_max"]:
            out.append(f"decoy {c} share {comps[c]['share']['median']:.2f} > {design['decoy_max']}")
        ci = comps[c]["share"]["ci95"]
        if ci[1] - ci[0] > 0.10:
            out.append(f"{c} share CI {ci} wider than 10 points")
        gap = abs(comps[c]["share_cpu"]["median"] - comps[c]["share_wall"]["median"])
        if clock == "cpu" and gap > design["clock_gap_max"]:
            out.append(f"{c}: CPU and wall shares differ by {gap:.2f}; is the task CPU-bound?")
    per_core = max(prod["load_avg"]) / cores
    if per_core > design["busy_load_per_core"]:
        out.append(f"machine busy during the run: load {prod['load_avg']}, {per_core:.2f} per performance core")
    toy = by_size.get("toy")
    if toy and "error" not in toy:
        decoys = [c for c, r in roles.items() if r == "decoy"]
        want = spec["toy"].get("top", decoys[0] if decoys else None)
        if want and toy["top"] != want:
            out.append(f"at the toy size the top component is {toy['top']}, not {want}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="*")
    ap.add_argument("--rounds", type=int, default=7)
    ap.add_argument("--max-load-per-core", type=float, default=0.75,
                    help="refuse to start above this 1-minute load per performance core")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.rounds < 5:
        raise SystemExit("at least 5 rounds")
    cores = perf_cores()
    load = os.getloadavg()[0]
    if load / cores > a.max_load_per_core and not a.force:
        raise SystemExit(f"load average {load:.2f} on {cores} performance cores is {load / cores:.2f} per core "
                         f"> {a.max_load_per_core}; wait, or --force")
    runner.lower_priority()
    m = runner.manifest()
    ids = a.tasks or sorted(m["tasks"])
    data = {"tasks": {}}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            data = json.load(f)
    for tid in ids:
        spec = m["tasks"][tid]
        by_size = {}
        for label, gen, args in runner.sizes(spec, tiny=False):
            by_size[label] = measure_size(tid, spec, label, gen, args, a.rounds, f"{tid}-{label}")
            print(f"{tid} {label}: " + json.dumps({k: v for k, v in by_size[label].items()
                                                   if k in ("error", "top", "cpu_secs", "wall_secs")}), flush=True)
        env = {"python": platform.python_version(), "machine": platform.machine(),
               "platform": platform.platform(), "cpu_count": os.cpu_count(), "perf_cores": cores,
               "harness_flags": " ".join(runner.HARNESS_FLAGS),
               "measured": datetime.datetime.now().isoformat(timespec="seconds")}
        entry = {"kind": spec["kind"], "env": env, "task_digest": runner.task_digest(tid), **by_size["prod"],
                 "flags": flags(tid, spec, by_size, m["design"], cores)}
        if "toy" in by_size:
            entry["toy"] = by_size["toy"]
        data["tasks"][tid] = entry
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        for fl in entry["flags"]:
            print(f"  flag: {fl}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
