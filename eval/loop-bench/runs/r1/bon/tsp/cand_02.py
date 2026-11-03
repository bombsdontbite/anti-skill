import math
import time

EPS = 1e-10


def distances(points):
    n = len(points)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = points[i]
        row = D[i]
        for j in range(i + 1, n):
            d = math.hypot(xi - points[j][0], yi - points[j][1])
            row[j] = d
            D[j][i] = d
    return D


def neighbours(D, k):
    n = len(D)
    res = []
    for i in range(n):
        row = D[i]
        cand = sorted((row[j], j) for j in range(n) if j != i)
        res.append([j for _, j in cand[:k]])
    return res


def nearest_neighbour(D, neigh, start=0):
    n = len(D)
    seen = [False] * n
    seen[start] = True
    tour = [start]
    cur = start
    for _ in range(n - 1):
        nxt = -1
        for c in neigh[cur]:
            if not seen[c]:
                nxt = c
                break
        if nxt < 0:
            row = D[cur]
            best = float("inf")
            for v in range(n):
                if not seen[v] and row[v] < best:
                    best = row[v]
                    nxt = v
        seen[nxt] = True
        tour.append(nxt)
        cur = nxt
    return tour


def improve(tour, D, neigh, deadline):
    """Repeated sweeps of neighbour-list 2-opt and Or-opt until a sweep changes nothing."""
    n = len(tour)
    pos = [0] * n

    def reindex():
        for idx, c in enumerate(tour):
            pos[c] = idx

    reindex()

    def reverse(i, j):
        inner = (j - i) % n + 1
        if inner * 2 > n:
            i, j = (j + 1) % n, (i - 1) % n
            inner = n - inner
        for _ in range(inner // 2):
            x, y = tour[i], tour[j]
            tour[i], tour[j] = y, x
            pos[y], pos[x] = i, j
            i = (i + 1) % n
            j = (j - 1) % n

    def two_opt(a):
        Da = D[a]
        i = pos[a]
        b = tour[(i + 1) % n]
        for c in neigh[a]:
            g = Da[b] - Da[c]
            if g <= EPS:
                break
            j = pos[c]
            d = tour[(j + 1) % n]
            if c == b or d == a:
                continue
            if g + D[c][d] - D[b][d] > EPS:
                reverse((i + 1) % n, j)
                return True
        b = tour[i - 1]
        for c in neigh[a]:
            g = Da[b] - Da[c]
            if g <= EPS:
                break
            j = pos[c]
            d = tour[j - 1]
            if c == b or d == a:
                continue
            if g + D[c][d] - D[b][d] > EPS:
                reverse(i, (j - 1) % n)
                return True
        return False

    def or_opt(a):
        i = pos[a]
        p = tour[i - 1]
        for L in (1, 2, 3):
            last = (i + L - 1) % n
            s1 = tour[last]
            nx = tour[(last + 1) % n]
            if nx == p or s1 == p:
                return False
            g = D[p][a] + D[s1][nx] - D[p][nx]
            if g <= EPS:
                continue
            seg = [tour[(i + k) % n] for k in range(L)]
            best = EPS
            move = None
            for e in ((a,) if L == 1 else (a, s1)):
                De = D[e]
                for c in neigh[e]:
                    if De[c] >= g:
                        break
                    if c in seg:
                        continue
                    jc = pos[c]
                    for u, v in ((c, tour[(jc + 1) % n]), (tour[jc - 1], c)):
                        if u in seg or v in seg:
                            continue
                        duv = D[u][v]
                        fwd = g - (D[u][a] + D[s1][v] - duv)
                        bwd = g - (D[u][s1] + D[a][v] - duv)
                        if fwd > best:
                            best, move = fwd, (u, False)
                        if bwd > best:
                            best, move = bwd, (u, True)
            if move is not None:
                u, flip = move
                rest = [tour[(last + 1 + k) % n] for k in range(n - L)]
                k = rest.index(u)
                if flip:
                    seg.reverse()
                tour[:] = rest[:k + 1] + seg + rest[k + 1:]
                reindex()
                return True
        return False

    while time.perf_counter() < deadline:
        changed = False
        for a in range(n):
            while two_opt(a):
                changed = True
        if time.perf_counter() > deadline:
            break
        if n >= 8:
            for a in range(n):
                if or_opt(a):
                    changed = True
        if not changed:
            break


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7
    D = distances(points)
    neigh = neighbours(D, 8)
    tour = nearest_neighbour(D, neigh, 0)
    improve(tour, D, neigh, deadline)
    return tour
