"""Score a cache eviction policy on synthetic traces. Usage: score.py <candidate.py> [--split train|test]"""
import bisect
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "cache-train-5"
TEST_SEED = "cache-test-44"
LENGTH = 30_000
TIME_LIMIT = 8.0


class Zipf:
    def __init__(self, rng, n, alpha, base):
        w = [1.0 / (r + 1) ** alpha for r in range(n)]
        tot, acc, self.cdf = sum(w), 0.0, []
        for x in w:
            acc += x
            self.cdf.append(acc / tot)
        self.keys = list(range(base, base + n))
        rng.shuffle(self.keys)
        self.rng = rng

    def __call__(self):
        return self.keys[min(len(self.keys) - 1, bisect.bisect_left(self.cdf, self.rng.random()))]


def trace_hot_with_scans(rng, cap):
    z, out, fresh = Zipf(rng, 4000, 0.9, 0), [], 10**6
    while len(out) < LENGTH:
        if rng.random() < 0.002:
            for _ in range(rng.randint(cap, 4 * cap)):
                out.append(fresh)
                fresh += 1
        else:
            out.append(z())
    return out[:LENGTH]


def trace_loop_and_hot(rng, cap):
    loop_len, hot = int(cap * rng.uniform(1.2, 1.8)), Zipf(rng, cap // 3, 1.0, 50_000)
    out, i = [], 0
    while len(out) < LENGTH:
        if rng.random() < 0.3:
            out.append(hot())
        else:
            out.append(i % loop_len)
            i += 1
    return out


def trace_phases(rng, cap):
    out = []
    for ph in range(5):
        z = Zipf(rng, rng.randint(2 * cap, 8 * cap), rng.uniform(0.7, 1.1), 100_000 * (ph + 1))
        out.extend(z() for _ in range(LENGTH // 5))
    return out


def trace_mixed(rng, cap):
    z, loop_len = Zipf(rng, 3000, 0.8, 0), 2 * cap
    out, i, fresh = [], 0, 10**6
    while len(out) < LENGTH:
        u = rng.random()
        if u < 0.6:
            out.append(z())
        elif u < 0.85:
            out.append(20_000 + i % loop_len)
            i += 1
        else:
            out.append(fresh)
            fresh += 1
    return out


def trace_recency(rng, cap):
    out, fresh = [], 0
    while len(out) < LENGTH:
        if out and rng.random() < 0.85:
            back = min(len(out), int(rng.expovariate(1.0 / (0.5 * cap))) + 1)
            out.append(out[-back])
        else:
            out.append(fresh)
            fresh += 1
    return out


def trace_shifting_loops(rng, cap):
    out = []
    for ph in range(6):
        loop_len, base = int(cap * rng.uniform(0.6, 2.5)), 1000 * ph
        out.extend(base + i % loop_len for i in range(LENGTH // 6))
        if ph % 2:
            rng.shuffle(out[-(LENGTH // 12):])
    return out


KINDS = [("hot_with_scans", trace_hot_with_scans, 200), ("loop_and_hot", trace_loop_and_hot, 100),
         ("phases", trace_phases, 150), ("mixed", trace_mixed, 200),
         ("recency", trace_recency, 100), ("shifting_loops", trace_shifting_loops, 120)]


def traces(seed):
    return [{"kind": k, "capacity": cap, "keys": fn(random.Random(f"{seed}/{k}"), cap)}
            for k, fn, cap in KINDS]


def stress_traces():
    """Traces the statement allows and the random kinds rarely make."""
    rng = random.Random("cache-stress-1")
    cap = 100
    return [
        {"kind": "one-key", "capacity": cap, "keys": [7] * LENGTH},
        {"kind": "all-distinct", "capacity": cap, "keys": list(range(LENGTH))},
        {"kind": "loop-cap-plus-one", "capacity": cap, "keys": [i % (cap + 1) for i in range(LENGTH)]},
        {"kind": "huge-and-negative-keys", "capacity": cap,
         "keys": [rng.choice((-1, 1)) * (10**18 + rng.randrange(3 * cap)) for _ in range(LENGTH)]},
        {"kind": "fits-exactly", "capacity": cap, "keys": [rng.randrange(cap) for _ in range(LENGTH)]},
    ]


RUNNER = r'''
def _run(cand, p):
    rates = []
    _arm(p["time_limit"])
    try:
        for t, tr in enumerate(p["traces"]):
            cap = tr["capacity"]
            c = cand.Cache(cap)
            resident = set()
            hits = 0
            for n, k in enumerate(tr["keys"]):
                st = c.store
                h = k in resident and k in st
                r = c.access(k)
                if r is not True and r is not False:
                    return {"error": f"trace {t}: access() must return a bool"}
                if r is not h:
                    return {"error": f"trace {t} step {n}: access() said hit={r}, the cache says {h}"}
                if h:
                    hits += 1
                else:
                    cur = set(c.store)
                    if len(cur) > cap:
                        return {"error": f"trace {t} step {n}: {len(cur)} keys stored, capacity {cap}"}
                    extra = cur - resident
                    extra.discard(k)
                    if extra:
                        return {"error": f"trace {t} step {n}: stored keys that were not just requested"}
                    resident = cur
            if len(set(c.store)) > cap:
                return {"error": f"trace {t}: over capacity at the end"}
            rates.append(hits / len(tr["keys"]))
    finally:
        _disarm()
    return {"rates": rates}
'''


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    trs = stress_traces() if split == "stress" else traces(seed)
    res = _bench.run_child(cand, RUNNER, {"traces": trs, "time_limit": TIME_LIMIT},
                           timeout=TIME_LIMIT + 10)
    if "error" in res:
        return _bench.fail(res)
    rates = res.get("rates", [])
    if len(rates) != len(trs):
        return _bench.fail({"error": "missing traces"})
    detail = {"split": split, "hit_rate_by_trace": {tr["kind"]: round(r, 4) for tr, r in zip(trs, rates)}}
    _bench.emit(True, sum(rates) / len(rates), detail)


if __name__ == "__main__":
    main()
