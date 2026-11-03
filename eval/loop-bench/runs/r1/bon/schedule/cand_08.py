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


def _decode(jobs, seq, m, out=None):
    free = [(0, k) for k in range(m)]
    cost = 0
    for j in seq:
        r, p, d, w = jobs[j]
        f, k = heapq.heappop(free)
        s = f if f > r else r
        e = s + p
        heapq.heappush(free, (e, k))
        if e > d:
            cost += w * (e - d)
        if out is not None:
            out.append((j, k, s))
    return cost


def _apply(seq, move):
    kind, i, j = move
    o = seq[:]
    if kind == 0:
        o[i], o[j] = o[j], o[i]
    else:
        o.insert(j, o.pop(i))
    return o


def schedule(jobs, m):
    clock = time.perf_counter
    t0 = clock()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(31337)
    cur = [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]
    cc = _decode(jobs, cur, m)
    alt = sorted(range(n), key=lambda j: (jobs[j][2], jobs[j][0]))
    ac = _decode(jobs, alt, m)
    if ac < cc:
        cur, cc = alt, ac
    best, bc = cur[:], cc

    tabu = {}
    tenure = 12
    it = 0
    sample = 18
    reach = min(n - 1, 12)
    while clock() - t0 < 0.74 and bc > 0:
        it += 1
        mv_best, mv_c, mv_jobs = None, None, None
        for _ in range(sample):
            i = rng.randrange(n)
            j = i + rng.randint(1, reach) * (1 if rng.random() < 0.5 else -1)
            if j < 0 or j >= n:
                continue
            kind = 0 if rng.random() < 0.5 else 1
            o = _apply(cur, (kind, i, j))
            c = _decode(jobs, o, m)
            moved = (cur[i], cur[j]) if kind == 0 else (cur[i],)
            forbidden = any(tabu.get(x, 0) > it for x in moved)
            if forbidden and c >= bc:
                continue
            if mv_c is None or c < mv_c:
                mv_best, mv_c, mv_jobs = o, c, moved
        if mv_best is None:
            continue
        cur, cc = mv_best, mv_c
        for x in mv_jobs:
            tabu[x] = it + tenure + rng.randint(0, 4)
        if cc < bc:
            best, bc = cur[:], cc

    out = []
    _decode(jobs, best, m, out)
    if _cost(jobs, out) < base_c:
        return out
    return base
