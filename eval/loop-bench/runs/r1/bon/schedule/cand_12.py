import heapq
import math
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


def _rule(jobs, m, by_rel, lw, lp, pbar, a, b, kk, g, cap):
    """Dispatch with priority a*log w - b*log p - slack+/(kk*pbar) + g*overdue/pbar.
    Gives up as soon as the running cost reaches `cap`."""
    n = len(jobs)
    scale = kk * pbar
    free = [(0, q) for q in range(m)]
    ready, out, i, cost = [], [], 0, 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[by_rel[i]][0] > t:
            t = jobs[by_rel[i]][0]
        while i < n and jobs[by_rel[i]][0] <= t:
            ready.append(by_rel[i])
            i += 1
        bi, bv = 0, None
        for idx in range(len(ready)):
            j = ready[idx]
            sl = jobs[j][2] - jobs[j][1] - t
            v = a * lw[j] - b * lp[j]
            if sl > 0:
                v -= sl / scale
            else:
                v -= g * sl / pbar
            if bv is None or v > bv:
                bv, bi = v, idx
        j = ready[bi]
        ready[bi] = ready[-1]
        ready.pop()
        out.append((j, k, t))
        e = t + jobs[j][1]
        if e > jobs[j][2]:
            cost += jobs[j][3] * (e - jobs[j][2])
            if cost >= cap:
                return None, cost
        heapq.heappush(free, (e, k))
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

    rng = random.Random(8)
    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    lw = [math.log(max(jb[3], 1e-6)) for jb in jobs]
    lp = [math.log(jb[1] if jb[1] > 0 else 0.5) for jb in jobs]
    by_rel = sorted(range(n), key=lambda j: (jobs[j][0], j))

    params = None
    for kk in (0.5, 1.0, 2.0, 4.0):
        for g in (0.0, 0.3):
            pr = (1.0, 1.0, kk, g)
            sch, c = _rule(jobs, m, by_rel, lw, lp, pbar, pr[0], pr[1], pr[2], pr[3], best_c)
            if sch is not None and c < best_c:
                best, best_c, params = sch, c, pr
    if params is None:
        params = (1.0, 1.0, 1.0, 0.0)

    step = 0.4
    fails = 0
    while time.perf_counter() - t0 < 0.73 and best_c > 0:
        a, b, kk, g = params
        a = max(0.0, a + rng.gauss(0, step))
        b = max(0.0, b + rng.gauss(0, step))
        kk = min(20.0, max(0.05, kk * math.exp(rng.gauss(0, step))))
        g = max(0.0, g + rng.gauss(0, step * 0.5))
        sch, c = _rule(jobs, m, by_rel, lw, lp, pbar, a, b, kk, g, best_c)
        if sch is not None and c < best_c:
            best, best_c, params = sch, c, (a, b, kk, g)
            fails = 0
        else:
            fails += 1
            if fails > 12:
                step = max(0.05, step * 0.8)
                fails = 0
                if rng.random() < 0.2:
                    step = 0.6
    return best
