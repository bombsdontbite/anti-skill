"""Score a faster usage_report. Usage: score.py <candidate.py> [--split train|test]

score = reference CPU time / candidate CPU time on the timed instances (best of RUNS each,
alternating fresh processes); invalid if any output differs from the reference's.
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "speedup-train-2"
TEST_SEED = "speedup-test-63"
RUNS = 3
N_SESSIONS = 5000
N_WINDOWS = 400
N_TIMED = 4
RUN_TIMEOUT = 8.0
SLOWDOWN_CAP = 3.0  # a candidate this many times slower than the reference is cut off

REFERENCE = '''
def usage_report(sessions, windows):
    report = []
    for lo, hi in windows:
        usage = 0
        count = 0
        for start, end, rate in sessions:
            a = max(start, lo)
            b = min(end, hi)
            if b > a:
                usage += rate * (b - a)
                count += 1
        report.append((usage, count))
    return report
'''
_ns = {}
exec(REFERENCE, _ns)
reference = _ns["usage_report"]


def span(rng):
    u = rng.random()
    if u < 0.7:
        return rng.randint(1, 1000)
    if u < 0.95:
        return rng.randint(1000, 50_000)
    return rng.randint(50_000, 500_000)


def timed_instance(rng, grid):
    sessions, windows = [], []
    for _ in range(N_SESSIONS):
        s = rng.randint(0, 1_000_000 // grid) * grid
        sessions.append((s, s + max(grid, span(rng) // grid * grid), rng.randint(1, 1000)))
    for _ in range(N_WINDOWS):
        lo = rng.randint(0, 1_000_000 // grid) * grid
        windows.append((lo, lo + max(grid, span(rng) // grid * grid)))
    return {"sessions": sessions, "windows": windows}


def edge_cases(rng):
    big = 10**12
    cases = [
        {"sessions": [], "windows": [(0, 10)]},
        {"sessions": [(0, 10, 5)], "windows": []},
        {"sessions": [(0, 10, 5)], "windows": [(10, 20), (-5, 0), (5, 15), (0, 10), (-100, 100)]},
        {"sessions": [(3, 7, 2)] * 5 + [(7, 9, 1)], "windows": [(7, 8), (6, 7), (0, 3), (2, 4)]},
        {"sessions": [(big, big + 5, 999), (-big, big, 1)], "windows": [(big + 1, big + 2), (0, 1)]},
    ]
    for _ in range(60):
        n, q, top = rng.randint(0, 25), rng.randint(0, 25), rng.choice([5, 20, 60])
        ss = []
        for _ in range(n):
            a = rng.randint(-top, top)
            ss.append((a, a + rng.randint(1, top), rng.randint(1, 9)))
        ws = []
        for _ in range(q):
            a = rng.randint(-top, top)
            ws.append((a, a + rng.randint(1, top)))
        cases.append({"sessions": ss, "windows": ws})
    return cases


RUNNER = r'''
_cpu = time.process_time  # captured before the candidate is imported

def _clean(rep, n):
    rep = list(rep)
    if len(rep) != n:
        raise ValueError(f"returned {len(rep)} rows for {n} windows")
    out = []
    for row in rep:
        u, c = row
        if type(u) is not int or type(c) is not int:
            raise ValueError("usage and count must be ints")
        out.append([u, c])
    return out

def _run(cand, p):
    res = {"edge": [], "timed": [], "cpu": 0.0}
    _arm(p["timeout"])
    try:
        for case in p["edge"]:
            ss = [tuple(s) for s in case["sessions"]]
            ws = [tuple(w) for w in case["windows"]]
            res["edge"].append(_clean(cand.usage_report(ss, ws), len(ws)))
        for case in p["timed"]:
            ss = [tuple(s) for s in case["sessions"]]
            ws = [tuple(w) for w in case["windows"]]
            t0 = _cpu()
            rep = list(cand.usage_report(ss, ws))
            res["cpu"] += _cpu() - t0
            res["timed"].append(_clean(rep, len(ws)))
    finally:
        _disarm()
    return res
'''


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    timed = [timed_instance(random.Random(f"{seed}/timed/{i}"), [1, 1, 10, 100][i % 4])
             for i in range(N_TIMED)]
    edge = edge_cases(random.Random(f"{seed}/edge"))
    expected_edge = [[list(r) for r in reference(c["sessions"], c["windows"])] for c in edge]
    payload = {"timed": timed, "timeout": RUN_TIMEOUT}
    ref_times, cand_times, expected = [], [], None
    for run in range(RUNS):
        ref = _bench.run_child(None, RUNNER, dict(payload, edge=[]), RUN_TIMEOUT + 5,
                               source=REFERENCE)
        if "error" in ref:
            return _bench.fail({"error": f"reference failed: {ref['error']}"})
        expected = expected or ref["timed"]
        ref_times.append(ref["cpu"])
        cap = max(1.5, SLOWDOWN_CAP * ref["cpu"] + 0.5)
        res = _bench.run_child(cand, RUNNER, dict(payload, timeout=cap,
                                                  edge=edge if run == 0 else []), cap + 3)
        if "error" in res:
            return _bench.fail(res)
        if run == 0:
            for i, (got, want) in enumerate(zip(res["edge"], expected_edge)):
                if got != want:
                    return _bench.fail({"error": f"wrong output on correctness test {i}"})
            if len(res["edge"]) != len(edge):
                return _bench.fail({"error": "missing correctness tests"})
        if res["timed"] != expected:
            return _bench.fail({"error": f"wrong output on a timed instance (run {run})"})
        cand_times.append(res["cpu"])
    ref_t, cand_t = min(ref_times), max(min(cand_times), 1e-6)
    detail = {"split": split, "reference_cpu_s": round(ref_t, 4), "candidate_cpu_s": round(cand_t, 6),
              "runs": RUNS}
    _bench.emit(True, ref_t / cand_t, detail)


if __name__ == "__main__":
    main()
