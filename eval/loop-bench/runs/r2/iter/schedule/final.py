import heapq, math, random, time
from bisect import bisect_right, insort

LIMIT = 0.85
CLOCK = time.time
SEED = 12345
NS = 1
PT = 0.5
PE = 0.8
PI = 0.6
LA = 0.0
TF0 = 0.0
TF1 = 0.0


def _dispatch(jobs, m, key):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    heapq.heapify(free)
    ready, seq, i = [], [], 0
    while len(seq) < n:
        t, k = heapq.heappop(free)
        if not ready and i < n and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        best = 0; bv = None
        for idx in range(len(ready)):
            v = key(ready[idx], t)
            if bv is None or v < bv:
                bv = v; best = idx
        j = ready[best]; ready[best] = ready[-1]; ready.pop()
        seq.append(j)
        heapq.heappush(free, (max(t, jobs[j][0]) + jobs[j][1], k))
    return seq


def _dispatch_la(jobs, m, kk, k2, win):
    # ATC with ready times: jobs released within `win` of the free time compete, discounted.
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / n
    order = sorted(range(n), key=lambda j: (jobs[j][0], j))
    free = [0] * m
    pool, seq, i = [], [], 0
    a1 = 1.0 / (kk * pbar); a2 = 1.0 / (k2 * pbar)
    while len(seq) < n:
        t = min(free)
        k = free.index(t)
        if not pool and i < n and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t + win:
            pool.append(order[i]); i += 1
        best = 0; bv = None
        for idx in range(len(pool)):
            r, p, d, w = jobs[pool[idx]]
            sl = d - p - (r if r > t else t)
            v = (w / p) * math.exp(-(sl if sl > 0 else 0) * a1 - ((r - t) if r > t else 0) * a2)
            if bv is None or v > bv:
                bv = v; best = idx
        j = pool[best]; pool[best] = pool[-1]; pool.pop()
        seq.append(j)
        r = jobs[j][0]
        free[k] = (r if r > t else t) + jobs[j][1]
    return seq


def schedule(jobs, m):
    t0 = CLOCK()
    n = len(jobs)
    if n == 0:
        return []
    rnd = random.Random(SEED)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    pbar = max(1.0, sum(P) / n)
    hrep = heapq.heapreplace

    def decode_full(perm):
        free = [0] * m
        out = []
        for j in perm:
            r = R[j]
            bf = min(free); bk = free.index(bf)
            bs = bf if bf > r else r
            free[bk] = bs + P[j]
            out.append((j, bk, bs))
        return out

    def build(perm):
        states = [None] * (n + 1); costs = [0] * (n + 1)
        free = [0] * m; c = 0
        for i in range(n):
            states[i] = free[:]; costs[i] = c
            j = perm[i]; r = R[j]; f = free[0]
            e = (r if r > f else f) + P[j]
            hrep(free, e)
            if e > D[j]:
                c += W[j] * (e - D[j])
        states[n] = free[:]; costs[n] = c
        return states, costs

    cands = [_dispatch(jobs, m, lambda j, t: (D[j], j))]
    for kk in (0.1, 0.25, 0.5, 1.0, 2.0, 3.0):
        def atc(j, t, kk=kk):
            sl = D[j] - P[j] - t
            if sl < 0: sl = 0
            return -(W[j] / (P[j] or 0.5)) * math.exp(-sl / (kk * pbar))
        cands.append(_dispatch(jobs, m, atc))
    cands.append(_dispatch(jobs, m, lambda j, t: max(P[j], D[j] - t) / (W[j] or 1e-9)))
    if LA:
        for kk in (0.25, 0.5, 1.0):
            cands.append(_dispatch_la(jobs, m, kk, 0.5, pbar))
    cands.append(sorted(range(n), key=lambda j: (D[j], j)))

    scored = []
    for perm in cands:
        st, cs = build(perm)
        scored.append((cs[n], perm))
    scored.sort(key=lambda x: x[0])

    def ls(perm, tend):
        perm = list(perm)
        states, costs = build(perm)
        cur = costs[n]
        best_c = cur; best_perm = perm[:]
        it = 0
        nm1 = n - 1
        rr = rnd.random; ri = rnd.randint
        T0 = TF0 * cur / n; T1 = TF1 * cur / n
        T = T0; tbeg = CLOCK(); span = max(1e-9, tend - tbeg)
        lg = math.log
        while cur > 0:
            it += 1
            if (it & 63) == 0:
                el = CLOCK() - tbeg
                if el > span:
                    break
                if T0 > 0:
                    T = T0 * (T1 / T0) ** (el / span)
            a = int(rr() * n)
            u = rr()
            w = 3 if u < 0.3 else (12 if u < 0.6 else (40 if u < 0.85 else n))
            if rr() < PT:
                for _ in range(10):
                    if costs[a + 1] > costs[a]:
                        break
                    a = int(rr() * n)
                if rr() < PE:
                    b = a - ri(1, w)
                else:
                    b = a + ri(-w, w)
            else:
                b = a + ri(-w, w)
            if b < 0: b = 0
            elif b > nm1: b = nm1
            if a == b:
                continue
            mv = rr() < PI
            if mv:
                x = perm.pop(a); perm.insert(b, x)
            else:
                perm[a], perm[b] = perm[b], perm[a]
            if a < b:
                lo, hi = a, b
            else:
                lo, hi = b, a
            free = states[lo][:]
            c = costs[lo]
            thr = cur - T * lg(1.0 - rr()) if T0 > 0 else cur
            i = lo
            conv = -1
            while i < n:
                j = perm[i]; r = R[j]; f = free[0]
                e = (r if r > f else f) + P[j]
                hrep(free, e)
                if e > D[j]:
                    c += W[j] * (e - D[j])
                    if c > thr:
                        break
                i += 1
                if i > hi and free == states[i]:
                    conv = i
                    c += costs[n] - costs[i]
                    break
            else:
                conv = n
            if conv >= 0 and c <= thr:
                delta = c - cur
                cur = c
                free = states[lo][:]; cc = costs[lo]
                for i in range(lo, conv):
                    states[i] = free[:]; costs[i] = cc
                    j = perm[i]; r = R[j]; f = free[0]
                    e = (r if r > f else f) + P[j]
                    hrep(free, e)
                    if e > D[j]:
                        cc += W[j] * (e - D[j])
                if delta:
                    for i in range(conv, n + 1):
                        costs[i] += delta
                if cur < best_c:
                    best_c = cur; best_perm = perm[:]
            else:
                if mv:
                    x = perm.pop(b); perm.insert(a, x)
                else:
                    perm[a], perm[b] = perm[b], perm[a]
        return best_c, best_perm

    ns = int(NS)
    starts = scored[:ns]
    res = []
    now = CLOCK()
    tot = t0 + LIMIT - now
    for idx, (c0, p0) in enumerate(starts):
        tend = CLOCK() + (tot * (0.5 if ns > 1 else 1.0)) / ns
        res.append(ls(p0, tend))
    res.sort(key=lambda x: x[0])
    bc, bp = res[0]
    if ns > 1:
        bc, bp = ls(bp, t0 + LIMIT)
    return decode_full(bp)
