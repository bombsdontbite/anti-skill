import math
import time
from collections import deque

INF = float("inf")


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


def nearest_neighbour(D, start):
    n = len(D)
    left = set(range(n))
    left.discard(start)
    tour = [start]
    cur = start
    while left:
        Dc = D[cur]
        nxt = min(left, key=lambda j: Dc[j])
        left.discard(nxt)
        tour.append(nxt)
        cur = nxt
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


def window_dp(t, D, k, deadline):
    """Slide a window along the tour; reorder its k interior cities optimally (Held-Karp)."""
    n = len(t)
    if n < k + 3:
        return []
    full = (1 << k) - 1
    size = 1 << k
    changed = []
    for i in range(n):
        if not (i & 7) and time.perf_counter() > deadline:
            break
        s = t[i]
        mids = [t[(i + 1 + q) % n] for q in range(k)]
        e = t[(i + k + 1) % n]
        old = D[s][mids[0]] + D[mids[-1]][e]
        for q in range(k - 1):
            old += D[mids[q]][mids[q + 1]]
        dp = [[INF] * k for _ in range(size)]
        par = [[-1] * k for _ in range(size)]
        Ds = D[s]
        for q in range(k):
            dp[1 << q][q] = Ds[mids[q]]
        rows = [D[m] for m in mids]
        for mask in range(1, size):
            row = dp[mask]
            for last in range(k):
                cost = row[last]
                if cost == INF:
                    continue
                Dl = rows[last]
                for q in range(k):
                    bit = 1 << q
                    if mask & bit:
                        continue
                    nm = mask | bit
                    c2 = cost + Dl[mids[q]]
                    if c2 < dp[nm][q]:
                        dp[nm][q] = c2
                        par[nm][q] = last
        best = INF
        bl = -1
        for q in range(k):
            c = dp[full][q] + rows[q][e]
            if c < best:
                best = c
                bl = q
        if best < old - 1e-10:
            order = []
            mask = full
            q = bl
            while q != -1:
                order.append(mids[q])
                pq = par[mask][q]
                mask ^= 1 << q
                q = pq
            order.reverse()
            for q in range(k):
                t[(i + 1 + q) % n] = order[q]
            changed.extend(order)
            changed.append(s)
            changed.append(e)
    return changed


def solve(points):
    """Neighbour-list 2-opt/Or-opt alternated with exact re-ordering of short tour windows."""
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.72
    D = build_dist(points)
    neigh = build_neighbors(D, 10)
    tour = nearest_neighbour(D, 0)
    local_search(tour, D, neigh, tour[:], deadline)
    for width in (5, 6):
        while time.perf_counter() < deadline:
            touched = window_dp(tour, D, width, deadline)
            if not touched:
                break
            local_search(tour, D, neigh, touched, deadline)
    return tour
