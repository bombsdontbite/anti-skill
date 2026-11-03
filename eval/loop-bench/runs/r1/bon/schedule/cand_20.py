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


def _list(jobs, seq, m, keep=None):
    heap = [(0, k) for k in range(m)]
    c = 0
    for j in seq:
        r, p, d, w = jobs[j]
        f, k = heapq.heappop(heap)
        s = f if f > r else r
        heapq.heappush(heap, (s + p, k))
        if s + p > d:
            c += w * (s + p - d)
        if keep is not None:
            keep.append((j, k, s))
    return c


def _late_positions(jobs, seq, m):
    heap = [(0, k) for k in range(m)]
    res = []
    for pos, j in enumerate(seq):
        r, p, d, w = jobs[j]
        f, k = heapq.heappop(heap)
        s = f if f > r else r
        heapq.heappush(heap, (s + p, k))
        if s + p > d:
            res.append(pos)
    return res


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 2:
        return base

    pbar = (sum(jb[1] for jb in jobs) / n) or 1.0
    wbar = (sum(jb[3] for jb in jobs) / n) or 1.0
    best_seq, best_c = None, None
    for alpha in (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
        for beta in (-1.0, -0.5, 0.0, 0.5):
            if time.perf_counter() - t0 > 0.35:
                break
            key = [jobs[j][2] - alpha * pbar * jobs[j][3] / wbar + beta * jobs[j][1] for j in range(n)]
            seq = sorted(range(n), key=lambda j: (key[j], jobs[j][0], j))
            c = _list(jobs, seq, m)
            if best_c is None or c < best_c:
                best_seq, best_c = seq, c
    starts = [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]
    c = _list(jobs, starts, m)
    if best_c is None or c < best_c:
        best_seq, best_c = starts, c

    seq = best_seq[:]
    moved = True
    while moved and time.perf_counter() - t0 < 0.74 and best_c > 0:
        moved = False
        for pos in _late_positions(jobs, seq, m):
            for back in (1, 2, 3, 5, 8):
                q = pos - back
                if q < 0:
                    break
                if time.perf_counter() - t0 > 0.74:
                    break
                x = seq.pop(pos)
                seq.insert(q, x)
                c = _list(jobs, seq, m)
                if c < best_c:
                    best_c = c
                    moved = True
                    break
                seq.pop(q)
                seq.insert(pos, x)
            if moved:
                break

    out = []
    _list(jobs, seq, m, out)
    if _cost(jobs, out) < base_c:
        return out
    return base
