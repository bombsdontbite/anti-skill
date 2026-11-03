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


def nearest_neighbour(D, neigh, start):
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
            Dc = D[cur]
            bd = INF
            for v in range(n):
                if not seen[v] and Dc[v] < bd:
                    bd = Dc[v]
                    nxt = v
        seen[nxt] = True
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


def solve(points):
    """Ant Colony System on candidate lists; iteration-best ant polished by local search."""
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.72
    rnd = random.Random(22)
    rand = rnd.random
    D = build_dist(points)
    neigh = build_neighbors(D, 10)

    nn = nearest_neighbour(D, neigh, 0)
    nn_len = max(tour_length(nn, D), 1e-12)
    best = nn[:]
    local_search(best, D, neigh, best[:], deadline)
    best_len = tour_length(best, D)

    q0, rho, xi, ants = 0.9, 0.1, 0.1, 8
    tau0 = 1.0 / (n * nn_len)
    tau = [[tau0] * n for _ in range(n)]
    eta = [[(1.0 / (d * d) if d > 1e-9 else 1e18) for d in row] for row in D]

    def construct():
        cur = rnd.randrange(n)
        seen = [False] * n
        seen[cur] = True
        left = set(range(n))
        left.discard(cur)
        t = [cur]
        while left:
            tc = tau[cur]
            hc = eta[cur]
            cands = []
            weights = []
            for c in neigh[cur]:
                if not seen[c]:
                    cands.append(c)
                    weights.append(tc[c] * hc[c])
            if cands:
                if rand() < q0:
                    bi = 0
                    for z in range(1, len(cands)):
                        if weights[z] > weights[bi]:
                            bi = z
                    nxt = cands[bi]
                else:
                    r = rand() * sum(weights)
                    acc = 0.0
                    nxt = cands[-1]
                    for c, w in zip(cands, weights):
                        acc += w
                        if acc >= r:
                            nxt = c
                            break
            else:
                Dc = D[cur]
                nxt = -1
                bd = INF
                for v in left:
                    if Dc[v] < bd:
                        bd = Dc[v]
                        nxt = v
            val = (1.0 - xi) * tau[cur][nxt] + xi * tau0
            tau[cur][nxt] = val
            tau[nxt][cur] = val
            seen[nxt] = True
            left.discard(nxt)
            t.append(nxt)
            cur = nxt
        return t

    while time.perf_counter() < deadline:
        it_best = None
        it_len = INF
        for _ in range(ants):
            if time.perf_counter() > deadline:
                break
            t = construct()
            L = tour_length(t, D)
            if L < it_len:
                it_len = L
                it_best = t
        if it_best is None:
            break
        local_search(it_best, D, neigh, it_best[:], deadline)
        it_len = tour_length(it_best, D)
        if it_len < best_len:
            best_len = it_len
            best = it_best[:]
        dep = rho / best_len if best_len > 0 else 0.0
        for k in range(n):
            u = best[k - 1]
            v = best[k]
            val = (1.0 - rho) * tau[u][v] + dep
            tau[u][v] = val
            tau[v][u] = val
    return best
