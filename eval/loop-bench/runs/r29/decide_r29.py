"""Pre-registered decision for loop-bench run 29 (written 2026-11-02, before the run started).

usage: decide_r29.py <run-dir> [--arms s=r29s,n2=r29n,nudge=r29u,plain=r28pl]

Reads <run-dir>/{dedup,cache}_{dev,test}.json (heldout_compare.py output) and prints:
  1. the choice between S and N2, made on the dev seed only;
  2. the report on the test seed: each arm against plain, and the shipped arm against the nudge.
Arms are matched by label prefix; a label belongs to the first arm whose prefix it starts with
and is followed by a digit.
"""
import argparse, itertools, json, os, statistics, sys

MIN_AGENTS = 6          # fewer finished S or N2 agents per task: no change, N2 stays
P_MAX = 0.10            # one-sided exact permutation test on the difference of means
CACHE_MARGIN = 0.004    # S may trail N2 on cache by at most 0.4 points (a quarter of N2's gain over plain in r28)


def arm_scores(results, prefix):
    out = []
    for label, r in results.items():
        rest = label[len(prefix):]
        if label.startswith(prefix) and rest[:1].isdigit():
            out.append(r["median"])
    return out


def perm_p(a, b):
    """P(mean(A) - mean(B) >= observed) over every relabelling of the pooled values (exact)."""
    pooled, k = a + b, len(a)
    obs = statistics.mean(a) - statistics.mean(b)
    total = hits = 0
    for idx in itertools.combinations(range(len(pooled)), k):
        s = set(idx)
        x = [pooled[i] for i in idx]
        y = [pooled[i] for i in range(len(pooled)) if i not in s]
        total += 1
        hits += statistics.mean(x) - statistics.mean(y) >= obs - 1e-12
    return hits / total


def load(run, task, split):
    p = os.path.join(run, f"{task}_{split}.json")
    return json.load(open(p))["results"] if os.path.exists(p) else None


def pct(a, b):
    return 100 * (statistics.mean(a) / statistics.mean(b) - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--arms", default="s=r29s,n2=r29n,nudge=r29u,plain=r28pl")
    a = ap.parse_args()
    arms = dict(kv.split("=") for kv in a.arms.split(","))

    print("== 1. Choice on the dev seed: S replaces N2 only if every condition holds")
    ok = True
    for task in ("dedup", "cache"):
        res = load(a.run, task, "dev")
        if res is None:
            print(f"{task}: no dev scores; N2 stays"); ok = False; continue
        s, n2 = arm_scores(res, arms["s"]), arm_scores(res, arms["n2"])
        if min(len(s), len(n2)) < MIN_AGENTS:
            print(f"{task}: S {len(s)} / N2 {len(n2)} agents, under {MIN_AGENTS}; N2 stays"); ok = False; continue
        ms, mn = statistics.mean(s), statistics.mean(n2)
        if task == "dedup":
            p = perm_p(s, n2)
            cond = ms > mn and p <= P_MAX
            print(f"dedup: S {ms:.2f} vs N2 {mn:.2f} ({pct(s, n2):+.1f}%), p={p:.3f} (needs S ahead, p <= {P_MAX}): {'yes' if cond else 'no'}")
        else:
            cond = ms >= mn - CACHE_MARGIN
            print(f"cache: S {ms:.4f} vs N2 {mn:.4f} ({100*(ms-mn):+.2f} points; S may trail by {100*CACHE_MARGIN:.1f} at most): {'yes' if cond else 'no'}")
        ok &= cond
    ship = "s" if ok else "n2"
    print(f"DECISION: {'S replaces N2' if ok else 'N2 stays'}")

    print("\n== 2. Report on the test seed (read once, after the decision above)")
    for task in ("dedup", "cache"):
        res = load(a.run, task, "test")
        if res is None:
            print(f"{task}: no test scores"); continue
        plain = arm_scores(res, arms["plain"])
        for name in ("s", "n2", "nudge"):
            x = arm_scores(res, arms[name])
            if x and plain:
                print(f"{task}: {name} {statistics.mean(x):.4g} (n={len(x)}) vs plain {statistics.mean(plain):.4g} (n={len(plain)}): {pct(x, plain):+.1f}%, p={perm_p(x, plain):.3f}")
        sh, nu = arm_scores(res, arms[ship]), arm_scores(res, arms["nudge"])
        if sh and nu:
            p = perm_p(sh, nu)
            verdict = "beats the nudge" if p <= P_MAX and statistics.mean(sh) > statistics.mean(nu) else "not separated from the nudge"
            print(f"{task}: shipped arm vs nudge: {pct(sh, nu):+.1f}%, p={p:.3f}: {verdict}")


if __name__ == "__main__":
    sys.exit(main())
