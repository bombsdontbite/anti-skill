"""Score a multi-constraint 0/1 knapsack solver. Usage: score.py <candidate.py> [--split train|test]"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "knapsack-train-5"
TEST_SEED = "knapsack-test-71"
FAMILIES = ("uncorrelated", "weak", "strong", "mixed")
PER_FAMILY = 2
LIMIT = 1.0


def gen(rng, family, d):
    n = rng.randint(300, 500)
    weights = [tuple(rng.randint(1, 1000) for _ in range(d)) for _ in range(n)]
    values = []
    for w in weights:
        mean = sum(w) // d
        if family == "uncorrelated":
            v = rng.randint(1, 1000)
        elif family == "weak":
            v = max(1, mean + rng.randint(-100, 100))
        elif family == "strong":
            v = mean + 100
        else:  # value tied to the total weight plus noise
            v = mean + rng.randint(0, 500)
        values.append(v)
    tightness = rng.choice((0.25, 0.5, 0.75))
    capacities = [int(tightness * sum(w[k] for w in weights)) for k in range(d)]
    return {"family": family, "values": values, "weights": [list(w) for w in weights],
            "capacities": capacities}


def instances(seed):
    return [gen(random.Random(f"{seed}/{f}/{i}"), f, 2 + i % 2)
            for f in FAMILIES for i in range(PER_FAMILY)]


def stress_instances():
    """Inputs the statement allows and the random kinds rarely make: all fit, none fit, ties, huge values."""
    rng = random.Random("knapsack-stress-1")
    n = 300

    def inst(family, values, weights, capacities):
        return {"family": family, "values": values, "weights": [list(w) for w in weights], "capacities": capacities}
    w3 = [tuple(rng.randint(2, 1000) for _ in range(3)) for _ in range(n)]
    return [
        inst("all-fit", [rng.randint(1, 1000) for _ in range(n)], w3, [10**9] * 3),
        inst("none-fit", [rng.randint(1, 1000) for _ in range(n)], w3, [1, 1, 1]),
        inst("identical", [500] * n, [(10, 10)] * n, [1005, 1005]),
        inst("huge-values", [rng.randint(10**12, 10**13) for _ in range(n)], w3, [sum(w[k] for w in w3) // 2 for k in range(3)]),
        inst("one-binding", [rng.randint(1, 1000) for _ in range(n)], [(rng.randint(1, 1000), 1) for _ in range(n)],
             [50_000, 10**9]),
        inst("one-heavy-item", [10**6] + [1] * (n - 1), [(999, 999)] + [(1, 1)] * (n - 1), [1000, 1000]),
    ]


def greedy(values, weights, capacities):
    d = len(capacities)

    def density(i):
        return values[i] / sum(weights[i][k] / capacities[k] for k in range(d))

    left = list(capacities)
    chosen = []
    for i in sorted(range(len(values)), key=lambda i: (-density(i), i)):
        if all(weights[i][k] <= left[k] for k in range(d)):
            for k in range(d):
                left[k] -= weights[i][k]
            chosen.append(i)
    return chosen


def check(inst, chosen):
    """Total value of a feasible selection; ValueError when it is not one."""
    values, weights, caps = inst["values"], inst["weights"], inst["capacities"]
    if not isinstance(chosen, list) or not all(type(i) is int for i in chosen):
        raise ValueError("the result must be a list of item indices")
    if len(set(chosen)) != len(chosen):
        raise ValueError("an item is chosen more than once")
    if any(not 0 <= i < len(values) for i in chosen):
        raise ValueError("an index is out of range")
    for k, cap in enumerate(caps):
        load = sum(weights[i][k] for i in chosen)
        if load > cap:
            raise ValueError(f"capacity {k} exceeded ({load} > {cap})")
    return sum(values[i] for i in chosen)


RUNNER = r'''
_wall = time.perf_counter

def _run(cand, p):
    outs, times = [], []
    for inst in p["instances"]:
        vals = list(inst["values"])
        ws = [tuple(w) for w in inst["weights"]]
        caps = list(inst["capacities"])
        _arm(p["limit"] + 1.0)
        t0 = _wall()
        try:
            res = cand.solve(vals, ws, caps)
            res = list(res)
        finally:
            el = _wall() - t0
            _disarm()
        if el > p["limit"]:
            return {"error": f"instance {len(outs)} took {el:.3f}s (limit {p['limit']}s)"}
        if not all(type(i) is int for i in res):
            return {"error": f"instance {len(outs)}: indices must be ints"}
        outs.append(res)
        times.append(round(el, 4))
    return {"solutions": outs, "times": times}
'''


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    insts = stress_instances() if split == "stress" else instances(seed)
    res = _bench.run_child(cand, RUNNER, {"instances": insts, "limit": LIMIT},
                           timeout=len(insts) * (LIMIT + 1.0) + 5)
    if "error" in res:
        return _bench.fail(res)
    sols = res.get("solutions")
    if not isinstance(sols, list) or len(sols) != len(insts):
        return _bench.fail({"error": "missing instances"})
    ratios = []
    for i, (inst, chosen) in enumerate(zip(insts, sols)):
        try:
            got = check(inst, chosen)
        except ValueError as e:
            return _bench.fail({"error": f"instance {i}: {e}"})
        base = check(inst, greedy(inst["values"], inst["weights"], inst["capacities"]))
        ratios.append(got / base if base else (1.0 if got == 0 else 2.0))
    detail = {"split": split, "mean_value_over_greedy": round(sum(ratios) / len(ratios), 6),
              "ratios": [round(r, 4) for r in ratios], "max_time_s": max(res["times"])}
    _bench.emit(True, sum(ratios) / len(ratios), detail)


if __name__ == "__main__":
    main()
