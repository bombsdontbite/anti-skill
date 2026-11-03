import heapq
import math
import time

LIMIT = 0.75


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


def _atc(jobs, m, scale, logwp):
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
        bi, bv = 0, -1e300
        for idx in range(len(ready)):
            j = ready[idx]
            s = jobs[j][2] - jobs[j][1] - t
            v = logwp[j] - (s / scale if s > 0 else 0.0)
            if v > bv:
                bv, bi = v, idx
        j = ready[bi]
        ready[bi] = ready[-1]
        ready.pop()
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def _decode(jobs, order, m, want=False):
    """Serial decoder: each job goes, in list order, to the machine where it can start
    soonest; among machines already idle at its release, the one idle the shortest."""
    free = [0] * m
    cost = 0
    out = [] if want else None
    for j in order:
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
        late = s + p - d
        if late > 0:
            cost += w * late
        if want:
            out.append((j, k, s))
    return cost, out


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
    logwp = [math.log(max(w, 1e-6) / (p if p > 0 else 0.5)) for r, p, d, w in jobs]

    seeds = []
    seeds.append(sorted(range(n), key=lambda j: (jobs[j][2], jobs[j][0])))
    seeds.append([j for j, _k, _s in sorted(best, key=lambda x: (x[2], x[0]))])
    for kk in (0.5, 1.0, 2.0, 3.0):
        if time.perf_counter() - t0 > 0.3:
            break
        sch = _atc(jobs, m, kk * pbar, logwp)
        c = _cost(jobs, sch)
        if c < best_c:
            best, best_c = sch, c
        seeds.append([j for j, _k, _s in sorted(sch, key=lambda x: (x[2], x[0]))])

    cur, cc = None, None
    for o in seeds:
        c, _ = _decode(jobs, o, m)
        if cc is None or c < cc:
            cur, cc = o[:], c

    improved = True
    while improved and time.perf_counter() - t0 < LIMIT:
        improved = False
        for i in range(n - 1):
            if time.perf_counter() - t0 > LIMIT:
                break
            cur[i], cur[i + 1] = cur[i + 1], cur[i]
            c, _ = _decode(jobs, cur, m)
            if c < cc:
                cc = c
                improved = True
            else:
                cur[i], cur[i + 1] = cur[i + 1], cur[i]

    c, sch = _decode(jobs, cur, m, True)
    if c < best_c:
        return sch
    return best
