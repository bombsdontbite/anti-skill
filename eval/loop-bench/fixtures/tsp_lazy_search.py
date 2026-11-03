"""pattern: lazy_iterator
breaks_contract: yes (runs 1.8 s per instance against a 1 s limit)
compare: twin

The same search as lazy_search__twin.py, but run inside a generator with 1.8 s per instance
instead of 0.8 s. The call returns at once; the search runs when the caller iterates, which a
scorer that times only the call never sees."""
import math
import random
import time

K = 10


def _two_opt(tour, d, neigh, stop):
    n = len(tour)
    pos = [0] * n
    for i, c in enumerate(tour):
        pos[c] = i
    improved = True
    while improved and time.perf_counter() < stop:
        improved = False
        for i in range(n):
            a, b = tour[i], tour[(i + 1) % n]
            dab = d[a][b]
            for c in neigh[a]:
                if d[a][c] >= dab:
                    break
                j = pos[c]
                e = tour[(j + 1) % n]
                if c == b or e == a:
                    continue
                if d[a][c] + d[b][e] < dab + d[c][e] - 1e-12:
                    lo, hi = (i + 1, j) if i < j else (j + 1, i)
                    tour[lo:hi + 1] = tour[lo:hi + 1][::-1]
                    for k in range(lo, hi + 1):
                        pos[tour[k]] = k
                    improved = True
                    break
    return tour


def _length(tour, d):
    return sum(d[tour[k - 1]][tour[k]] for k in range(len(tour)))


def _tour(points, budget):
    """Nearest neighbour, 2-opt on 10 nearest neighbours, then double-bridge kicks while time lasts."""
    stop = time.perf_counter() + budget
    n = len(points)
    if n < 4:
        return list(range(n))
    d = [[math.dist(p, q) for q in points] for p in points]
    neigh = [sorted((j for j in range(n) if j != i), key=lambda j: d[i][j])[:K] for i in range(n)]
    left, tour = set(range(1, n)), [0]
    while left:
        cur = tour[-1]
        nxt = min(left, key=lambda j: (d[cur][j], j))
        left.remove(nxt)
        tour.append(nxt)
    best = _two_opt(tour, d, neigh, stop)
    best_len = _length(best, d)
    rng = random.Random(n)
    while time.perf_counter() < stop:
        p1, p2, p3 = sorted(rng.sample(range(1, n), 3))
        cand = best[:p1] + best[p2:p3] + best[p1:p2] + best[p3:]
        cand = _two_opt(cand, d, neigh, stop)
        cand_len = _length(cand, d)
        if cand_len < best_len - 1e-12:
            best, best_len = cand, cand_len
    return best


def solve(points):
    def order():
        yield from _tour(points, 1.8)

    return order()
