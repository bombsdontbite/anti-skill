import bisect
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


def _atc(jobs, m, scale, lv):
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
        bi, bv = 0, None
        for idx in range(len(ready)):
            j = ready[idx]
            sl = jobs[j][2] - jobs[j][1] - t
            v = lv[j] - (sl / scale if sl > 0 else 0.0)
            if bv is None or v > bv:
                bv, bi = v, idx
        j = ready[bi]
        ready[bi] = ready[-1]
        ready.pop()
        out.append((j, k, t))
        heapq.heappush(free, (t + jobs[j][1], k))
    return out


def _compact(jobs, sched, m):
    """Re-place jobs in their current start order, each into the earliest hole that fits."""
    starts = [[] for _ in range(m)]
    ends = [[] for _ in range(m)]
    out = []
    for j, _k, _s in sorted(sched, key=lambda x: (x[2], x[0])):
        r, p = jobs[j][0], jobs[j][1]
        bs, bi, bk = None, 0, 0
        for k in range(m):
            st, en = starts[k], ends[k]
            i = bisect.bisect_right(en, r)
            s = r
            while i < len(st):
                if s + p <= st[i]:
                    break
                if en[i] > s:
                    s = en[i]
                i += 1
            if bs is None or s < bs:
                bs, bi, bk = s, i, k
        starts[bk].insert(bi, bs)
        ends[bk].insert(bi, bs + p)
        out.append((j, bk, bs))
    return out


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    best_s = _edf(jobs, m)
    best_sc = _cost(jobs, best_s)
    if best_sc == 0:
        return best_s

    R = [jb[0] for jb in jobs]
    P = [jb[1] for jb in jobs]
    D = [jb[2] for jb in jobs]
    W = [jb[3] for jb in jobs]
    pbar = (sum(P) / n) or 1.0
    lv = [math.log(max(W[j], 1e-6) / (P[j] if P[j] > 0 else 0.5)) for j in range(n)]

    seeds = [[j for j, _k, _s in sorted(best_s, key=lambda x: (x[2], x[0]))]]
    for kk in (0.5, 1.0, 2.0, 4.0):
        if time.perf_counter() - t0 > 0.25:
            break
        sch = _atc(jobs, m, kk * pbar, lv)
        c = _cost(jobs, sch)
        if c < best_sc:
            best_s, best_sc = sch, c
        seeds.append([j for j, _k, _s in sorted(sch, key=lambda x: (x[2], x[0]))])
    seeds.append(sorted(range(n), key=lambda j: (D[j], j)))

    def tail(seq, lo, free0, c0, cap, frees=None, costs=None, late=None):
        free = free0[:]
        c = c0
        for idx in range(lo, n):
            j = seq[idx]
            r = R[j]
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
            e = s + P[j]
            free[k] = e
            lt = e > D[j]
            if lt:
                c += W[j] * (e - D[j])
                if c > cap:
                    return None
            if frees is not None:
                frees[idx + 1] = free[:]
                costs[idx + 1] = c
                late[idx] = lt
        return c

    inf = float("inf")
    zero = [0] * m
    cur, cc = None, inf
    for s in seeds:
        c = tail(s, 0, zero, 0, inf)
        if c < cc:
            cur, cc = s[:], c
    frees = [None] * (n + 1)
    costs = [0] * (n + 1)
    late = [False] * n
    frees[0] = zero[:]
    tail(cur, 0, zero, 0, inf, frees, costs, late)
    best, bc = cur[:], cc

    rng = random.Random(24)
    t_hi = max(1.0, 0.015 * cc)
    t_lo = t_hi * 1e-4
    budget = 0.7
    while n > 2 and bc > 0:
        el = time.perf_counter() - t0
        if el > budget:
            break
        temp = t_hi * (t_lo / t_hi) ** (el / budget)
        if rng.random() < 0.6:
            lates = [x for x in range(n) if late[x]]
            i = rng.choice(lates) if lates else rng.randrange(n)
            q = max(0, i - rng.randint(1, 20))
        else:
            i = rng.randrange(n)
            q = min(n - 1, max(0, i + rng.randint(-12, 12)))
        if i == q:
            continue
        o = cur[:]
        if rng.random() < 0.75:
            o.insert(q, o.pop(i))
        else:
            o[i], o[q] = o[q], o[i]
        lo = i if i < q else q
        cap = cc - temp * math.log(1.0 - rng.random())
        c = tail(o, lo, frees[lo], costs[lo], cap)
        if c is None:
            continue
        cur, cc = o, c
        tail(cur, lo, frees[lo], costs[lo], inf, frees, costs, late)
        if cc < bc:
            best, bc = cur[:], cc

    free = [0] * m
    sch = []
    for j in best:
        r = R[j]
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
        free[k] = s + P[j]
        sch.append((j, k, s))
    for cand in (sch, _compact(jobs, sch, m), _compact(jobs, best_s, m)):
        c = _cost(jobs, cand)
        if c < best_sc:
            best_s, best_sc = cand, c
    return best_s
