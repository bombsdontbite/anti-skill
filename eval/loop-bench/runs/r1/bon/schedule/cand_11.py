import heapq
import time

_DEADLINE = 0.74


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


def _value(jobs, seq, m):
    free = [0] * m
    c = 0
    for j in seq:
        r, p, d, w = jobs[j]
        k = 0
        for q in range(1, m):
            if free[q] < free[k]:
                k = q
        s = free[k] if free[k] > r else r
        free[k] = s + p
        if s + p > d:
            c += w * (s + p - d)
    return c


def _realise(jobs, seq, m):
    free = [0] * m
    out = []
    for j in seq:
        k = 0
        for q in range(1, m):
            if free[q] < free[k]:
                k = q
        s = max(free[k], jobs[j][0])
        free[k] = s + jobs[j][1]
        out.append((j, k, s))
    return out


def _descend(jobs, seq, m, c, t0):
    """First-improvement descent: interchanges at distance 1..3, then single-job moves
    up to 6 places earlier or later; repeat until a full sweep changes nothing."""
    n = len(seq)
    changed = True
    while changed:
        changed = False
        for g in (1, 2, 3):
            for i in range(n - g):
                if time.perf_counter() - t0 > _DEADLINE:
                    return seq, c
                seq[i], seq[i + g] = seq[i + g], seq[i]
                v = _value(jobs, seq, m)
                if v < c:
                    c = v
                    changed = True
                else:
                    seq[i], seq[i + g] = seq[i + g], seq[i]
        for i in range(n):
            for off in (-6, -4, -2, 2, 4, 6):
                q = i + off
                if q < 0 or q >= n:
                    continue
                if time.perf_counter() - t0 > _DEADLINE:
                    return seq, c
                x = seq.pop(i)
                seq.insert(q, x)
                v = _value(jobs, seq, m)
                if v < c:
                    c = v
                    changed = True
                    break
                seq.pop(q)
                seq.insert(i, x)
    return seq, c


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 2:
        return base

    starts = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (jobs[j][2], j)),
        sorted(range(n), key=lambda j: (jobs[j][2] - jobs[j][1], -jobs[j][3])),
    ]
    scored = sorted(((_value(jobs, s, m), s) for s in starts), key=lambda x: x[0])
    best_seq, best_val = scored[0][1], scored[0][0]
    for v, s in scored:
        if time.perf_counter() - t0 > _DEADLINE or best_val == 0:
            break
        s, v = _descend(jobs, s[:], m, v, t0)
        if v < best_val:
            best_seq, best_val = s, v

    sch = _realise(jobs, best_seq, m)
    if _cost(jobs, sch) < base_c:
        return sch
    return base
