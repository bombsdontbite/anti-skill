import heapq
import random
import time

STOP = 0.74


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


def _tw(jobs, seq, m):
    free = [0] * m
    c = 0
    for j in seq:
        r, p, d, w = jobs[j]
        k = free.index(min(free))
        s = free[k] if free[k] > r else r
        free[k] = s + p
        if s + p > d:
            c += w * (s + p - d)
    return c


def _sched(jobs, seq, m):
    free = [0] * m
    out = []
    for j in seq:
        k = free.index(min(free))
        s = max(free[k], jobs[j][0])
        free[k] = s + jobs[j][1]
        out.append((j, k, s))
    return out


def _vnd(jobs, seq, m, val, t0, rng):
    n = len(seq)
    level = 0
    while level < 3:
        if time.perf_counter() - t0 > STOP:
            break
        improved = False
        idxs = list(range(n))
        rng.shuffle(idxs)
        for i in idxs:
            if time.perf_counter() - t0 > STOP:
                break
            if level == 0:
                if i + 1 >= n:
                    continue
                seq[i], seq[i + 1] = seq[i + 1], seq[i]
                v = _tw(jobs, seq, m)
                if v < val:
                    val, improved = v, True
                    break
                seq[i], seq[i + 1] = seq[i + 1], seq[i]
            elif level == 1:
                for q in (i - 5, i - 3, i - 2, i + 2, i + 3, i + 5):
                    if 0 <= q < n:
                        x = seq.pop(i)
                        seq.insert(q, x)
                        v = _tw(jobs, seq, m)
                        if v < val:
                            val, improved = v, True
                            break
                        seq.pop(q)
                        seq.insert(i, x)
                if improved:
                    break
            else:
                q = i + rng.randint(4, 12)
                if q < n:
                    seq[i], seq[q] = seq[q], seq[i]
                    v = _tw(jobs, seq, m)
                    if v < val:
                        val, improved = v, True
                        break
                    seq[i], seq[q] = seq[q], seq[i]
        level = 0 if improved else level + 1
    return seq, val


def schedule(jobs, m):
    t0 = time.perf_counter()
    n = len(jobs)
    if n == 0:
        return []
    base = _edf(jobs, m)
    base_c = _cost(jobs, base)
    if base_c == 0 or n < 3:
        return base

    rng = random.Random(16)
    cur = [j for j, _k, _s in sorted(base, key=lambda x: (x[2], x[0]))]
    cv = _tw(jobs, cur, m)
    edd = sorted(range(n), key=lambda j: (jobs[j][2], j))
    ev = _tw(jobs, edd, m)
    if ev < cv:
        cur, cv = edd, ev
    cur, cv = _vnd(jobs, cur, m, cv, t0, rng)
    best, bv = cur[:], cv

    shake = 2
    while time.perf_counter() - t0 < STOP and bv > 0:
        o = best[:]
        for _ in range(shake):
            i = rng.randrange(n)
            q = min(n - 1, max(0, i + rng.randint(-20, 20)))
            o.insert(q, o.pop(i))
        ov = _tw(jobs, o, m)
        o, ov = _vnd(jobs, o, m, ov, t0, rng)
        if ov < bv:
            best, bv = o[:], ov
            shake = 2
        else:
            shake = shake + 1 if shake < 8 else 2

    sch = _sched(jobs, best, m)
    if _cost(jobs, sch) < base_c:
        return sch
    return base
