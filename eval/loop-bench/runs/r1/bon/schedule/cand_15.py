import heapq
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


def _simulate(jobs, keys, m, record=None):
    """Jobs taken in increasing key order; each goes to the machine that lets it start
    earliest, preferring the machine that has been idle for the shortest time."""
    seq = sorted(range(len(jobs)), key=lambda j: keys[j])
    free = [0] * m
    tot = 0
    for j in seq:
        r, p, d, w = jobs[j]
        bk, bf, ek, ef = -1, -1, 0, free[0]
        for k in range(m):
            f = free[k]
            if f <= r and f > bf:
                bf, bk = f, k
            if f < ef:
                ef, ek = f, k
        if bk >= 0:
            s, k = r, bk
        else:
            s, k = ef, ek
        free[k] = s + p
        if s + p > d:
            tot += w * (s + p - d)
        if record is not None:
            record.append((j, k, s))
    return tot


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0:
        return base

    rng = random.Random(15)
    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    wbar = (sum(jb[3] for jb in jobs) / n) or 1.0

    best_keys, best_val = None, None
    for lam in (0.0, 0.25, 0.5, 1.0, 2.0):
        ks = [jobs[j][2] - lam * pbar * (jobs[j][3] / wbar) for j in range(n)]
        v = _simulate(jobs, ks, m)
        if best_val is None or v < best_val:
            best_keys, best_val = ks, v
    starts = {}
    for j, _k, s in base:
        starts[j] = s
    ks = [float(starts[j]) for j in range(n)]
    v = _simulate(jobs, ks, m)
    if v < best_val:
        best_keys, best_val = ks, v

    sigma = 0.5
    trials, wins = 0, 0
    while time.perf_counter() - t0 < 0.75 and best_val > 0:
        cand = best_keys[:]
        for _ in range(rng.choice((1, 1, 2, 3, 5))):
            j = rng.randrange(n)
            cand[j] += rng.gauss(0.0, sigma * pbar)
        v = _simulate(jobs, cand, m)
        trials += 1
        if v <= best_val:
            if v < best_val:
                wins += 1
            best_keys, best_val = cand, v
        if trials == 25:
            rate = wins / 25.0
            if rate > 0.2:
                sigma = min(sigma * 1.3, 20.0)
            else:
                sigma = max(sigma / 1.3, 0.05)
            trials, wins = 0, 0

    out = []
    _simulate(jobs, best_keys, m, out)
    if _cost(jobs, out) < base_c:
        return out
    return base
