import heapq
import math
import random
import time


def _edf(jobs, m):
    order = sorted(range(len(jobs)), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i = [], [], 0
    while len(out) < len(jobs):
        t, k = heapq.heappop(free)
        if not ready and i < len(order) and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < len(order) and jobs[order[i]][0] <= t:
            j = order[i]
            heapq.heappush(ready, (jobs[j][2], j))
            i += 1
        _, j = heapq.heappop(ready)
        t = max(t, jobs[j][0])
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def _cost(jobs, sched):
    c = 0
    for j, _k, s in sched:
        late = s + jobs[j][1] - jobs[j][2]
        if late > 0:
            c += jobs[j][3] * late
    return c


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(1818)
    R = [jb[0] for jb in jobs]
    P = [jb[1] for jb in jobs]
    D = [jb[2] for jb in jobs]
    W = [jb[3] for jb in jobs]

    def tail(seq, lo, free0, c0, limit):
        free = free0[:]
        c = c0
        for idx in range(lo, n):
            j = seq[idx]
            k = 0
            fk = free[0]
            for q in range(1, m):
                if free[q] < fk:
                    fk = free[q]
                    k = q
            s = fk if fk > R[j] else R[j]
            e = s + P[j]
            free[k] = e
            if e > D[j]:
                c += W[j] * (e - D[j])
                if c > limit:
                    return None
        return c

    def states(seq, lo, frees, costs):
        free = frees[lo][:]
        c = costs[lo]
        for idx in range(lo, n):
            j = seq[idx]
            k = 0
            for q in range(1, m):
                if free[q] < free[k]:
                    k = q
            s = free[k] if free[k] > R[j] else R[j]
            e = s + P[j]
            free[k] = e
            if e > D[j]:
                c += W[j] * (e - D[j])
            frees[idx + 1] = free[:]
            costs[idx + 1] = c

    seeds = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (D[j], j)),
        sorted(range(n), key=lambda j: (D[j] - P[j], j)),
    ]
    zero = [0] * m
    cur, cc = None, None
    for s in seeds:
        c = tail(s, 0, zero, 0, float("inf"))
        if cc is None or c < cc:
            cur, cc = s[:], c
    frees = [None] * (n + 1)
    costs = [0] * (n + 1)
    frees[0] = zero[:]
    states(cur, 0, frees, costs)
    best, bc = cur[:], cc

    t_hi = max(1.0, 0.02 * cc)
    t_lo = max(1e-3, t_hi * 1e-4)
    budget = 0.76
    while True:
        el = time.perf_counter() - t0
        if el > budget or bc == 0:
            break
        temp = t_hi * (t_lo / t_hi) ** (el / budget)
        i = rng.randrange(n)
        j = min(n - 1, max(0, i + rng.randint(-30, 30)))
        if i == j:
            continue
        lo, hi = (i, j) if i < j else (j, i)
        o = cur[:]
        u = rng.random()
        if u < 0.35:
            o[i], o[j] = o[j], o[i]
        elif u < 0.8:
            o.insert(j, o.pop(i))
        else:
            o[lo:hi + 1] = o[lo:hi + 1][::-1]
        limit = cc - temp * math.log(1.0 - rng.random())
        c = tail(o, lo, frees[lo], costs[lo], limit)
        if c is None:
            continue
        cur, cc = o, c
        states(cur, lo, frees, costs)
        if cc < bc:
            best, bc = cur[:], cc

    free = [0] * m
    out = []
    for j in best:
        k = 0
        for q in range(1, m):
            if free[q] < free[k]:
                k = q
        s = free[k] if free[k] > R[j] else R[j]
        free[k] = s + P[j]
        out.append((j, k, s))
    if _cost(jobs, out) < base_c:
        return out
    return base
