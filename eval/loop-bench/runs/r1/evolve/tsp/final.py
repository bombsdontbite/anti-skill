import math
import random
import time
from collections import deque

EPS = 1e-10


def _dmat(pts):
    return [[math.dist(p, q) for q in pts] for p in pts]


def _neigh(D, n, k):
    out = []
    for i in range(n):
        Di = D[i]
        out.append(sorted((j for j in range(n) if j != i), key=lambda j: Di[j])[:k])
    return out


def _tlen(t, D):
    n = len(t)
    return sum(D[t[i - 1]][t[i]] for i in range(n))


def _rev(t, pos, i, j, n):
    L = (j - i) % n + 1
    if 2 * L > n:
        i, j = (j + 1) % n, (i - 1) % n
        L = n - L
    for _ in range(L // 2):
        a = t[i]
        b = t[j]
        t[i] = b
        pos[b] = i
        t[j] = a
        pos[a] = j
        i += 1
        if i == n:
            i = 0
        j -= 1
        if j < 0:
            j = n - 1


def _try2opt(a, t, pos, D, nb, n):
    i = pos[a]
    an = t[(i + 1) % n]
    ap = t[i - 1]
    Da = D[a]
    dan = Da[an]
    dap = Da[ap]
    for c in nb[a]:
        dac = Da[c]
        g1 = dan - dac
        g2 = dap - dac
        if g1 <= 0 and g2 <= 0:
            break
        j = pos[c]
        if g1 > 0:
            cn = t[(j + 1) % n]
            if c != an and cn != a:
                gg = g1 + D[c][cn] - D[an][cn]
                if gg > EPS:
                    _rev(t, pos, pos[an], j, n)
                    return (a, an, c, cn), gg
        if g2 > 0:
            cp = t[j - 1]
            if c != ap and cp != a:
                gg = g2 + D[c][cp] - D[ap][cp]
                if gg > EPS:
                    _rev(t, pos, i, pos[cp], n)
                    return (a, ap, c, cp), gg
    return None


def _tryor(a, t, pos, D, nb, n, maxL=3):
    i = pos[a]
    for L in range(1, maxL + 1):
        if L >= n - 3:
            break
        e = (i + L - 1) % n
        s1 = a
        s2 = t[e]
        p = t[i - 1]
        nx = t[(e + 1) % n]
        seg = [t[(i + k) % n] for k in range(L)]
        segs = set(seg)
        rem = D[p][s1] + D[s2][nx] - D[p][nx]
        if rem <= EPS:
            continue
        for s in (s1, s2) if L > 1 else (s1,):
            Ds = D[s]
            for c in nb[s]:
                if Ds[c] >= rem:
                    break
                if c in segs:
                    continue
                jc = pos[c]
                for u, v in ((c, t[(jc + 1) % n]), (t[jc - 1], c)):
                    if u in segs or v in segs:
                        continue
                    duv = D[u][v]
                    a1 = D[u][s1] + D[s2][v] - duv
                    a2 = D[u][s2] + D[s1][v] - duv
                    if a1 <= a2:
                        add, fwd = a1, True
                    else:
                        add, fwd = a2, False
                    if add < rem - EPS:
                        st = pos[nx]
                        r = [t[(st + k) % n] for k in range(n - L)]
                        idx = r.index(u)
                        ins = seg if fwd else seg[::-1]
                        nt = r[: idx + 1] + ins + r[idx + 1:]
                        t[:] = nt
                        for k in range(n):
                            pos[nt[k]] = k
                        return (p, nx, s1, s2, u, v), rem - add
    return None


def _ls(t, pos, D, nb, active, deadline, use_or=True):
    n = len(t)
    inq = [False] * n
    q = deque()
    for a in active:
        if not inq[a]:
            inq[a] = True
            q.append(a)
    cnt = 0
    gain = 0.0
    while q:
        cnt += 1
        if (cnt & 31) == 0 and time.perf_counter() > deadline:
            return False, gain
        a = q.popleft()
        inq[a] = False
        r = _try2opt(a, t, pos, D, nb, n)
        if r is None and use_or:
            r = _tryor(a, t, pos, D, nb, n)
        if r is not None:
            gain += r[1]
            for x in r[0]:
                if not inq[x]:
                    inq[x] = True
                    q.append(x)
            if not inq[a]:
                inq[a] = True
                q.append(a)
    return True, gain


def _nn(D, n, start=0):
    left = set(range(n))
    left.remove(start)
    t = [start]
    while left:
        Dc = D[t[-1]]
        nxt = min(left, key=lambda j: Dc[j])
        left.remove(nxt)
        t.append(nxt)
    return t


def _posof(t):
    pos = [0] * len(t)
    for k, x in enumerate(t):
        pos[x] = k
    return pos


def _small(n):
    return list(range(n))


def solve(points):
    """cand_12 (ILS, 0.85 s) with cand_07's length bookkeeping by kick delta minus LS gain."""
    t0 = time.perf_counter()
    deadline = t0 + 0.85
    n = len(points)
    if n <= 7:
        return list(range(n))
    rng = random.Random(7)
    D = _dmat(points)
    nb = _neigh(D, n, 8)
    t = _nn(D, n, 0)
    pos = _posof(t)
    _ls(t, pos, D, nb, t, deadline)
    best = t[:]
    bestL = _tlen(t, D)
    W = min(n - 1, 50)
    while time.perf_counter() < deadline:
        i = rng.randrange(n)
        s = best[i:] + best[:i]
        p1, p2, p3 = sorted(rng.sample(range(1, W + 1), 3))
        a0, a1 = s[p1 - 1], s[p1]
        b0, b1 = s[p2 - 1], s[p2]
        c0, c1 = s[p3 - 1], s[p3 % n]
        kd = D[a0][b1] + D[c0][a1] + D[b0][c1] - D[a0][a1] - D[b0][b1] - D[c0][c1]
        t = s[:p1] + s[p2:p3] + s[p1:p2] + s[p3:]
        pos = _posof(t)
        ok, g = _ls(t, pos, D, nb, (s[0], a0, a1, b0, b1, c0, c1), deadline)
        if not ok:
            break
        if kd - g < -1e-9:
            L = _tlen(t, D)
            if L < bestL - EPS:
                bestL = L
                best = t
    return best
