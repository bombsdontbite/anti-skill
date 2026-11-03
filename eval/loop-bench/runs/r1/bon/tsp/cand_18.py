import math
import time

EPS = 1e-10


def savings_tour(points, D):
    """Clarke-Wright savings around a central hub, merged greedily into one path."""
    n = len(D)
    cx = sum(p[0] for p in points) / n
    cy = sum(p[1] for p in points) / n
    hub = min(range(n), key=lambda i: (points[i][0] - cx) ** 2 + (points[i][1] - cy) ** 2)
    Dh = D[hub]
    others = [i for i in range(n) if i != hub]
    sav = []
    for x in range(len(others)):
        i = others[x]
        Di = D[i]
        hi = Dh[i]
        for y in range(x + 1, len(others)):
            j = others[y]
            sav.append((hi + Dh[j] - Di[j], i, j))
    sav.sort(reverse=True)

    deg = [0] * n
    parent = list(range(n))
    adj = [[] for _ in range(n)]

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    need = len(others) - 1
    links = 0
    for _, i, j in sav:
        if links >= need:
            break
        if deg[i] < 2 and deg[j] < 2:
            ri = find(i)
            rj = find(j)
            if ri != rj:
                parent[ri] = rj
                deg[i] += 1
                deg[j] += 1
                adj[i].append(j)
                adj[j].append(i)
                links += 1
    first = others[0]
    for v in others:
        if deg[v] < 2:
            first = v
            break
    path = [first]
    prev = -1
    cur = first
    while len(path) < len(others):
        nb = adj[cur]
        nxt = nb[0] if nb[0] != prev else nb[1]
        prev, cur = cur, nxt
        path.append(nxt)
    return [hub] + path


def make_improver(tour, D, neigh):
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
            if c != b and d != a and g + D[c][d] - D[b][d] > EPS:
                reverse((i + 1) % n, j)
                return True
        b = tour[i - 1]
        for c in neigh[a]:
            g = Da[b] - Da[c]
            if g <= EPS:
                break
            j = pos[c]
            d = tour[j - 1]
            if c != b and d != a and g + D[c][d] - D[b][d] > EPS:
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
            best, move = EPS, None
            for e in ((a,) if L == 1 else (a, s1)):
                for c in neigh[e]:
                    if D[e][c] >= g:
                        break
                    if c in seg:
                        continue
                    jc = pos[c]
                    for u, v in ((c, tour[(jc + 1) % n]), (tour[jc - 1], c)):
                        if u in seg or v in seg:
                            continue
                        duv = D[u][v]
                        f = g - (D[u][a] + D[s1][v] - duv)
                        r = g - (D[u][s1] + D[a][v] - duv)
                        if f > best:
                            best, move = f, (u, False)
                        if r > best:
                            best, move = r, (u, True)
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

    def run(deadline):
        while time.perf_counter() < deadline:
            changed = False
            for a in range(n):
                if two_opt(a):
                    changed = True
            if n >= 8:
                for a in range(n):
                    if or_opt(a):
                        changed = True
            if not changed:
                break

    return run


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7
    D = [[math.hypot(p[0] - q[0], p[1] - q[1]) for q in points] for p in points]
    neigh = []
    for i in range(n):
        row = D[i]
        neigh.append([j for _, j in sorted((row[j], j) for j in range(n) if j != i)[:10]])
    tour = savings_tour(points, D)
    make_improver(tour, D, neigh)(deadline)
    return tour
