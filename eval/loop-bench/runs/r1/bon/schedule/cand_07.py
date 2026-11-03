import bisect
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


def _slot(starts, ends, r, p):
    """Earliest start >= r of a length-p hole on one machine, and the index to insert at."""
    i = bisect.bisect_right(ends, r)
    s = r
    L = len(starts)
    while i < L:
        if s + p <= starts[i]:
            return s, i
        if ends[i] > s:
            s = ends[i]
        i += 1
    return s, L


def _place(jobs, prio, m, build=False):
    """Serial generation of an active schedule: jobs in priority order, each into the
    earliest hole on any machine that fits it (higher-priority jobs are never moved)."""
    starts = [[] for _ in range(m)]
    ends = [[] for _ in range(m)]
    cost = 0
    out = []
    for j in prio:
        r, p, d, w = jobs[j]
        bs, bi, bk = None, 0, 0
        for k in range(m):
            s, i = _slot(starts[k], ends[k], r, p)
            if bs is None or s < bs:
                bs, bi, bk = s, i, k
                if s == r:
                    break
        starts[bk].insert(bi, bs)
        ends[bk].insert(bi, bs + p)
        if bs + p > d:
            cost += w * (bs + p - d)
        if build:
            out.append((j, bk, bs))
    return cost, out


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 2:
        return base

    rng = random.Random(77)
    wbar = (sum(jb[3] for jb in jobs) / n) or 1.0
    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    keys = [
        lambda j: (jobs[j][2], j),
        lambda j: (jobs[j][2] - jobs[j][1], j),
        lambda j: (jobs[j][2] - pbar * jobs[j][3] / wbar, j),
        lambda j: (jobs[j][2] - 0.5 * pbar * jobs[j][3] / wbar, j),
        lambda j: (jobs[j][0] + jobs[j][1], jobs[j][2]),
        lambda j: (jobs[j][2] - jobs[j][1] * jobs[j][3] / wbar, j),
    ]
    cur, cc = None, None
    for key in keys:
        o = sorted(range(n), key=key)
        c, _ = _place(jobs, o, m)
        if cc is None or c < cc:
            cur, cc = o, c

    limit = 0.72
    stale = 0
    while time.perf_counter() - t0 < limit and cc > 0:
        o = cur[:]
        i = rng.randrange(n)
        j = min(n - 1, max(0, i + rng.randint(-10, 10)))
        if i == j:
            continue
        if rng.random() < 0.6:
            o[i], o[j] = o[j], o[i]
        else:
            o.insert(j, o.pop(i))
        c, _ = _place(jobs, o, m)
        if c < cc or (c == cc and stale > 30):
            cur, cc = o, c
            stale = 0
        else:
            stale += 1

    c, sch = _place(jobs, cur, m, True)
    if c < base_c:
        return sch
    return base
