import math
import time
from collections import deque
from itertools import combinations


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


def christofides_like(D):
    """MST + greedy matching of odd-degree vertices + Euler circuit + shortcuts."""
    n = len(D)
    inf = float("inf")
    in_tree = [False] * n
    best = [inf] * n
    parent = [-1] * n
    best[0] = 0.0
    for _ in range(n):
        u = -1
        bu = inf
        for v in range(n):
            if not in_tree[v] and best[v] < bu:
                bu = best[v]
                u = v
        in_tree[u] = True
        Du = D[u]
        for v in range(n):
            if not in_tree[v] and Du[v] < best[v]:
                best[v] = Du[v]
                parent[v] = u

    edges = []
    for v in range(n):
        if parent[v] >= 0:
            edges.append((v, parent[v]))
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    odd = [v for v in range(n) if deg[v] % 2 == 1]
    pairs = sorted((D[a][b], a, b) for a, b in combinations(odd, 2))
    matched = [False] * n
    for _, a, b in pairs:
        if not matched[a] and not matched[b]:
            matched[a] = matched[b] = True
            edges.append((a, b))

    adj = [[] for _ in range(n)]
    for e, (a, b) in enumerate(edges):
        adj[a].append(e)
        adj[b].append(e)
    used = [False] * len(edges)
    ptr = [0] * n
    stack = [0]
    circuit = []
    while stack:
        v = stack[-1]
        lst = adj[v]
        while ptr[v] < len(lst) and used[lst[ptr[v]]]:
            ptr[v] += 1
        if ptr[v] == len(lst):
            circuit.append(stack.pop())
        else:
            e = lst[ptr[v]]
            used[e] = True
            a, b = edges[e]
            stack.append(b if a == v else a)

    seen = [False] * n
    tour = []
    for v in circuit:
        if not seen[v]:
            seen[v] = True
            tour.append(v)
    for v in range(n):
        if not seen[v]:
            tour.append(v)
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
    neigh = build_neighbors(D, 10)
    tour = christofides_like(D)
    local_search(tour, D, neigh, tour[:], deadline)
    return tour
