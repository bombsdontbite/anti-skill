"""Score an online bin-packing priority function. Usage: score.py <candidate.py> [--split train|test]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "binpack-train-7"
TEST_SEED = "binpack-test-91"
N_ITEMS = 2000
PER_DIST = 5
TIME_LIMIT = 8.0


def gen_items(rng, dist):
    if dist == "uniform":
        return 150, [rng.randint(20, 100) for _ in range(N_ITEMS)]
    if dist == "weibull":
        return 100, [min(100, max(1, round(rng.weibullvariate(45, 3)))) for _ in range(N_ITEMS)]
    items = []
    for _ in range(N_ITEMS):
        items.append(rng.randint(5, 30) if rng.random() < 0.6 else rng.randint(45, 75))
    return 100, items


def stress_instances():
    """Item lists the statement allows and the random kinds rarely make: exact fits, all equal, tiny."""
    rng = random.Random("binpack-stress-1")
    n = 500
    return [
        {"dist": "full-items", "capacity": 100, "items": [100] * n},
        {"dist": "just-over-half", "capacity": 100, "items": [51] * n},
        {"dist": "tiny", "capacity": 100, "items": [1] * n},
        {"dist": "exact-pairs", "capacity": 100, "items": [x for _ in range(n // 2) for x in (rng.randint(1, 99),) for x in (x, 100 - x)]},
        {"dist": "one-size", "capacity": 150, "items": [50] * n},
    ]


def instances(seed):
    out = []
    for dist in ("uniform", "weibull", "bimodal"):
        for k in range(PER_DIST):
            cap, items = gen_items(random.Random(f"{seed}/{dist}/{k}"), dist)
            out.append({"dist": dist, "capacity": cap, "items": items})
    return out


RUNNER = r'''
def _run(cand, p):
    out = []
    _arm(p["time_limit"])
    try:
        for inst in p["instances"]:
            cap = inst["capacity"]
            rem = []
            picks = []
            for item in inst["items"]:
                caps = [r for r in rem if r >= item]
                caps.append(cap)
                pr = cand.priority(item, list(caps))
                pr = list(pr)
                if len(pr) != len(caps):
                    return {"error": f"priority returned {len(pr)} values for {len(caps)} bins"}
                best = 0
                for i in range(1, len(pr)):
                    if pr[i] > pr[best]:
                        best = i
                picks.append(best)
                if best == len(caps) - 1:
                    rem.append(cap - item)
                else:
                    seen = -1
                    for j, r in enumerate(rem):
                        if r >= item:
                            seen += 1
                            if seen == best:
                                rem[j] = r - item
                                break
            out.append(picks)
    finally:
        _disarm()
    return {"picks": out}
'''


def replay(inst, picks):
    """Re-run the packing from the chosen positions; return bins used or raise ValueError."""
    cap, items = inst["capacity"], inst["items"]
    if not isinstance(picks, list) or len(picks) != len(items):
        raise ValueError("wrong number of decisions")
    rem = []
    for item, best in zip(items, picks):
        fit = [j for j, r in enumerate(rem) if r >= item]
        if not isinstance(best, int) or not 0 <= best <= len(fit):
            raise ValueError("decision outside the offered bins")
        if best == len(fit):
            rem.append(cap - item)
        else:
            rem[fit[best]] -= item
    return len(rem)


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    insts = stress_instances() if split == "stress" else instances(seed)
    res = _bench.run_child(cand, RUNNER, {"instances": insts, "time_limit": TIME_LIMIT},
                           timeout=TIME_LIMIT + 10)
    if "error" in res:
        return _bench.fail(res)
    ratios, per = [], {}
    try:
        for inst, picks in zip(insts, res["picks"]):
            used = replay(inst, picks)
            lb = math.ceil(sum(inst["items"]) / inst["capacity"])
            ratios.append(used / lb)
            per.setdefault(inst["dist"], []).append(used / lb)
    except (ValueError, TypeError, KeyError) as e:
        return _bench.fail({"error": f"invalid packing: {e}"})
    if len(ratios) != len(insts):
        return _bench.fail({"error": "missing instances"})
    detail = {"split": split, "mean_bins_over_lower_bound": round(sum(ratios) / len(ratios), 6),
              "by_distribution": {d: round(sum(v) / len(v), 6) for d, v in per.items()}}
    _bench.emit(True, -sum(ratios) / len(ratios), detail)


if __name__ == "__main__":
    main()
