"""Late acceptance hill climbing (Burke & Bykov) over a permutation decoded by list
scheduling."""
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


def _run(jobs, seq, m, keep):
    free = [0] * m
    total = 0
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
            total += w * (s + p - d)
        if keep is not None:
            keep.append((j, k, s))
    return total


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(555)
    a = [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]
    b = sorted(range(n), key=lambda j: (jobs[j][2], j))
    ca, cb = _run(jobs, a, m, None), _run(jobs, b, m, None)
    cur, cc = (a, ca) if ca <= cb else (b, cb)
    best, bc = cur[:], cc

    hist_len = 60
    hist = [cc] * hist_len
    v = 0
    while time.perf_counter() - t0 < 0.75 and bc > 0:
        o = cur[:]
        i = rng.randrange(n)
        reach = rng.choice((3, 8, 20))
        j = min(n - 1, max(0, i + rng.randint(-reach, reach)))
        if i == j:
            continue
        mv = rng.random()
        if mv < 0.4:
            o[i], o[j] = o[j], o[i]
        elif mv < 0.85:
            o.insert(j, o.pop(i))
        else:
            lo, hi = (i, j) if i < j else (j, i)
            o[lo:hi + 1] = o[lo:hi + 1][::-1]
        c = _run(jobs, o, m, None)
        if c <= cc or c <= hist[v]:
            cur, cc = o, c
            if c < bc:
                best, bc = o[:], c
        if cc < hist[v]:
            hist[v] = cc
        v = (v + 1) % hist_len

    out = []
    _run(jobs, best, m, out)
    if _cost(jobs, out) < base_c:
        return out
    return base
