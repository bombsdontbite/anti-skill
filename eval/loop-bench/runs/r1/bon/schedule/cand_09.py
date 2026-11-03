import heapq
import math
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


def _xatc(jobs, m, by_rel, logwp, pbar, kk, window, idle_pen):
    """ATC with lookahead: jobs released within `window` of the free machine are eligible,
    and waiting for them costs an idle penalty (Morton's X-dispatch idea)."""
    n = len(jobs)
    scale = kk * pbar
    free = [(0, k) for k in range(m)]
    pool, out, i = [], [], 0
    cost = 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        if not pool and jobs[by_rel[i]][0] > t:
            t = jobs[by_rel[i]][0]
        horizon = t + window
        while i < n and jobs[by_rel[i]][0] <= horizon:
            pool.append(by_rel[i])
            i += 1
        bi, bv = 0, None
        for idx in range(len(pool)):
            j = pool[idx]
            r, p, d, w = jobs[j]
            s = r if r > t else t
            sl = d - p - s
            v = logwp[j] - (sl / scale if sl > 0 else 0.0)
            if s > t:
                v -= idle_pen * (s - t) / pbar
            if bv is None or v > bv:
                bv, bi = v, idx
        j = pool[bi]
        pool[bi] = pool[-1]
        pool.pop()
        r, p, d, w = jobs[j]
        s = r if r > t else t
        out.append((j, k, s))
        if s + p > d:
            cost += w * (s + p - d)
        heapq.heappush(free, (s + p, k))
    return out, cost


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
    pmin = min(jb[1] for jb in jobs)
    logwp = [math.log(max(w, 1e-6) / (p if p > 0 else 0.5)) for r, p, d, w in jobs]
    by_rel = sorted(range(n), key=lambda j: (jobs[j][0], j))

    grid = []
    for kk in (1.0, 2.0, 0.5, 3.0, 0.25, 5.0):
        grid.append((kk, 0.0, 0.0))
    for kk in (1.0, 2.0, 0.5, 3.0):
        for win in (0.5 * pbar, pbar, max(pmin, 1)):
            for pen in (1.0, 2.0, 4.0):
                grid.append((kk, win, pen))
    for kk, win, pen in grid:
        if time.perf_counter() - t0 > 0.7:
            break
        sch, c = _xatc(jobs, m, by_rel, logwp, pbar, kk, win, pen)
        if c < best_c:
            best, best_c = sch, c
            if c == 0:
                break
    return best
