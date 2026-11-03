"""Score a machine scheduler on weighted tardiness. Usage: score.py <candidate.py> [--split train|test]"""
import heapq
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "schedule-train-4"
TEST_SEED = "schedule-test-27"
N_JOBS = 200
N_INST = 8
LIMIT = 1.0


def edf(jobs, m):
    order = sorted(range(len(jobs)), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i = [], [], 0
    while len(out) < len(jobs):
        t, k = heapq.heappop(free)
        if not ready and i < len(order) and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < len(order) and jobs[order[i]][0] <= t:
            heapq.heappush(ready, (jobs[order[i]][2], order[i]))
            i += 1
        _, j = heapq.heappop(ready)
        t = max(t, jobs[j][0])
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def gen(rng, m):
    durs = [rng.randint(1, 10) if rng.random() < 0.7 else rng.randint(10, 50) for _ in range(N_JOBS)]
    horizon = int(sum(durs) / m * rng.uniform(0.55, 0.8))
    jobs = []
    for p in durs:
        r = rng.randint(0, horizon)
        slack = int(p * rng.uniform(0.0, 2.5)) + rng.randint(0, 40)
        jobs.append((r, p, r + p + slack, rng.randint(1, 10)))
    return jobs


def instances(seed):
    out = []
    for i in range(N_INST):
        m = [2, 3, 4, 6][i % 4]
        out.append({"m": m, "jobs": gen(random.Random(f"{seed}/{i}"), m)})
    return out


def stress_instances():
    """Inputs the statement allows and the random kinds rarely make: ties, no lateness, huge times."""
    rng = random.Random("schedule-stress-1")
    n = N_JOBS
    kinds = {
        "identical-jobs": (3, [(0, 5, 20, 3)] * n),
        "nothing-late": (4, [(rng.randint(0, 100), rng.randint(1, 10), 10**6, rng.randint(1, 10)) for _ in range(n)]),
        "all-late-at-release": (2, [(r, p, r, rng.randint(1, 10)) for r, p in
                                    ((rng.randint(0, 500), rng.randint(1, 20)) for _ in range(n))]),
        "huge-times": (6, [(10**9 + rng.randint(0, 10**6), rng.randint(1, 10**4), 10**9 + rng.randint(0, 10**6),
                            rng.randint(1, 10)) for _ in range(n)]),
        "one-long-job": (3, [(0, 10**5, 10, 10)] + [(rng.randint(0, 50), 1, rng.randint(1, 60), 1) for _ in range(n - 1)]),
        "few-jobs": (6, [(i, 3, i + 3, 1) for i in range(5)]),
    }
    return [{"m": m, "jobs": jobs} for m, jobs in kinds.values()]


def check(jobs, m, sched):
    """Return weighted tardiness, or raise ValueError when the schedule is infeasible."""
    if not isinstance(sched, list) or len(sched) != len(jobs):
        raise ValueError("every job must be scheduled exactly once")
    seen, per_machine, wt = set(), {}, 0
    for row in sched:
        if not isinstance(row, list) or len(row) != 3 or not all(type(v) is int for v in row):
            raise ValueError("each entry must be (job, machine, start) integers")
        j, k, s = row
        if not 0 <= j < len(jobs) or j in seen:
            raise ValueError(f"job {j} missing, unknown or repeated")
        if not 0 <= k < m:
            raise ValueError(f"machine {k} out of range")
        r, p, d, w = jobs[j]
        if s < r:
            raise ValueError(f"job {j} starts before its release")
        seen.add(j)
        per_machine.setdefault(k, []).append((s, s + p, j))
        wt += w * max(0, s + p - d)
    for k, iv in per_machine.items():
        iv.sort()
        for (s1, e1, j1), (s2, _, j2) in zip(iv, iv[1:]):
            if s2 < e1:
                raise ValueError(f"jobs {j1} and {j2} overlap on machine {k}")
    return wt


RUNNER = r'''
_wall = time.perf_counter  # captured before the candidate is imported
def _run(cand, p):
    outs, times = [], []
    for inst in p["instances"]:
        jobs = [tuple(j) for j in inst["jobs"]]
        _arm(p["limit"] + 1.0)
        t0 = _wall()
        try:
            res = [list(r) for r in cand.schedule(jobs, inst["m"])]  # inside the timer, as in tsp
        finally:
            el = _wall() - t0
            _disarm()
        if el > p["limit"]:
            return {"error": f"instance {len(outs)} took {el:.3f}s (limit {p['limit']}s)"}
        outs.append(res)
        times.append(round(el, 4))
    return {"schedules": outs, "times": times}
'''


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    insts = stress_instances() if split == "stress" else instances(seed)
    res = _bench.run_child(cand, RUNNER, {"instances": insts, "limit": LIMIT},
                           timeout=len(insts) * (LIMIT + 1.0) + 5)
    if "error" in res:
        return _bench.fail(res)
    ratios = []
    for i, (inst, sched) in enumerate(zip(insts, res.get("schedules", []))):
        jobs, m = inst["jobs"], inst["m"]
        try:
            wt = check(jobs, m, sched)
        except ValueError as e:
            return _bench.fail({"error": f"instance {i}: {e}"})
        ratios.append(wt / max(1, check(jobs, m, [list(r) for r in edf(jobs, m)])))
    if len(ratios) != len(insts):
        return _bench.fail({"error": "missing instances"})
    detail = {"split": split, "mean_tardiness_over_edf": round(sum(ratios) / len(ratios), 6),
              "ratios": [round(r, 4) for r in ratios], "max_time_s": max(res["times"])}
    _bench.emit(True, -sum(ratios) / len(ratios), detail)


if __name__ == "__main__":
    main()
