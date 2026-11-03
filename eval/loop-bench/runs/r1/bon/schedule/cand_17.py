"""Pilot method (Duin & Voss): build the job sequence one position at a time; each
candidate for the next position is judged by completing the sequence greedily in
earliest-due-date order and taking the full schedule's cost."""
import heapq
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


def _step(jobs, free, j):
    """Place job j on `free` (mutated); return (machine, start, lateness cost)."""
    r, p, d, w = jobs[j]
    k = 0
    fk = free[0]
    for q in range(1, len(free)):
        if free[q] < fk:
            fk = free[q]
            k = q
    s = fk if fk > r else r
    free[k] = s + p
    return k, s, (w * (s + p - d) if s + p > d else 0)


def _rollout(jobs, free, rem, skip):
    f = free[:]
    c = 0
    for j in rem:
        if j != skip:
            c += _step(jobs, f, j)[2]
    return c


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0:
        return base

    rem = sorted(range(n), key=lambda j: (jobs[j][2], jobs[j][0], j))
    free = [0] * m
    cost = 0
    out = []
    while rem:
        if time.perf_counter() - t0 < 0.66 and len(rem) > 1:
            cands = rem[:3]
            look = rem[:8]
            heavy = max(look, key=lambda j: (jobs[j][3] / (jobs[j][1] + 0.5), -j))
            if heavy not in cands:
                cands.append(heavy)
            soon = min(look, key=lambda j: (jobs[j][0], jobs[j][2], j))
            if soon not in cands:
                cands.append(soon)
            pick, pval = None, None
            for j in cands:
                f = free[:]
                c = _step(jobs, f, j)[2]
                v = c + _rollout(jobs, f, rem, j)
                if pval is None or v < pval:
                    pick, pval = j, v
        else:
            pick = rem[0]
        k, s, c = _step(jobs, free, pick)
        cost += c
        out.append((pick, k, s))
        rem.remove(pick)

    if cost < base_c and _cost(jobs, out) < base_c:
        return out
    return base
