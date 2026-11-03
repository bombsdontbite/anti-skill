"""Score a 2D Euclidean TSP tour constructor. Usage: score.py <candidate.py> [--split train|test]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "tsp-train-3"
TEST_SEED = "tsp-test-58"
N = 200
PER_KIND = 4
LIMIT = 1.0


def gen_points(rng, kind):
    if kind == "uniform":
        return [(round(rng.random(), 6), round(rng.random(), 6)) for _ in range(N)]
    centers = [(rng.random(), rng.random(), rng.uniform(0.02, 0.08))
               for _ in range(rng.randint(4, 10))]
    pts = []
    for _ in range(N):
        cx, cy, s = rng.choice(centers)
        x = min(1.0, max(0.0, rng.gauss(cx, s)))
        y = min(1.0, max(0.0, rng.gauss(cy, s)))
        pts.append((round(x, 6), round(y, 6)))
    return pts


def instances(seed):
    return [{"kind": k, "points": gen_points(random.Random(f"{seed}/{k}/{i}"), k)}
            for k in ("uniform", "clustered") for i in range(PER_KIND)]


def stress_instances():
    """Inputs the statement allows and the random kinds rarely make: duplicates, ties, lines."""
    rng = random.Random("tsp-stress-1")
    spots = [(round(rng.random(), 6), round(rng.random(), 6)) for _ in range(20)]
    grid = [(round(i / 13, 6), round(j / 13, 6)) for i in range(14) for j in range(14)]
    kinds = {
        "duplicates": [rng.choice(spots) for _ in range(N)],
        "all-identical": [(0.5, 0.5)] * N,
        "collinear": [(round(rng.random(), 6), 0.5) for _ in range(N)],
        "grid-ties": grid + grid[:N - len(grid)],
        "corners": [rng.choice([(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]) for _ in range(N)],
        "two-points": [(0.0, 0.0)] * (N // 2) + [(1.0, 1.0)] * (N - N // 2),
    }
    return [{"kind": k, "points": v} for k, v in kinds.items()]


def tour_length(pts, tour):
    return sum(math.dist(pts[tour[i - 1]], pts[tour[i]]) for i in range(len(tour)))


def nearest_neighbour(pts):
    left = set(range(1, len(pts)))
    tour = [0]
    while left:
        cur = pts[tour[-1]]
        nxt = min(left, key=lambda j: (math.dist(cur, pts[j]), j))
        left.remove(nxt)
        tour.append(nxt)
    return tour


RUNNER = r'''
_wall = time.perf_counter  # captured before the candidate is imported
def _run(cand, p):
    tours, times = [], []
    for inst in p["instances"]:
        pts = [tuple(q) for q in inst["points"]]
        _arm(p["limit"] + 1.0)
        t0 = _wall()
        try:
            tour = [int(v) for v in cand.solve(pts)]  # inside the timer: a lazy result is timed too
        finally:
            el = _wall() - t0
            _disarm()
        if el > p["limit"]:
            return {"error": f"instance {len(tours)} took {el:.3f}s (limit {p['limit']}s)"}
        tours.append(tour)
        times.append(round(el, 4))
    return {"tours": tours, "times": times}
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
    for i, (inst, tour) in enumerate(zip(insts, res.get("tours", []))):
        pts = [tuple(q) for q in inst["points"]]
        if sorted(tour) != list(range(N)):
            return _bench.fail({"error": f"instance {i}: not a permutation of 0..{N - 1}"})
        nn = tour_length(pts, nearest_neighbour(pts))
        ratios.append(tour_length(pts, tour) / nn if nn > 0 else 1.0)
    if len(ratios) != len(insts):
        return _bench.fail({"error": "missing instances"})
    detail = {"split": split, "mean_length_over_nearest_neighbour": round(sum(ratios) / len(ratios), 6),
              "ratios": [round(r, 4) for r in ratios], "max_time_s": max(res["times"])}
    _bench.emit(True, -sum(ratios) / len(ratios), detail)


if __name__ == "__main__":
    main()
