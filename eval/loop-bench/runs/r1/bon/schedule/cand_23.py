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


def schedule(jobs, m):
    t0 = time.perf_counter()
    stop = 0.75
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    R = [jb[0] for jb in jobs]
    P = [jb[1] for jb in jobs]
    D = [jb[2] for jb in jobs]
    W = [jb[3] for jb in jobs]
    rng = random.Random(23)

    def run(seq, lo, free0, c0, cap, frees=None, costs=None):
        """Decode seq[lo:] from a saved prefix state; None once the cost reaches cap.
        With frees/costs given, also refreshes the saved prefix states."""
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
                if c >= cap:
                    return None
            if frees is not None:
                frees[idx + 1] = free[:]
                costs[idx + 1] = c
        return c

    inf = float("inf")
    zero = [0] * m
    seeds = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (D[j], j)),
        sorted(range(n), key=lambda j: (D[j] - P[j], j)),
    ]
    cur, cc = None, inf
    for s in seeds:
        c = run(s, 0, zero, 0, inf)
        if c < cc:
            cur, cc = s[:], c
    frees = [None] * (n + 1)
    costs = [0] * (n + 1)
    frees[0] = zero[:]
    run(cur, 0, zero, 0, inf, frees, costs)
    best, bc = cur[:], cc

    def descend():
        nonlocal cur, cc
        improved = True
        while improved and cc > 0:
            improved = False
            for i in range(n):
                for blk in (1, 2, 3):
                    if i + blk > n:
                        break
                    for shift in (-1, -2, -3, -5, -8, 1, 2, 3, 5, 8):
                        if time.perf_counter() - t0 > stop:
                            return
                        rest = cur[:i] + cur[i + blk:]
                        q = i + shift
                        if q < 0 or q > len(rest):
                            continue
                        o = rest[:q] + cur[i:i + blk] + rest[q:]
                        lo = i if i < q else q
                        c = run(o, lo, frees[lo], costs[lo], cc)
                        if c is not None and c < cc:
                            cur, cc = o, c
                            run(cur, lo, frees[lo], costs[lo], inf, frees, costs)
                            improved = True

    descend()
    if cc < bc:
        best, bc = cur[:], cc
    while time.perf_counter() - t0 < stop and bc > 0:
        cur = best[:]
        for _ in range(rng.randint(2, 5)):
            i = rng.randrange(n)
            q = min(n - 1, max(0, i + rng.randint(-15, 15)))
            cur[i], cur[q] = cur[q], cur[i]
        cc = run(cur, 0, zero, 0, inf, frees, costs)
        descend()
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
