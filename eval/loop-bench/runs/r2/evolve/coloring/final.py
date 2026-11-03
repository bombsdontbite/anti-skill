import time, random, heapq

BUDGET = 0.6
SWITCH = 0.35


def dsatur(n, adj):
    colors = [-1] * n
    satsets = [set() for _ in range(n)]
    deg = [len(a) for a in adj]
    heap = [(0, -deg[u], u) for u in range(n)]
    heapq.heapify(heap)
    done = 0
    while done < n:
        s, d, u = heapq.heappop(heap)
        if colors[u] != -1 or -s != len(satsets[u]):
            continue
        taken = satsets[u]
        c = 0
        while c in taken:
            c += 1
        colors[u] = c
        done += 1
        for v in adj[u]:
            if colors[v] == -1 and c not in satsets[v]:
                satsets[v].add(c)
                heapq.heappush(heap, (-len(satsets[v]), d, v))
    return colors


def partialcol(n, adj, k, init, deadline, rnd):
    col = [c if c < k else -1 for c in init]
    gamma = [[0] * k for _ in range(n)]
    for u in range(n):
        cu = col[u]
        if cu >= 0:
            for v in adj[u]:
                gamma[v][cu] += 1
    U = set(u for u in range(n) if col[u] < 0)
    best = len(U)
    tabu = [[0] * k for _ in range(n)]
    it = 0
    alpha = 0.6
    rr = rnd.random
    perf = time.perf_counter
    K = range(k)
    while U:
        it += 1
        if (it & 15) == 0:
            now = perf()
            if now > deadline:
                return None
            alpha = 0.6 if now < deadline - SWITCH else 1.2
        asp = best - len(U)
        Ul = list(U)
        mins = [min(gamma[v]) for v in Ul]
        target = min(mins)
        bm = []
        while not bm:
            for i in range(len(Ul)):
                if mins[i] <= target:
                    v = Ul[i]
                    g = gamma[v]
                    tv = tabu[v]
                    for c in K:
                        if g[c] == target and (tv[c] <= it or target - 1 < asp):
                            bm.append((v, c))
            if not bm:
                target += 1
                if target > n:
                    break
        if not bm:
            continue
        v, c = bm[int(rr() * len(bm))]
        U.discard(v)
        col[v] = c
        for w in adj[v]:
            gamma[w][c] += 1
        tt = int(alpha * len(U)) + int(rr() * 10)
        for w in adj[v]:
            if col[w] == c:
                col[w] = -1
                U.add(w)
                for x in adj[w]:
                    gamma[x][c] -= 1
                tabu[w][c] = it + tt
        if len(U) < best:
            best = len(U)
    return col


def color(n, edges):
    t0 = time.perf_counter()
    deadline = t0 + BUDGET
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    best = dsatur(n, adj)
    k = max(best) + 1 if n else 0
    rnd = random.Random(1)
    while k > 1 and time.perf_counter() < deadline:
        res = partialcol(n, adj, k - 1, best, deadline, rnd)
        if res is None:
            break
        best = res
        k -= 1
    return best
