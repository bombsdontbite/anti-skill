import heapq
import math
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


def _dispatch(jobs, m, prio):
    """Non-delay list scheduling: the earliest free machine takes the ready job with the
    highest priority prio(j, t)."""
    n = len(jobs)
    order = sorted(range(n), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i = [], [], 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i])
            i += 1
        bi, bv = 0, None
        for idx in range(len(ready)):
            v = prio(ready[idx], t)
            if bv is None or v > bv:
                bv, bi = v, idx
        j = ready[bi]
        ready[bi] = ready[-1]
        ready.pop()
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    best = _edf(jobs, m)
    best_c = _cost(jobs, best)
    if best_c == 0:
        return best

    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    logwp = []
    for r, p, d, w in jobs:
        logwp.append(math.log(max(w, 1e-6) / (p if p > 0 else 0.5)))

    rules = []

    def make_atc(scale):
        def atc(j, t):
            r, p, d, w = jobs[j]
            s = d - p - t
            if s < 0:
                s = 0
            return (logwp[j] - s / scale, -d, -j)
        return atc

    for kk in (0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        rules.append(make_atc(kk * pbar))

    def wmdd(j, t):
        r, p, d, w = jobs[j]
        mdd = d - t
        if mdd < p:
            mdd = p
        return (-mdd / max(w, 1e-6), -d, -j)

    rules.append(wmdd)

    def make_covert(kk):
        def covert(j, t):
            r, p, d, w = jobs[j]
            pp = p if p > 0 else 0.5
            s = d - p - t
            if s < 0:
                s = 0
            f = 1.0 - s / (kk * pp)
            if f < 0:
                f = 0.0
            return (max(w, 1e-6) / pp * f, -d, -j)
        return covert

    for kk in (1.0, 2.0, 4.0):
        rules.append(make_covert(kk))

    def wslack(j, t):
        r, p, d, w = jobs[j]
        s = d - p - t
        if s <= 0:
            return (1, logwp[j], -d, -j)
        return (0, -s / max(w, 1e-6), -d, -j)

    rules.append(wslack)

    for rule in rules:
        if time.perf_counter() - t0 > 0.6:
            break
        cand = _dispatch(jobs, m, rule)
        c = _cost(jobs, cand)
        if c < best_c:
            best, best_c = cand, c
    return best
