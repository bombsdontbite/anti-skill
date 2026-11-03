import math
import time

EPS = 1e-10


def farthest_insertion(D):
    n = len(D)
    far = max(range(1, n), key=lambda j: D[0][j])
    tour = [0, far]
    inside = [False] * n
    inside[0] = inside[far] = True
    mind = [min(D[0][j], D[far][j]) for j in range(n)]
    for _ in range(n - 2):
        v = -1
        vd = -1.0
        for j in range(n):
            if not inside[j] and mind[j] > vd:
                vd = mind[j]
                v = j
        Dv = D[v]
        best = float("inf")
        bi = 0
        for k in range(len(tour)):
            u = tour[k - 1]
            w = tour[k]
            c = Dv[u] + Dv[w] - D[u][w]
            if c < best:
                best = c
                bi = k
        tour.insert(bi, v)
        inside[v] = True
        for j in range(n):
            if Dv[j] < mind[j]:
                mind[j] = Dv[j]
    return tour


def two_opt(tour, D, deadline):
    n = len(tour)
    changed = False
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            if time.perf_counter() > deadline:
                return changed
            a = tour[i]
            Da = D[a]
            b = tour[i + 1]
            jmax = n if i > 0 else n - 1
            for j in range(i + 2, jmax):
                c = tour[j]
                d = tour[j + 1] if j + 1 < n else tour[0]
                if Da[c] + D[b][d] - Da[b] - D[c][d] < -EPS:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    b = tour[i + 1]
                    improved = True
                    changed = True
    return changed


def or_opt(tour, D, deadline):
    """Move chains of 1..3 cities to their best place anywhere in the tour (optionally reversed)."""
    n = len(tour)
    changed = False
    for L in (1, 2, 3):
        i = 1
        while i + L < n:
            if time.perf_counter() > deadline:
                return changed
            p = tour[i - 1]
            s0 = tour[i]
            s1 = tour[i + L - 1]
            nx = tour[i + L]
            g = D[p][s0] + D[s1][nx] - D[p][nx]
            if g <= EPS:
                i += 1
                continue
            D0 = D[s0]
            D1 = D[s1]
            best = EPS
            bk = -1
            bflip = False
            for k in range(n):
                if i <= k <= i + L:
                    continue
                u = tour[k - 1]
                w = tour[k]
                duw = D[u][w]
                f = g - (D0[u] + D1[w] - duw)
                r = g - (D1[u] + D0[w] - duw)
                if f > best:
                    best, bk, bflip = f, k, False
                if r > best:
                    best, bk, bflip = r, k, True
            if bk >= 0:
                seg = tour[i:i + L]
                if bflip:
                    seg.reverse()
                if bk < i:
                    tour[:] = tour[:bk] + seg + tour[bk:i] + tour[i + L:]
                else:
                    tour[:] = tour[:i] + tour[i + L:bk] + seg + tour[bk:]
                changed = True
            i += 1
    return changed


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7
    D = [[math.hypot(p[0] - q[0], p[1] - q[1]) for q in points] for p in points]
    tour = farthest_insertion(D)
    rounds = 0
    while time.perf_counter() < deadline:
        a = two_opt(tour, D, deadline)
        b = or_opt(tour, D, deadline) if n >= 6 else False
        rounds += 1
        if not a and not b:
            break
        # rotate so that chains crossing the array end get a turn too
        shift = (rounds * 37) % n
        tour[:] = tour[shift:] + tour[:shift]
    return tour
