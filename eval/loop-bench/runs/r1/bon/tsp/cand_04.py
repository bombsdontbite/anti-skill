import math
import time


def cheapest_insertion(D, init):
    """Grow a cycle from `init`, always inserting the outside city whose insertion is cheapest."""
    n = len(D)
    succ = [-1] * n
    for k in range(len(init)):
        succ[init[k - 1]] = init[k]
    members = list(init)
    inside = [False] * n
    for v in init:
        inside[v] = True
    outside = set(v for v in range(n) if not inside[v])
    cost = [0.0] * n
    after = [-1] * n

    def best_for(x):
        Dx = D[x]
        best = float("inf")
        bu = -1
        for u in members:
            w = succ[u]
            c = Dx[u] + Dx[w] - D[u][w]
            if c < best:
                best = c
                bu = u
        return best, bu

    for x in outside:
        cost[x], after[x] = best_for(x)

    while outside:
        v = min(outside, key=lambda x: (cost[x], x))
        u = after[v]
        w = succ[u]
        succ[u] = v
        succ[v] = w
        outside.discard(v)
        members.append(v)
        Duv = D[u][v]
        Dvw = D[v][w]
        for x in outside:
            if after[x] == u:
                cost[x], after[x] = best_for(x)
            else:
                Dx = D[x]
                c1 = Dx[u] + Dx[v] - Duv
                if c1 < cost[x]:
                    cost[x] = c1
                    after[x] = u
                c2 = Dx[v] + Dx[w] - Dvw
                if c2 < cost[x]:
                    cost[x] = c2
                    after[x] = v

    s = init[0]
    tour = [s]
    c = succ[s]
    while c != s:
        tour.append(c)
        c = succ[c]
    return tour


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7
    D = [[math.hypot(p[0] - q[0], p[1] - q[1]) for q in points] for p in points]

    far = max(range(1, n), key=lambda j: D[0][j])
    tour = cheapest_insertion(D, [0, far])

    # 2-opt, best partner for every i, sweeping until nothing improves
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            if time.perf_counter() > deadline:
                return tour
            a = tour[i]
            b = tour[i + 1]
            Da = D[a]
            Db = D[b]
            base = Da[b]
            best = -1e-10
            bj = -1
            jmax = n if i > 0 else n - 1
            for j in range(i + 2, jmax):
                c = tour[j]
                d = tour[(j + 1) % n]
                delta = Da[c] + Db[d] - base - D[c][d]
                if delta < best:
                    best = delta
                    bj = j
            if bj >= 0:
                tour[i + 1:bj + 1] = tour[i + 1:bj + 1][::-1]
                improved = True
    return tour
