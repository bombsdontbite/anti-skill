"""Iterated greedy over a job permutation: destroy a few jobs, reinsert each at the best of a
handful of nearby positions, accept with a Ruiz-Stuetzle style constant temperature."""
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


def _decode(jobs, perm, m, build=False):
    free = [0] * m
    cost = 0
    out = []
    for j in perm:
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
        if s + p > d:
            cost += w * (s + p - d)
        if build:
            out.append((j, k, s))
    return cost, out


def schedule(jobs, m):
    t0 = time.perf_counter()
    limit = 0.75
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(4242)
    starts = [
        [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))],
        sorted(range(n), key=lambda j: (jobs[j][2], j)),
        sorted(range(n), key=lambda j: (jobs[j][0] + jobs[j][1], jobs[j][2])),
    ]
    cur, cc = None, None
    for s in starts:
        c, _ = _decode(jobs, s, m)
        if cc is None or c < cc:
            cur, cc = s, c
    best, bc = cur[:], cc
    psum = sum(jb[1] for jb in jobs)
    wsum = sum(jb[3] for jb in jobs)
    temp = 0.4 * (psum / n) * (wsum / n) / 10.0 or 1.0

    while time.perf_counter() - t0 < limit:
        o = cur[:]
        dsize = rng.randint(2, 6)
        removed = []
        for _ in range(dsize):
            removed.append(o.pop(rng.randrange(len(o))))
        for j in removed:
            dj = jobs[j][2]
            pos0 = 0
            for x in o:
                if jobs[x][2] < dj:
                    pos0 += 1
            cand = set()
            for off in (-8, -4, -2, -1, 0, 1, 2, 4, 8):
                q = pos0 + off
                if 0 <= q <= len(o):
                    cand.add(q)
            for _ in range(2):
                cand.add(rng.randint(0, len(o)))
            bpos, bval = 0, None
            for q in cand:
                o.insert(q, j)
                c, _ = _decode(jobs, o, m)
                o.pop(q)
                if bval is None or c < bval:
                    bval, bpos = c, q
            o.insert(bpos, j)
            if time.perf_counter() - t0 > limit:
                break
        if len(o) != n:
            break
        c, _ = _decode(jobs, o, m)
        if c < cc or rng.random() < math.exp(-(c - cc) / temp):
            cur, cc = o, c
            if c < bc:
                best, bc = o[:], c
                if bc == 0:
                    break

    c, sch = _decode(jobs, best, m, True)
    if c < base_c:
        return sch
    return base
