"""Score a graph colouring heuristic. Usage: score.py <candidate.py> [--split train|test]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _bench  # noqa: E402

TRAIN_SEED = "coloring-train-6"
TEST_SEED = "coloring-test-44"
KINDS = ("sparse", "medium", "dense", "geometric", "geometric", "near_bipartite",
         "planted", "planted")
LIMIT = 1.0


def gen(rng, kind):
    n = rng.randint(150, 400)
    pairs = set()
    if kind in ("sparse", "medium", "dense"):
        p = {"sparse": rng.uniform(6, 12) / n, "medium": rng.uniform(0.1, 0.2),
             "dense": rng.uniform(0.4, 0.6)}[kind]
        pairs = {(u, v) for u in range(n) for v in range(u + 1, n) if rng.random() < p}
    elif kind == "geometric":
        pts = [(rng.random(), rng.random()) for _ in range(n)]
        r = math.sqrt(rng.uniform(10, 30) / (math.pi * n))
        pairs = {(u, v) for u in range(n) for v in range(u + 1, n)
                 if math.dist(pts[u], pts[v]) < r}
    elif kind == "near_bipartite":
        side = [rng.random() < 0.5 for _ in range(n)]
        p = rng.uniform(0.05, 0.15)
        pairs = {(u, v) for u in range(n) for v in range(u + 1, n)
                 if side[u] != side[v] and rng.random() < p}
        for _ in range(n // 20):
            u, v = rng.sample(range(n), 2)
            if side[u] == side[v]:
                pairs.add((min(u, v), max(u, v)))
    else:  # planted: k hidden groups, edges only between groups
        k = rng.randint(4, 9)
        group = [rng.randrange(k) for _ in range(n)]
        p = rng.uniform(0.15, 0.4)
        pairs = {(u, v) for u in range(n) for v in range(u + 1, n)
                 if group[u] != group[v] and rng.random() < p}
    perm = list(range(n))
    rng.shuffle(perm)
    edges = [[perm[u], perm[v]] if rng.random() < 0.5 else [perm[v], perm[u]]
             for u, v in sorted(pairs)]
    rng.shuffle(edges)
    return {"kind": kind, "n": n, "edges": edges}


def stress_instances():
    """Graphs the statement allows and the random kinds rarely make: empty, complete, star, path."""
    def inst(kind, n, pairs):
        return {"kind": kind, "n": n, "edges": [list(e) for e in pairs]}
    n = 200
    return [
        inst("no-edges", n, []),
        inst("complete", n, [(u, v) for u in range(n) for v in range(u + 1, n)]),
        inst("star", n, [(0, v) for v in range(1, n)]),
        inst("path", n, [(v + 1, v) for v in range(n - 1)]),
        inst("complete-bipartite", n, [(u, v) for u in range(n // 2) for v in range(n // 2, n)]),
        inst("clique-plus-isolated", n, [(u, v) for u in range(30) for v in range(u + 1, 30)]),
        inst("one-node", 1, []),
    ]


def instances(seed):
    return [gen(random.Random(f"{seed}/{k}/{i}"), k) for i, k in enumerate(KINDS)]


def largest_first(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    colors = [-1] * n
    for u in sorted(range(n), key=lambda u: (-len(adj[u]), u)):
        taken = {colors[v] for v in adj[u]}
        c = 0
        while c in taken:
            c += 1
        colors[u] = c
    return colors


def check(inst, colors):
    """Number of colours of a proper colouring; ValueError when it is not one."""
    n = inst["n"]
    if not isinstance(colors, list) or len(colors) != n:
        raise ValueError(f"expected one colour per node ({n})")
    if not all(type(c) is int and 0 <= c < n for c in colors):
        raise ValueError(f"colours must be integers in 0 .. {n - 1}")
    for u, v in inst["edges"]:
        if colors[u] == colors[v]:
            raise ValueError(f"nodes {u} and {v} are adjacent and share colour {colors[u]}")
    return len(set(colors))


RUNNER = r'''
_wall = time.perf_counter

def _run(cand, p):
    outs, times = [], []
    for inst in p["instances"]:
        edges = [tuple(e) for e in inst["edges"]]
        _arm(p["limit"] + 1.0)
        t0 = _wall()
        try:
            res = list(cand.color(inst["n"], edges))
        finally:
            el = _wall() - t0
            _disarm()
        if el > p["limit"]:
            return {"error": f"instance {len(outs)} took {el:.3f}s (limit {p['limit']}s)"}
        if not all(type(c) is int for c in res):
            return {"error": f"instance {len(outs)}: colours must be ints"}
        outs.append(res)
        times.append(round(el, 4))
    return {"colorings": outs, "times": times}
'''


def main():
    cand, split = _bench.parse_args(sys.argv)
    seed = TRAIN_SEED if split == "train" else _bench.test_seed(TEST_SEED)
    insts = stress_instances() if split == "stress" else instances(seed)
    res = _bench.run_child(cand, RUNNER, {"instances": insts, "limit": LIMIT},
                           timeout=len(insts) * (LIMIT + 1.0) + 5)
    if "error" in res:
        return _bench.fail(res)
    cols = res.get("colorings")
    if not isinstance(cols, list) or len(cols) != len(insts):
        return _bench.fail({"error": "missing instances"})
    ratios, used = [], []
    for i, (inst, colors) in enumerate(zip(insts, cols)):
        try:
            got = check(inst, colors)
        except ValueError as e:
            return _bench.fail({"error": f"instance {i}: {e}"})
        ratios.append(got / check(inst, largest_first(inst["n"], inst["edges"])))
        used.append(got)
    detail = {"split": split, "mean_colours_over_largest_first": round(sum(ratios) / len(ratios), 6),
              "ratios": [round(r, 4) for r in ratios], "colours": used,
              "max_time_s": max(res["times"])}
    _bench.emit(True, -sum(ratios) / len(ratios), detail)


if __name__ == "__main__":
    main()
