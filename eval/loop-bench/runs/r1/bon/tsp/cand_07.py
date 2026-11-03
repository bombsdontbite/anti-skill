import math
import time

EPS = 1e-10


def hilbert_key(x, y, order):
    side = 1 << order
    d = 0
    s = side >> 1
    while s > 0:
        rx = 1 if (x & s) else 0
        ry = 1 if (y & s) else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x = side - 1 - x
                y = side - 1 - y
            x, y = y, x
        s >>= 1
    return d


def hilbert_order(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    minx, miny = min(xs), min(ys)
    span = max(max(xs) - minx, max(ys) - miny, 1e-12)
    order = 16
    scale = ((1 << order) - 1) / span
    keys = []
    for i, (x, y) in enumerate(points):
        hx = int((x - minx) * scale)
        hy = int((y - miny) * scale)
        keys.append((hilbert_key(hx, hy, order), i))
    keys.sort()
    return [i for _, i in keys]


def solve(points):
    n = len(points)
    if n <= 3:
        return list(range(n))
    deadline = time.perf_counter() + 0.7

    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = points[i]
        for j in range(i + 1, n):
            d = math.hypot(xi - points[j][0], yi - points[j][1])
            D[i][j] = d
            D[j][i] = d
    K = min(10, n - 1)
    neigh = []
    for i in range(n):
        row = D[i]
        neigh.append(sorted((j for j in range(n) if j != i), key=lambda j: row[j])[:K])

    tour = hilbert_order(points)
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

    def node_insertion(a):
        """Or-opt: lift a chain starting at a and drop it next to a near neighbour."""
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
            for e in set((a, s1)):
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
                return True
        return False

    def two_opt(a):
        i = pos[a]
        Da = D[a]
        for side in (1, -1):
            b = tour[(i + 1) % n] if side == 1 else tour[i - 1]
            dab = Da[b]
            for c in neigh[a]:
                g = dab - Da[c]
                if g <= EPS:
                    break
                j = pos[c]
                d = tour[(j + 1) % n] if side == 1 else tour[j - 1]
                if c == b or d == a:
                    continue
                if g + D[c][d] - D[b][d] > EPS:
                    if side == 1:
                        reverse((i + 1) % n, j)
                    else:
                        reverse(i, (j - 1) % n)
                    return True
        return False

    while time.perf_counter() < deadline:
        moves = 0
        for a in range(n):
            if two_opt(a):
                moves += 1
            elif n >= 8 and node_insertion(a):
                moves += 1
        if moves == 0:
            break
    return tour
