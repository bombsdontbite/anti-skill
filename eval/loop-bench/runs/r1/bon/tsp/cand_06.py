import math
import time
from collections import deque


def build_dist(points):
    n = len(points)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = points[i]
        Di = D[i]
        for j in range(i + 1, n):
            xj, yj = points[j]
            d = math.hypot(xi - xj, yi - yj)
            Di[j] = d
            D[j][i] = d
    return D


def build_neighbors(D, k):
    n = len(D)
    k = min(k, n - 1)
    out = []
    for i in range(n):
        Di = D[i]
        order = sorted((Di[j], j) for j in range(n) if j != i)
        out.append([j for _, j in order[:k]])
    return out


def convex_hull(points):
    n = len(points)
    idx = sorted(range(n), key=lambda i: (points[i][0], points[i][1], i))

    def cross(o, a, b):
        ox, oy = points[o]
        ax, ay = points[a]
        bx, by = points[b]
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)

    lower = []
    for i in idx:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], i) <= 0:
            lower.pop()
        lower.append(i)
    upper = []
    for i in reversed(idx):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], i) <= 0:
            upper.pop()
        upper.append(i)
    hull = lower[:-1] + upper[:-1]
    if not hull:
        hull = [idx[0]]
    return hull


def hull_insertion(D, hull):
    """Start from the convex hull and insert the remaining cities by cheapest insertion."""
    n = len(D)
    succ = [-1] * n
    for k in range(len(hull)):
        succ[hull[k - 1]] = hull[k]
    members = list(hull)
    outside = set(range(n)) - set(hull)
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
        for x in outside:
            if after[x] == u:
                cost[x], after[x] = best_for(x)
            else:
                Dx = D[x]
                c1 = Dx[u] + Dx[v] - D[u][v]
                if c1 < cost[x]:
                    cost[x] = c1
                    after[x] = u
                c2 = Dx[v] + Dx[w] - D[v][w]
                if c2 < cost[x]:
                    cost[x] = c2
                    after[x] = v
    s = hull[0]
    tour = [s]
    c = succ[s]
    while c != s:
        tour.append(c)
        c = succ[c]
    return tour


def local_search(tour, D, neigh, todo, deadline, maxseg=3):
    """2-opt + Or-opt with neighbour lists and a work queue (don't-look bits)."""
    n = len(tour)
    if n < 5:
        return
    pos = [0] * n
    for idx, c in enumerate(tour):
        pos[c] = idx
    queue = deque()
    inq = [False] * n
    for c in todo:
        if not inq[c]:
            inq[c] = True
            queue.append(c)
    eps = 1e-10
    use_or = n >= 8

    def reverse(i, j):
        inner = (j - i) % n + 1
        if inner * 2 > n:
            i, j = (j + 1) % n, (i - 1) % n
            inner = n - inner
        for _ in range(inner // 2):
            x = tour[i]
            y = tour[j]
            tour[i] = y
            pos[y] = i
            tour[j] = x
            pos[x] = j
            i += 1
            if i == n:
                i = 0
            j -= 1
            if j < 0:
                j = n - 1

    def or_move(a):
        i = pos[a]
        p = tour[i - 1]
        Dp = D[p]
        for seglen in range(1, maxseg + 1):
            last = (i + seglen - 1) % n
            s1 = tour[last]
            nx = tour[(last + 1) % n]
            if nx == p or s1 == p:
                break
            g = Dp[a] + D[s1][nx] - Dp[nx]
            if g <= eps:
                continue
            seg = [tour[(i + k) % n] for k in range(seglen)]
            best = eps
            move = None
            ends = (a,) if seglen == 1 else (a, s1)
            for e in ends:
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
                        gain = g - (D[u][a] + D[s1][v] - duv)
                        if gain > best:
                            best = gain
                            move = (u, v, False)
                        gain = g - (D[u][s1] + D[a][v] - duv)
                        if gain > best:
                            best = gain
                            move = (u, v, True)
            if move is not None:
                u, v, flip = move
                rest = [tour[(last + 1 + k) % n] for k in range(n - seglen)]
                k = rest.index(u)
                if flip:
                    seg.reverse()
                tour[:] = rest[:k + 1] + seg + rest[k + 1:]
                for idx, c in enumerate(tour):
                    pos[c] = idx
                return (p, nx, u, v, a, s1)
        return None

    count = 0
    while queue:
        count += 1
        if not (count & 31) and time.perf_counter() > deadline:
            break
        a = queue.popleft()
        inq[a] = False
        Da = D[a]
        i = pos[a]
        found = None
        b = tour[(i + 1) % n]
        dab = Da[b]
        for c in neigh[a]:
            g = dab - Da[c]
            if g <= eps:
                break
            j = pos[c]
            d = tour[(j + 1) % n]
            if c == b or d == a:
                continue
            if g + D[c][d] - D[b][d] > eps:
                reverse((i + 1) % n, j)
                found = (a, b, c, d)
                break
        if found is None:
            b = tour[i - 1]
            dab = Da[b]
            for c in neigh[a]:
                g = dab - Da[c]
                if g <= eps:
                    break
                j = pos[c]
                d = tour[j - 1]
                if c == b or d == a:
                    continue
                if g + D[c][d] - D[b][d] > eps:
                    reverse(i, (j - 1) % n)
                    found = (a, b, c, d)
                    break
        if found is None and use_or:
            found = or_move(a)
        if found is not None:
            for c in found:
                if not inq[c]:
                    inq[c] = True
                    queue.append(c)


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.75
    D = build_dist(points)
    neigh = build_neighbors(D, 12)
    tour = hull_insertion(D, convex_hull(points))
    local_search(tour, D, neigh, tour[:], deadline)
    return tour
