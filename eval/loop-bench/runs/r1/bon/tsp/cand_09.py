import math
import time

EPS = 1e-10


def mst_preorder(D):
    """Prim's MST, then a depth-first walk that visits nearer children first (double-tree tour)."""
    n = len(D)
    inf = float("inf")
    in_tree = [False] * n
    key = [inf] * n
    parent = [-1] * n
    key[0] = 0.0
    for _ in range(n):
        u = -1
        ku = inf
        for v in range(n):
            if not in_tree[v] and key[v] < ku:
                ku = key[v]
                u = v
        in_tree[u] = True
        Du = D[u]
        for v in range(n):
            if not in_tree[v] and Du[v] < key[v]:
                key[v] = Du[v]
                parent[v] = u
    children = [[] for _ in range(n)]
    for v in range(n):
        if parent[v] >= 0:
            children[parent[v]].append(v)
    order = []
    stack = [0]
    while stack:
        v = stack.pop()
        order.append(v)
        Dv = D[v]
        stack.extend(sorted(children[v], key=lambda c: -Dv[c]))
    return order


def improve(tour, D, neigh, deadline):
    n = len(tour)
    pos = [0] * n
    for idx, c in enumerate(tour):
        pos[c] = idx

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

    def two_opt_sweep():
        count = 0
        for a in range(n):
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
                    count += 1
                    break
            i = pos[a]
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
                    count += 1
                    break
        return count

    def or_sweep():
        count = 0
        for a in range(n):
            i = pos[a]
            p = tour[i - 1]
            for L in (1, 2, 3):
                last = (i + L - 1) % n
                s1 = tour[last]
                nx = tour[(last + 1) % n]
                if nx == p or s1 == p:
                    break
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
                    for idx, c in enumerate(tour):
                        pos[c] = idx
                    count += 1
                    break
        return count

    while time.perf_counter() < deadline:
        moved = two_opt_sweep()
        if time.perf_counter() > deadline:
            break
        if n >= 8:
            moved += or_sweep()
        if moved == 0:
            break


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7
    D = [[math.hypot(p[0] - q[0], p[1] - q[1]) for q in points] for p in points]
    neigh = []
    for i in range(n):
        row = D[i]
        neigh.append([j for _, j in sorted((row[j], j) for j in range(n) if j != i)[:8]])
    tour = mst_preorder(D)
    improve(tour, D, neigh, deadline)
    return tour
