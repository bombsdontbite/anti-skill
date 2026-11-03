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


def _place(jobs, free, j):
    k = 0
    for q in range(1, len(free)):
        if free[q] < free[k]:
            k = q
    s = free[k] if free[k] > jobs[j][0] else jobs[j][0]
    return k, s


def _lookahead(jobs, free, rem, skip, horizon):
    """Cost of greedily placing the next `horizon` remaining jobs in EDD order."""
    f = free[:]
    c = 0
    taken = 0
    for j in rem:
        if j == skip:
            continue
        k, s = _place(jobs, f, j)
        e = s + jobs[j][1]
        f[k] = e
        if e > jobs[j][2]:
            c += jobs[j][3] * (e - jobs[j][2])
        taken += 1
        if taken >= horizon:
            break
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

    edd = sorted(range(n), key=lambda j: (jobs[j][2], jobs[j][0], j))
    width, branch, horizon = 4, 4, 15
    # state: (estimate, cost, free, remaining, trail)
    beam = [(0, 0, [0] * m, edd, None)]
    for _step in range(n):
        if time.perf_counter() - t0 > 0.62:
            width, branch, horizon = 1, 1, 0
        children = []
        for _est, cost, free, rem, trail in beam:
            cands = list(rem[:branch])
            if branch > 1:
                window = rem[:10]
                heavy = max(window, key=lambda j: (jobs[j][3] / (jobs[j][1] + 1.0), -j))
                if heavy not in cands:
                    cands.append(heavy)
                early = min(window, key=lambda j: (jobs[j][0], jobs[j][2]))
                if early not in cands:
                    cands.append(early)
            for j in cands:
                k, s = _place(jobs, free, j)
                e = s + jobs[j][1]
                c = cost + (jobs[j][3] * (e - jobs[j][2]) if e > jobs[j][2] else 0)
                nf = free[:]
                nf[k] = e
                est = c + (_lookahead(jobs, nf, rem, j, horizon) if horizon else 0)
                children.append((est, c, nf, j, rem, (j, k, s, trail)))
        children.sort(key=lambda x: (x[0], x[1]))
        beam = []
        seen = set()
        for est, c, nf, j, rem, trail in children:
            sig = (c, tuple(sorted(nf)))
            if sig in seen:
                continue
            seen.add(sig)
            idx = rem.index(j)
            beam.append((est, c, nf, rem[:idx] + rem[idx + 1:], trail))
            if len(beam) >= width:
                break

    best = min(beam, key=lambda x: x[1])
    out = []
    node = best[4]
    while node is not None:
        j, k, s, node = node
        out.append((j, k, s))
    out.reverse()
    if len(out) == n and _cost(jobs, out) < base_c:
        return out
    return base
