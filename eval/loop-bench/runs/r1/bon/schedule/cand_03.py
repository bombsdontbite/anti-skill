import heapq
import math
import random
import time

BUDGET = 0.78


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


def _score(jobs, perm, m):
    free = [0] * m
    cost = 0
    for j in perm:
        r, p, d, w = jobs[j]
        k = 0
        f = free[0]
        for q in range(1, m):
            if free[q] < f:
                f = free[q]
                k = q
        s = f if f > r else r
        free[k] = s + p
        if s + p > d:
            cost += w * (s + p - d)
    return cost


def _build(jobs, perm, m):
    free = [0] * m
    out = []
    for j in perm:
        r, p = jobs[j][0], jobs[j][1]
        k = min(range(m), key=lambda q: (free[q], q))
        s = max(free[k], r)
        free[k] = s + p
        out.append((j, k, s))
    return out


def schedule(jobs, m):
    start = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 2:
        return base

    rng = random.Random(20261027)
    seeds = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (jobs[j][2], j)),
        sorted(range(n), key=lambda j: (jobs[j][2] - jobs[j][1], j)),
        sorted(range(n), key=lambda j: (max(jobs[j][0] + jobs[j][1], jobs[j][2]), j)),
    ]
    cur, cc = None, None
    for s in seeds:
        c = _score(jobs, s, m)
        if cc is None or c < cc:
            cur, cc = s, c
    best, bc = cur[:], cc

    def neighbour(perm):
        o = perm[:]
        i = rng.randrange(n)
        span = min(n - 1, 25)
        j = i + rng.randint(-span, span)
        if j < 0:
            j = 0
        elif j >= n:
            j = n - 1
        if i == j:
            j = (i + 1) % n
        if rng.random() < 0.5:
            o[i], o[j] = o[j], o[i]
        else:
            x = o.pop(i)
            o.insert(j, x)
        return o

    ups = []
    for _ in range(40):
        c = _score(jobs, neighbour(cur), m)
        if c > cc:
            ups.append(c - cc)
    t_hi = (sum(ups) / len(ups)) * 0.5 if ups else max(1.0, cc / n)
    t_lo = t_hi * 1e-3

    while True:
        el = time.perf_counter() - start
        if el > BUDGET:
            break
        frac = el / BUDGET
        temp = t_hi * (t_lo / t_hi) ** frac
        o = neighbour(cur)
        c = _score(jobs, o, m)
        dlt = c - cc
        if dlt <= 0 or rng.random() < math.exp(-dlt / temp):
            cur, cc = o, c
            if c < bc:
                best, bc = o[:], c
                if bc == 0:
                    break

    sch = _build(jobs, best, m)
    if _cost(jobs, sch) < base_c:
        return sch
    return base
