import math
import time


def solve(points):
    """Nearest neighbour, then plain first-improvement 2-opt over all pairs."""
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7

    D = [[math.hypot(p[0] - q[0], p[1] - q[1]) for q in points] for p in points]

    unvisited = set(range(1, n))
    tour = [0]
    cur = 0
    while unvisited:
        Dc = D[cur]
        nxt = min(unvisited, key=lambda j: (Dc[j], j))
        unvisited.remove(nxt)
        tour.append(nxt)
        cur = nxt

    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            if time.perf_counter() > deadline:
                return tour
            a = tour[i]
            Da = D[a]
            b = tour[i + 1]
            jmax = n if i > 0 else n - 1
            for j in range(i + 2, jmax):
                c = tour[j]
                d = tour[j + 1] if j + 1 < n else tour[0]
                delta = Da[c] + D[b][d] - Da[b] - D[c][d]
                if delta < -1e-10:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    b = tour[i + 1]
                    improved = True
    return tour
