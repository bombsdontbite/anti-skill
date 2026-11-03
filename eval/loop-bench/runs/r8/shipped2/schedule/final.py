import heapq, math, random, time

BUDGET = 0.85
SPAN = 12
PT = 0.5
KS = (0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1, 1.5, 2, 3, 5, 8)



def _dispatch(jobs, m, K, pbar):
    """ATC list scheduling."""
    n = len(jobs)
    free = [0] * m
    order = sorted(range(n), key=lambda j: jobs[j][0])
    done = [False] * n
    pending, i, out, cost = [], 0, [], 0
    kp = K * pbar
    while len(out) < n:
        t = min(free); k = free.index(t)
        while i < n and done[order[i]]:
            i += 1
        if not pending and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            if not done[order[i]]:
                pending.append(order[i])
            i += 1
        cand = pending
        bj, bv = -1, -1.0
        for j in cand:
            r, p, d, w = jobs[j]
            s = r if r > t else t
            v = w / p * math.exp(-max(0, d - p - s) / kp)
            if v > bv:
                bv, bj = v, j
        j = bj
        r, p, d, w = jobs[j]
        if j in pending:
            pending.remove(j)
        done[j] = True
        s = max(t, r)
        out.append((j, k, s))
        free[k] = s + p
        cost += w * max(0, s + p - d)
    return cost, out
def _rebuild(R, P, D, W, seq, lo, states, lat, suf):
    free = list(states[lo])
    n = len(seq)
    for pos in range(lo, n):
        states[pos] = tuple(free)
        j = seq[pos]
        f = heapq.heappop(free)
        r = R[j]
        e = (f if f > r else r) + P[j]
        heapq.heappush(free, e)
        lat[pos] = W[j] * (e - D[j]) if e > D[j] else 0
    acc = 0
    for pos in range(n - 1, -1, -1):
        acc += lat[pos]
        suf[pos] = acc


def _suffix(R, P, D, W, seq, lo, start, cap, hr=heapq.heapreplace):
    """Lateness of seq[lo:] from machine state start; gives up (returns cap + 1) once over cap."""
    free = list(start)
    c = 0
    for j in seq[lo:]:
        r = R[j]
        f = free[0]
        e = (f if f > r else r) + P[j]
        hr(free, e)
        e -= D[j]
        if e > 0:
            c += W[j] * e
            if c > cap:
                return cap + 1
    return c


def _decode(jobs, m, seq):
    free = [0] * m; out = []
    for j in seq:
        r, p, d, w = jobs[j]
        f = min(free); k = free.index(f)
        s = max(f, r); free[k] = s + p
        out.append((j, k, s))
    return out


def _ls(jobs, m, seq, deadline, rnd):
    n = len(seq)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    states = [None] * (n + 1)
    states[0] = tuple([0] * m)
    lat = [0] * n
    suf = [0] * (n + 1)
    _rebuild(R, P, D, W, seq, 0, states, lat, suf)
    it = 0
    while suf[0] > 0:
        it += 1
        if it & 63 == 0 and time.time() > deadline:
            break
        a = rnd.randrange(n)
        if rnd.random() < PT:
            for _ in range(6):
                if lat[a] > 0:
                    break
                a = rnd.randrange(n)
            b = max(0, a - rnd.randint(1, SPAN))
        else:
            b = min(n - 1, max(0, a + rnd.randint(-SPAN, SPAN)))
        if a == b:
            continue
        lo = a if a < b else b
        j = seq.pop(a); seq.insert(b, j)
        if _suffix(R, P, D, W, seq, lo, states[lo], suf[lo]) <= suf[lo]:
            _rebuild(R, P, D, W, seq, lo, states, lat, suf)
        else:
            j = seq.pop(b); seq.insert(a, j)
    return suf[0], seq


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / n
    starts = sorted(_dispatch(jobs, m, K, pbar) for K in KS)
    best = starts[0]
    seq = [j for j, _, _ in sorted(best[1], key=lambda x: (x[2], x[1]))]
    c, s = _ls(jobs, m, seq, t0 + BUDGET, random.Random(1))
    return _decode(jobs, m, s) if c < best[0] else best[1]
