import math, random, time

TIME = 0.7
K = 8
WIN = 50
PG = 0.25
STALL = 400


def solve(points):
    t0 = time.time()
    n = len(points)
    if n <= 3:
        return list(range(n))
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    D = [[math.hypot(xs[i] - xs[j], ys[i] - ys[j]) for j in range(n)] for i in range(n)]
    nbr = [sorted((j for j in range(n) if j != i), key=D[i].__getitem__)[:K] for i in range(n)]

    # nearest neighbour start
    left = set(range(1, n)); tour = [0]
    while left:
        c = D[tour[-1]]
        nx = min(left, key=c.__getitem__)
        left.remove(nx); tour.append(nx)
    pos = [0] * n
    for i, c in enumerate(tour):
        pos[c] = i

    def reverse(i, j):
        # reverse tour[i..j] cyclically, choosing the shorter side
        inner = (j - i) % n + 1
        if inner * 2 > n:
            i, j = (j + 1) % n, (i - 1) % n
            inner = n - inner
        for _ in range(inner // 2):
            a, b = tour[i], tour[j]
            tour[i], tour[j] = b, a
            pos[b], pos[a] = i, j
            i = (i + 1) % n; j = (j - 1) % n

    def two_opt_node(a):
        for succ in (True, False):
            pa = pos[a]
            b = tour[(pa + 1) % n] if succ else tour[(pa - 1) % n]
            dab = D[a][b]
            for c in nbr[a]:
                g = dab - D[a][c]
                if g <= 1e-12:
                    break
                pc = pos[c]
                d = tour[(pc + 1) % n] if succ else tour[(pc - 1) % n]
                if d == a or c == b:
                    continue
                if g + D[c][d] - D[b][d] > 1e-12:
                    if succ:
                        reverse((pa + 1) % n, pc)
                    else:
                        reverse(pc, (pa - 1) % n)
                    return (a, b, c, d)
        return None

    def or_opt_node(a):
        # move segment starting at a (len 1..3) next to a neighbour
        pa = pos[a]
        p = tour[pa - 1]
        for L in (1, 2, 3):
            last = tour[(pa + L - 1) % n]; q = tour[(pa + L) % n]
            if q == p:
                break
            rem = D[p][a] + D[last][q] - D[p][q]
            if rem <= 1e-12:
                continue
            for end, other in ((a, last), (last, a)):
                De = D[end]; Do = D[other]
                for c in nbr[end]:
                    dc = De[c]
                    if dc >= rem:
                        break
                    pc = pos[c]
                    if (pc - pa) % n < L:
                        continue
                    Dc = D[c]
                    for d in (tour[(pc + 1) % n], tour[pc - 1]):
                        if (pos[d] - pa) % n < L:
                            continue
                        add = dc + Do[d] - Dc[d]
                        if add < rem - 1e-12:
                            seg = [tour[(pa + k) % n] for k in range(L)]
                            segset = set(seg)
                            rest = [x for x in tour if x not in segset]
                            ic = rest.index(c)
                            if rest[(ic + 1) % len(rest)] == d:
                                ins = ic + 1
                                piece = seg if end == a else seg[::-1]
                            else:
                                ins = ic
                                piece = seg[::-1] if end == a else seg
                            rest[ins:ins] = piece
                            tour[:] = rest
                            for i2, x in enumerate(tour):
                                pos[x] = i2
                            return (p, q, c, d, a, last)
        return None

    def local_search(active):
        queue = list(active); inq = [False] * n
        for a in queue:
            inq[a] = True
        while queue:
            a = queue.pop(); inq[a] = False
            r = two_opt_node(a) or or_opt_node(a)
            if r:
                for x in r:
                    if not inq[x]:
                        inq[x] = True; queue.append(x)
                if not inq[a]:
                    inq[a] = True; queue.append(a)

    def tlen(t):
        return sum(D[t[i - 1]][t[i]] for i in range(n))

    local_search(range(n))
    if n < 8:
        return tour
    rng = random.Random(1)
    best = tour[:]; bl = tlen(tour); cur = bl; acc = best[:]; stall = 0
    while time.time() - t0 < TIME:
        # segment-local double bridge
        w = min(n - 1, WIN) if rng.random() >= PG else n - 1
        s = rng.randrange(n)
        a, b, c = sorted(rng.sample(range(1, w), 3))
        idx = [(s + k) % n for k in range(w + 1)]
        seg = [tour[i] for i in idx]
        new = seg[:a] + seg[b:c] + seg[a:b] + seg[c:]
        for i, x in zip(idx, new):
            tour[i] = x; pos[x] = i
        touched = [seg[a - 1], seg[a], seg[b - 1], seg[b], seg[c - 1], seg[c]]
        local_search(touched)
        L = tlen(tour)
        if L <= cur + 1e-12:
            if L < cur - 1e-12:
                stall = 0
            else:
                stall += 1
            cur = L; acc = tour[:]
            if L < bl - 1e-12:
                bl = L; best = tour[:]
        elif stall > STALL:
            cur = L; acc = tour[:]; stall = 0
        else:
            stall += 1
            tour[:] = acc
            for i, x in enumerate(tour):
                pos[x] = i
    return best
