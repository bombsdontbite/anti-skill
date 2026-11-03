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


def _play(jobs, seq, m, log=None):
    free = [0] * m
    total = 0
    for j in seq:
        r, p, d, w = jobs[j]
        k = 0
        key = None
        for q in range(m):
            f = free[q]
            st = f if f > r else r
            kq = (st, -f)
            if key is None or kq < key:
                key, k = kq, q
        s = key[0]
        free[k] = s + p
        if s + p > d:
            total += w * (s + p - d)
        if log is not None:
            log.append((j, k, s))
    return total


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(2121)
    first = [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]
    second = sorted(range(n), key=lambda j: (jobs[j][2], -jobs[j][3], j))
    cur = first if _play(jobs, first, m) <= _play(jobs, second, m) else second
    cc = _play(jobs, cur, m)
    best, bc = cur[:], cc

    total_time = 0.75
    rounds = 3
    for rnd in range(rounds):
        r_start = time.perf_counter() - t0
        r_end = r_start + (total_time - r_start) / (rounds - rnd)
        th0 = max(1.0, 0.005 * cc)
        if rnd > 0:
            cur, cc = best[:], bc
        while True:
            el = time.perf_counter() - t0
            if el > r_end or bc == 0:
                break
            th = th0 * (1.0 - (el - r_start) / max(1e-9, r_end - r_start))
            o = cur[:]
            i = rng.randrange(n)
            q = min(n - 1, max(0, i + rng.randint(-18, 18)))
            if i == q:
                continue
            if rng.random() < 0.7:
                o.insert(q, o.pop(i))
            else:
                o[i], o[q] = o[q], o[i]
            c = _play(jobs, o, m)
            if c - cc < th:
                cur, cc = o, c
                if c < bc:
                    best, bc = o[:], c

    out = []
    _play(jobs, best, m, out)
    if _cost(jobs, out) < base_c:
        return out
    return base
