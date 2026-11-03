import math
import random
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


def tour_length(t, D):
    total = D[t[-1]][t[0]]
    for k in range(1, len(t)):
        total += D[t[k - 1]][t[k]]
    return total


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


def randomized_nn(D, neigh, rnd, greedy):
    n = len(D)
    cur = rnd.randrange(n)
    seen = [False] * n
    seen[cur] = True
    t = [cur]
    for _ in range(n - 1):
        opts = []
        for c in neigh[cur]:
            if not seen[c]:
                opts.append(c)
                if len(opts) == 2:
                    break
        if opts:
            if greedy or len(opts) == 1 or rnd.random() < 0.8:
                nxt = opts[0]
            else:
                nxt = opts[1]
        else:
            Dc = D[cur]
            nxt = -1
            bd = INF
            for v in range(n):
                if not seen[v] and Dc[v] < bd:
                    bd = Dc[v]
                    nxt = v
        seen[nxt] = True
        t.append(nxt)
        cur = nxt
    return t


def recombine(p1, p2, D, neigh, rnd):
    """Edge recombination: walk using parent edges, shared edges first, shortest first."""
    n = len(p1)
    adj = [[] for _ in range(n)]
    for p in (p1, p2):
        for k in range(n):
            u = p[k - 1]
            v = p[k]
            adj[u].append(v)
            adj[v].append(u)
    seen = [False] * n
    cur = rnd.randrange(n)
    seen[cur] = True
    child = [cur]
    for _ in range(n - 1):
        Dc = D[cur]
        cand = [v for v in adj[cur] if not seen[v]]
        nxt = -1
        if cand:
            shared = [v for v in cand if cand.count(v) > 1]
            pool = shared if shared else cand
            bd = INF
            for v in pool:
                if Dc[v] < bd:
                    bd = Dc[v]
                    nxt = v
        else:
            for v in neigh[cur]:
                if not seen[v]:
                    nxt = v
                    break
            if nxt < 0:
                bd = INF
                for v in range(n):
                    if not seen[v] and Dc[v] < bd:
                        bd = Dc[v]
                        nxt = v
        seen[nxt] = True
        child.append(nxt)
        cur = nxt
    return child


def solve(points):
    """Small memetic algorithm: locally optimised population, edge-recombination offspring."""
    n = len(points)
    if n <= 3:
        return list(range(n))
    start = time.perf_counter()
    deadline = start + 0.75
    rnd = random.Random(16)
    D = build_dist(points)
    neigh = build_neighbors(D, 8)

    pop = []
    for k in range(8):
        if pop and time.perf_counter() > start + 0.3:
            break
        t = randomized_nn(D, neigh, rnd, k == 0)
        local_search(t, D, neigh, t[:], deadline)
        pop.append([tour_length(t, D), t])

    while len(pop) >= 2 and time.perf_counter() < deadline:
        i, j = rnd.sample(range(len(pop)), 2)
        child = recombine(pop[i][1], pop[j][1], D, neigh, rnd)
        local_search(child, D, neigh, child[:], deadline)
        L = tour_length(child, D)
        worst = 0
        for z in range(1, len(pop)):
            if pop[z][0] > pop[worst][0]:
                worst = z
        duplicate = False
        for q in pop:
            if abs(q[0] - L) < 1e-9:
                duplicate = True
                break
        if not duplicate and L < pop[worst][0]:
            pop[worst] = [L, child]

    best = pop[0]
    for q in pop:
        if q[0] < best[0]:
            best = q
    return best[1]
