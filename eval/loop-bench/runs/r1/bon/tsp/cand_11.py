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


def greedy_edge(D, neigh):
    """Greedy edge on the candidate graph, fragments joined by nearest free endpoint."""
    n = len(D)
    pairs = set()
    for i in range(n):
        for j in neigh[i]:
            pairs.add((i, j) if i < j else (j, i))
    cand = sorted((D[i][j], i, j) for i, j in pairs)
    deg = [0] * n
    parent = list(range(n))
    adj = [[] for _ in range(n)]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def link(i, j):
        parent[find(i)] = find(j)
        deg[i] += 1
        deg[j] += 1
        adj[i].append(j)
        adj[j].append(i)

    edges = 0
    for _, i, j in cand:
        if deg[i] < 2 and deg[j] < 2 and find(i) != find(j):
            link(i, j)
            edges += 1
    while edges < n - 1:
        ends = [v for v in range(n) if deg[v] < 2]
        best = None
        bd = float("inf")
        for x in range(len(ends)):
            a = ends[x]
            ra = find(a)
            Da = D[a]
            for y in range(x + 1, len(ends)):
                b = ends[y]
                if Da[b] < bd and find(b) != ra:
                    bd = Da[b]
                    best = (a, b)
        link(best[0], best[1])
        edges += 1
    start = 0
    for v in range(n):
        if deg[v] < 2:
            start = v
            break
    tour = [start]
    prev = -1
    cur = start
    while len(tour) < n:
        nb = adj[cur]
        nxt = nb[0] if nb[0] != prev else nb[1]
        prev, cur = cur, nxt
        tour.append(nxt)
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


def anneal(tour, D, neigh, rnd, t_start, t_stop, T0, T1):
    """Simulated annealing over neighbour-list 2-opt moves; returns the best tour seen."""
    n = len(tour)
    t = tour[:]
    pos = [0] * n
    for idx, c in enumerate(t):
        pos[c] = idx
    K = len(neigh[0])
    cur = tour_length(t, D)
    best = t[:]
    best_len = cur
    rand = rnd.random
    rint = rnd.randrange
    exp = math.exp
    span = max(t_stop - t_start, 1e-6)

    def reverse(i, j):
        inner = (j - i) % n + 1
        if inner * 2 > n:
            i, j = (j + 1) % n, (i - 1) % n
            inner = n - inner
        for _ in range(inner // 2):
            x = t[i]
            y = t[j]
            t[i] = y
            pos[y] = i
            t[j] = x
            pos[x] = j
            i += 1
            if i == n:
                i = 0
            j -= 1
            if j < 0:
                j = n - 1

    while True:
        now = time.perf_counter()
        if now >= t_stop:
            break
        frac = (now - t_start) / span
        T = T0 * (T1 / T0) ** frac
        for _ in range(1500):
            a = rint(n)
            c = neigh[a][rint(K)]
            i = pos[a]
            j = pos[c]
            if rand() < 0.5:
                b = t[(i + 1) % n]
                d = t[(j + 1) % n]
                if c == b or d == a:
                    continue
                delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                if delta < 0 or rand() < exp(-delta / T):
                    reverse((i + 1) % n, j)
                    cur += delta
            else:
                b = t[i - 1]
                d = t[j - 1]
                if c == b or d == a:
                    continue
                delta = D[a][c] + D[b][d] - D[a][b] - D[c][d]
                if delta < 0 or rand() < exp(-delta / T):
                    reverse(i, (j - 1) % n)
                    cur += delta
        if cur < best_len - 1e-12:
            best_len = cur
            best = t[:]
    return best


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    start = time.perf_counter()
    deadline = start + 0.75
    rnd = random.Random(1234)
    D = build_dist(points)
    neigh = build_neighbors(D, 8)

    base = greedy_edge(D, neigh)
    local_search(base, D, neigh, base[:], start + 0.2)
    base_len = tour_length(base, D)
    if n < 8:
        return base

    avg = max(base_len / n, 1e-9)
    sa_start = time.perf_counter()
    cand = anneal(base, D, neigh, rnd, sa_start, start + 0.62, 0.06 * avg, 0.002 * avg)
    local_search(cand, D, neigh, cand[:], deadline)
    if tour_length(cand, D) < base_len:
        return cand
    return base
