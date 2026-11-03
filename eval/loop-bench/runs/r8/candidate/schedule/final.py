import bisect, heapq, math, random, time

TIME_LIMIT = 0.8
SEED = 1
T_FRAC = 0.05
W = 8


def _dispatch(jobs, m, key):
    """List scheduling: when a machine frees, start the ready job minimising key(j, t)."""
    order = sorted(range(len(jobs)), key=lambda j: jobs[j][0])
    free = [0] * m
    ready, seq, i = [], [], 0
    n = len(jobs)
    while len(seq) < n:
        t = min(free); k = free.index(t)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        j = min(ready, key=lambda j: key(j, t))
        ready.remove(j)
        seq.append(j)
        free[k] = t + jobs[j][1]
    return seq


def _snaps(jobs, m, seq):
    """Machine free times (a heap of plain ints) and cost before each position, plus the end."""
    free = [0] * m
    c = 0
    F, Cs = [], []
    for j in seq:
        F.append(free[:]); Cs.append(c)
        r, p, d, w = jobs[j]
        q = bisect.bisect_right(free, r) - 1
        if q < 0:
            q = 0; e = free[0] + p
        else:
            e = r + p
        del free[q]
        if e > d:
            c += w * (e - d)
        bisect.insort(free, e)
    F.append(free); Cs.append(c)
    return F, Cs


def _eval(jobs, seq, lo, hi, F, Cs, cap):
    """Cost of seq, which equals the snapshotted sequence outside lo..hi; None if above cap."""
    free = F[lo][:]
    c = Cs[lo]
    n = len(seq)
    for idx in range(lo, n):
        if idx > hi and free == F[idx]:
            c += Cs[n] - Cs[idx]
            return c if c <= cap else None
        r, p, d, w = jobs[seq[idx]]
        q = bisect.bisect_right(free, r) - 1
        if q < 0:
            q = 0; e = free[0] + p
        else:
            e = r + p
        del free[q]
        if e > d:
            c += w * (e - d)
            if c > cap: return None
        bisect.insort(free, e)
    return c


def _decode(jobs, m, seq):
    return _snaps(jobs, m, seq)[1][-1]


def _assign(jobs, m, seq):
    free = [(0, k) for k in range(m)]
    out = []
    for j in seq:
        r = jobs[j][0]
        q = bisect.bisect_right(free, (r, m)) - 1
        if q < 0: q = 0
        t, k = free.pop(q)
        s = max(t, r)
        out.append((j, k, s))
        bisect.insort(free, (s + jobs[j][1], k))
    return out


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    if n == 0: return []
    pbar = sum(j[1] for j in jobs) / n
    cands = [_dispatch(jobs, m, lambda j, t: (jobs[j][2], j))]
    for K in (0.5, 1, 2, 4):
        def atc(j, t, K=K):
            r, p, d, w = jobs[j]
            return -w / p * math.exp(-max(0, d - p - t) / (K * pbar))
        cands.append(_dispatch(jobs, m, atc))
    cur = min(cands, key=lambda s: _decode(jobs, m, s))
    F, Cs = _snaps(jobs, m, cur)
    cc = bc = Cs[-1]; best = cur[:]
    rnd = random.Random(SEED)
    T0 = max(1.0, bc / n * T_FRAC); T = T0
    it = 0
    while bc > 0:
        it += 1
        if it & 63 == 0:
            el = (time.time() - t0) / TIME_LIMIT
            if el > 1: break
            T = T0 * (1 - el) ** 2 + 1e-9
        a = rnd.randrange(n)
        b = min(n - 1, max(0, a + rnd.randint(-W, W)))
        if a == b: continue
        lo, hi = (a, b) if a < b else (b, a)
        swap = rnd.random() < 0.5
        if swap:
            cur[a], cur[b] = cur[b], cur[a]
        else:
            cur.insert(b, cur.pop(a))
        cap = cc - T * math.log(rnd.random() + 1e-300)
        c = _eval(jobs, cur, lo, hi, F, Cs, cap)
        if c is not None:
            cc = c
            free = F[lo][:]; cs = Cs[lo]
            for idx in range(lo, n):
                if idx > hi and free == F[idx]:
                    dlt = cs - Cs[idx]
                    if dlt:
                        for q in range(idx, n + 1): Cs[q] += dlt
                    break
                F[idx] = free[:]; Cs[idx] = cs
                r, p, d, w = jobs[cur[idx]]
                q = bisect.bisect_right(free, r) - 1
                if q < 0:
                    q = 0; e = free[0] + p
                else:
                    e = r + p
                del free[q]
                if e > d:
                    cs += w * (e - d)
                bisect.insort(free, e)
            else:
                F[n] = free; Cs[n] = cs
            if c < bc: bc, best = c, cur[:]
        elif swap:
            cur[a], cur[b] = cur[b], cur[a]
        else:
            cur.insert(a, cur.pop(b))
    return _assign(jobs, m, best)
