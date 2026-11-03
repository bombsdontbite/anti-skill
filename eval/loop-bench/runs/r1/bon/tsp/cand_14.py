import math
import random
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


def tour_length(t, D):
    total = D[t[-1]][t[0]]
    for k in range(1, len(t)):
        total += D[t[k - 1]][t[k]]
    return total


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


def segment_kick(t, neigh, rnd):
    """Cut out a chain longer than Or-opt handles and drop it beside a spatial neighbour."""
    n = len(t)
    L = rnd.randint(4, max(4, min(12, n // 3)))
    s = rnd.randrange(n)
    r = t[s:] + t[:s]
    seg = r[:L]
    rest = r[L:]
    segset = set(seg)
    options = [c for c in neigh[seg[0]] + neigh[seg[-1]] if c not in segset]
    if options:
        k = rest.index(options[rnd.randrange(len(options))])
    else:
        k = rnd.randrange(len(rest))
    if rnd.random() < 0.5:
        seg.reverse()
    new = rest[:k + 1] + seg + rest[k + 1:]
    m = len(rest)
    touched = [seg[0], seg[-1], rest[k], rest[(k + 1) % m], rest[0], rest[-1]]
    return new, touched


def solve(points):
    """ILS with chain-relocation kicks and a shrinking acceptance threshold."""
    n = len(points)
    if n <= 3:
        return list(range(n))
    start = time.perf_counter()
    deadline = start + 0.75
    rnd = random.Random(99)
    D = build_dist(points)
    neigh = build_neighbors(D, 10)

    cur = farthest_insertion(D)
    local_search(cur, D, neigh, cur[:], deadline)
    if n < 12:
        return cur
    cur_len = tour_length(cur, D)
    best = cur[:]
    best_len = cur_len
    avg = cur_len / n
    span = deadline - time.perf_counter()
    t_begin = time.perf_counter()
    while True:
        now = time.perf_counter()
        if now >= deadline:
            break
        frac = (now - t_begin) / span if span > 0 else 1.0
        threshold = 0.04 * avg * (1.0 - frac)
        t, touched = segment_kick(cur, neigh, rnd)
        local_search(t, D, neigh, touched, deadline)
        L = tour_length(t, D)
        if L < cur_len + threshold:
            cur = t
            cur_len = L
            if L < best_len - 1e-12:
                best = t[:]
                best_len = L
    return best
