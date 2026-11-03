import math, random, time
from collections import deque


def solve(points):
    """ILS: NN start; 2-opt + Or-opt (segments 1-3) on 10-nearest lists with a don't-look queue;
    double-bridge kicks (70% within 50 positions, 30% global), equal-or-better acceptance,
    restart from the best tour with 4 global double-bridges after 400 kicks without a new best."""
    t_end = time.perf_counter() + 0.62
    t_hard = t_end + 0.05
    PG = 0.3
    n = len(points)
    if n <= 4:
        return list(range(n))
    D = [[math.dist(a, b) for b in points] for a in points]
    K = 10
    nb = [[j for j in sorted(range(n), key=lambda j: D[i][j]) if j != i][:K] for i in range(n)]
    rnd = random.Random(12345)
    EPS = 1e-10
    GAIN = [0.0]

    left = set(range(1, n)); t = [0]
    while left:
        row = D[t[-1]]
        nx = min(left, key=lambda j: row[j])
        left.remove(nx); t.append(nx)
    pos = [0] * n
    for i, c in enumerate(t):
        pos[c] = i

    def rev(x, y):
        # reverse tour positions x..y going forward (cyclic)
        if x <= y:
            t[x:y + 1] = t[x:y + 1][::-1]
            for k in range(x, y + 1):
                pos[t[k]] = k
        else:
            x, y = y + 1, x - 1
            if x <= y:
                t[x:y + 1] = t[x:y + 1][::-1]
                for k in range(x, y + 1):
                    pos[t[k]] = k

    def try2opt(a):
        i = pos[a]
        for succ in (1, 0):
            b = t[(i + 1) % n] if succ else t[i - 1]
            dab = D[a][b]
            Da = D[a]
            for c in nb[a]:
                g1 = dab - Da[c]
                if g1 <= EPS:
                    break
                j = pos[c]
                d = t[(j + 1) % n] if succ else t[j - 1]
                if c == b or d == a:
                    continue
                gain = g1 + D[c][d] - D[b][d]
                if gain > EPS:
                    GAIN[0] += gain
                    if succ:
                        rev((i + 1) % n, j)
                    else:
                        rev(j, (i - 1) % n)
                    return (a, b, c, d)
        return None

    def tryor(a):
        i0 = pos[a]
        for L in (1, 2, 3):
            for start in ((i0, (i0 - L + 1) % n) if L > 1 else (i0,)):
                s0 = t[start]; s1 = t[(start + L - 1) % n]
                p = t[start - 1]; q = t[(start + L) % n]
                rem = D[p][s0] + D[s1][q] - D[p][q]
                if rem <= EPS:
                    continue
                for e in ((s0, s1) if L > 1 else (s0,)):
                    other = s1 if e == s0 else s0
                    De = D[e]; Do = D[other]
                    for c in nb[e]:
                        dec = De[c]
                        if dec >= rem:
                            break
                        j = pos[c]
                        if (j - start) % n < L:
                            continue
                        Dc = D[c]
                        for d in (t[(j + 1) % n], t[j - 1]):
                            if (pos[d] - start) % n < L:
                                continue
                            gain = rem - (dec + Do[d] - Dc[d])
                            if gain > EPS:
                                GAIN[0] += gain
                                segl = [t[(start + k) % n] for k in range(L)]
                                seg = set(segl)
                                rest = [x for x in t if x not in seg]
                                ci = rest.index(c)
                                if rest[(ci + 1) % len(rest)] == d:
                                    sl = segl if e == s0 else segl[::-1]
                                    rest[ci + 1:ci + 1] = sl
                                else:
                                    sl = segl if e == s1 else segl[::-1]
                                    rest[ci:ci] = sl
                                t[:] = rest
                                for k, cc in enumerate(t):
                                    pos[cc] = k
                                return (p, q, s0, s1, c, d)
        return None

    def local(queue, inq):
        while queue:
            if time.perf_counter() > t_hard:
                return
            a = queue.popleft(); inq[a] = False
            r = try2opt(a)
            if r is None:
                r = tryor(a)
            if r is not None:
                for x in r + (a,):
                    if not inq[x]:
                        inq[x] = True; queue.append(x)

    def length():
        return sum(D[t[k - 1]][t[k]] for k in range(n))

    local(deque(range(n)), [True] * n)
    cl = length(); best = t[:]; bl = cl
    W = min(n - 1, 50)
    it = 0
    stall = 0
    while time.perf_counter() < t_end:
        it += 1
        if it % 64 == 0:
            r = rnd.randrange(n)
            t[:] = t[r:] + t[:r]
            for k, cc in enumerate(t):
                pos[cc] = k
        saved = t[:]; savedp = pos[:]
        if rnd.random() < PG:
            a, b, c = sorted(rnd.sample(range(1, n), 3))
        else:
            r = rnd.randrange(n - W)
            a, b, c = sorted(rnd.sample(range(r + 1, r + W + 1), 3))
        ta1, ta, tb1, tb, tc1, tc = t[a - 1], t[a], t[b - 1], t[b], t[c - 1], t[c]
        kd = D[ta1][tb] + D[tc1][ta] + D[tb1][tc] - D[ta1][ta] - D[tb1][tb] - D[tc1][tc]
        t[a:c] = t[b:c] + t[a:b]
        for k in range(a, c):
            pos[t[k]] = k
        inq = [False] * n
        q = deque()
        for x in (ta1, ta, tb1, tb, tc1, tc):
            if not inq[x]:
                inq[x] = True; q.append(x)
        GAIN[0] = 0.0
        local(q, inq)
        nl = cl + kd - GAIN[0]
        if nl < cl + EPS:
            cl = nl
            if nl < bl - EPS:
                bl = nl; best = t[:]; stall = 0
        else:
            t[:] = saved; pos[:] = savedp
        stall += 1
        if stall > 400:
            stall = 0
            t[:] = best
            for _ in range(4):
                a, b, c = sorted(rnd.sample(range(1, n), 3))
                t[a:c] = t[b:c] + t[a:b]
            for k, cc in enumerate(t):
                pos[cc] = k
            local(deque(range(n)), [True] * n)
            cl = length()
    return best
