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


def _atc(jobs, m, scale):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: (jobs[j][0], j))
    lv = [math.log(max(w, 1e-6) / (p if p > 0 else 0.5)) for r, p, d, w in jobs]
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


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0:
        return base

    R = [jb[0] for jb in jobs]
    P = [jb[1] for jb in jobs]
    D = [jb[2] for jb in jobs]
    W = [jb[3] for jb in jobs]
    pbar = (sum(P) / n) or 1.0

    def line(seq):
        t = 0
        c = 0
        for j in seq:
            if R[j] > t:
                t = R[j]
            t += P[j]
            if t > D[j]:
                c += W[j] * (t - D[j])
        return c

    init, init_c = base, base_c
    alt = _atc(jobs, m, 2.0 * pbar)
    alt_c = _cost(jobs, alt)
    if alt_c < init_c:
        init, init_c = alt, alt_c

    seqs = [[] for _ in range(m)]
    for j, k, s in sorted(init, key=lambda x: (x[2], x[0])):
        seqs[k].append(j)
    mc = [line(s) for s in seqs]
    cur = sum(mc)
    best_seqs, best = [s[:] for s in seqs], cur

    rng = random.Random(19)
    t_hi = max(1.0, 0.01 * cur)
    t_lo = t_hi * 1e-4
    budget = 0.76
    while True:
        el = time.perf_counter() - t0
        if el > budget or best == 0:
            break
        temp = t_hi * (t_lo / t_hi) ** (el / budget)
        a = rng.randrange(m)
        if not seqs[a]:
            continue
        mv = rng.random()
        if mv < 0.45 or m == 1:
            sa = seqs[a][:]
            if len(sa) < 2:
                continue
            i = rng.randrange(len(sa))
            q = min(len(sa) - 1, max(0, i + rng.randint(-4, 4)))
            if i == q:
                continue
            if rng.random() < 0.5:
                sa[i], sa[q] = sa[q], sa[i]
            else:
                sa.insert(q, sa.pop(i))
            ca = line(sa)
            dlt = ca - mc[a]
            if dlt <= 0 or rng.random() < math.exp(-dlt / temp):
                seqs[a] = sa
                mc[a] = ca
                cur += dlt
        else:
            b = rng.randrange(m - 1)
            if b >= a:
                b += 1
            sa = seqs[a][:]
            sb = seqs[b][:]
            i = rng.randrange(len(sa))
            j = sa[i]
            if mv < 0.8 or not sb:
                sa.pop(i)
                pos = 0
                for x in sb:
                    if D[x] < D[j]:
                        pos += 1
                pos = min(len(sb), max(0, pos + rng.randint(-2, 2)))
                sb.insert(pos, j)
            else:
                q = min(len(sb) - 1, max(0, rng.randrange(len(sb))))
                sa[i], sb[q] = sb[q], sa[i]
            ca, cb = line(sa), line(sb)
            dlt = ca + cb - mc[a] - mc[b]
            if dlt <= 0 or rng.random() < math.exp(-dlt / temp):
                seqs[a], seqs[b] = sa, sb
                mc[a], mc[b] = ca, cb
                cur += dlt
        if cur < best:
            best = cur
            best_seqs = [s[:] for s in seqs]

    if best >= init_c:
        return init
    out = []
    for k in range(m):
        t = 0
        for j in best_seqs[k]:
            s = R[j] if R[j] > t else t
            out.append((j, k, s))
            t = s + P[j]
    return out
