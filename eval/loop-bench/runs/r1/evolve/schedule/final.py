import math
import random
import time


def _dispatch(jobs, m, prio):
    n = len(jobs)
    left = set(range(n))
    free = [0] * m
    out, cost = [], 0
    while left:
        mk = min(range(m), key=lambda x: free[x])
        t = free[mk]
        ready = [j for j in left if jobs[j][0] <= t]
        if not ready:
            t = min(jobs[j][0] for j in left)
            ready = [j for j in left if jobs[j][0] <= t]
        bj = min(ready, key=lambda j: (prio(j, t), j))
        left.discard(bj)
        r, p, d, w = jobs[bj]
        out.append((bj, mk, t))
        free[mk] = t + p
        if t + p > d:
            cost += w * (t + p - d)
    return cost, out


def _portfolio(jobs, m):
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / max(n, 1)
    rules = [
        lambda j, t: jobs[j][2],
        lambda j, t: max(jobs[j][2], t + jobs[j][1]),
        lambda j, t: max(jobs[j][1], jobs[j][2] - t) / jobs[j][3],
        lambda j, t: jobs[j][1] / jobs[j][3],
    ]
    for k in (0.5, 1.0, 2.0, 3.0, 5.0):
        rules.append(lambda j, t, k=k: -jobs[j][3] / jobs[j][1] * math.exp(
            -max(jobs[j][2] - jobs[j][1] - t, 0) / (k * pbar)))
    best = None
    for pr in rules:
        c, out = _dispatch(jobs, m, pr)
        if best is None or c < best[0]:
            best = (c, out)
    return best


def _pilot(jobs, m, t0, tlim, H=12, ncand=3):
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / max(n, 1)
    order = sorted(range(n), key=lambda j: jobs[j][0])

    def idx(j, t, kp):
        r, p, d, w = jobs[j]
        return w / p * math.exp(-max(d - p - t, 0) / kp)

    def run(free, ready, i, kp, steps, forced=None):
        # dispatch `steps` jobs (all if None); returns cost, assignments, state
        free = free[:]; ready = ready[:]
        out, cost, cnt = [], 0, 0
        while (steps is None or cnt < steps) and (ready or i < n):
            mk = min(range(m), key=lambda x: free[x])
            t = free[mk]
            if not ready and jobs[order[i]][0] > t:
                t = jobs[order[i]][0]
            while i < n and jobs[order[i]][0] <= t:
                ready.append(order[i]); i += 1
            if forced is not None and cnt == 0:
                bi = ready.index(forced)
            else:
                bv, bi = -1.0, 0
                for q, j in enumerate(ready):
                    v = idx(j, t, kp)
                    if v > bv:
                        bv, bi = v, q
            j = ready[bi]; ready[bi] = ready[-1]; ready.pop()
            r, p, d, w = jobs[j]
            if r > t:
                t = r
            out.append((j, mk, t)); free[mk] = t + p
            if t + p > d:
                cost += w * (t + p - d)
            cnt += 1
        return cost, out, free, ready, i

    bestk, bestc = 2.0, None
    for k in (0.5, 1.0, 2.0, 3.0, 5.0):
        c = run([0] * m, [], 0, k * pbar, None)[0]
        if bestc is None or c < bestc:
            bestk, bestc = k, c
    kp = bestk * pbar
    base = run([0] * m, [], 0, kp, None)

    free, ready, i, out, total = [0] * m, [], 0, [], 0
    while len(out) < n:
        if time.time() - t0 > tlim:
            c, rest, _, _, _ = run(free, ready, i, kp, None)
            out += rest; total += c
            break
        mk = min(range(m), key=lambda x: free[x])
        t = free[mk]
        rd = ready[:]; ii = i
        if not rd and jobs[order[ii]][0] > t:
            t = jobs[order[ii]][0]
        while ii < n and jobs[order[ii]][0] <= t:
            rd.append(order[ii]); ii += 1
        cands = sorted(rd, key=lambda j: -idx(j, t, kp))[:ncand]
        best = None
        for j in cands:
            c = run(free, ready, i, kp, H, forced=j)[0]
            if best is None or c < best[0]:
                best = (c, j)
        c, step, free, ready, i = run(free, ready, i, kp, 1, forced=best[1])
        out += step; total += c
    return (total, out) if total <= base[0] else (base[0], base[1])


def _decoder(jobs, m):
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]

    def decode(order, emit=False):
        free = [0] * m
        c = 0
        out = []
        for j in order:
            r = R[j]
            bk, bs = 0, None
            for k in range(m):
                s = free[k] if free[k] > r else r
                if bs is None or s < bs or (s == bs and free[k] > free[bk]):
                    bk, bs = k, s
            e = bs + P[j]
            free[bk] = e
            if e > D[j]:
                c += W[j] * (e - D[j])
            if emit:
                out.append((j, bk, bs))
        return out if emit else c
    return decode


def _sa(jobs, m, order, t0, limit, seed=7):
    n = len(jobs)
    decode = _decoder(jobs, m)
    cur = decode(order)
    best, bestc = order[:], cur
    if n < 2:
        return bestc, best, decode
    rng = random.Random(seed)
    deltas = []
    for _ in range(20):
        i = rng.randrange(n); q = max(0, min(n - 1, i + rng.randint(-8, 8)))
        o = order[:]; x = o.pop(i); o.insert(q, x)
        deltas.append(abs(decode(o) - cur))
    T0 = max(1e-9, 0.1 * sum(deltas) / len(deltas))
    Tend = T0 / 100
    start = time.time() - t0
    span = max(1e-6, limit - start)
    while True:
        el = time.time() - t0
        if el > limit:
            break
        T = T0 * (Tend / T0) ** ((el - start) / span)
        for _ in range(10):
            i = rng.randrange(n); q = i + rng.randint(-8, 8)
            if q < 0 or q >= n or q == i:
                continue
            new = order[:]; x = new.pop(i); new.insert(q, x)
            c = decode(new)
            if c <= cur or rng.random() < math.exp(-(c - cur) / T):
                order, cur = new, c
                if c < bestc:
                    best, bestc = new, c
    return bestc, best, decode



def _rr(jobs, m, seed, t0, limit):
    n = len(jobs)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    seqs = [[] for _ in range(m)]
    for j, k, s in sorted(seed[1], key=lambda x: x[2]):
        seqs[k].append(j)

    def mcost(seq):
        t = 0; c = 0
        for j in seq:
            s = t if t > R[j] else R[j]
            t = s + P[j]
            if t > D[j]:
                c += W[j] * (t - D[j])
        return c

    mc = [mcost(s) for s in seqs]
    cur = sum(mc)
    bydl = sorted(range(n), key=lambda j: D[j])
    rank = [0] * n
    for i, j in enumerate(bydl):
        rank[j] = i
    rng = random.Random(13)
    while time.time() - t0 < limit and n > 3:
        new = [s[:] for s in seqs]
        nc = mc[:]
        c0 = rank[rng.randrange(n)]
        rem = set()
        size = rng.randint(2, 5)
        while len(rem) < size:
            rem.add(bydl[max(0, min(n - 1, c0 + rng.randint(-6, 6)))])
        touched = set()
        for k in range(m):
            if any(j in rem for j in new[k]):
                new[k] = [j for j in new[k] if j not in rem]
                touched.add(k)
        for k in touched:
            nc[k] = mcost(new[k])
        rl = list(rem)
        rng.shuffle(rl)
        for j in rl:
            bd, bk, bq = None, 0, 0
            for k in range(m):
                sk = new[k]
                pos = 0
                while pos < len(sk) and D[sk[pos]] < D[j]:
                    pos += 1
                for q in range(max(0, pos - 3), min(len(sk), pos + 3) + 1):
                    c = mcost(sk[:q] + [j] + sk[q:]) - nc[k]
                    if bd is None or c < bd:
                        bd, bk, bq = c, k, q
            new[bk].insert(bq, j)
            nc[bk] += bd
        tot = sum(nc)
        if tot <= cur:
            seqs, mc, cur = new, nc, tot
    if cur > seed[0]:
        return seed[1]
    out = []
    for k, seq in enumerate(seqs):
        t = 0
        for j in seq:
            s = t if t > R[j] else R[j]
            out.append((j, k, s))
            t = s + P[j]
    return out



def schedule(jobs, m):
    """cand_13 (portfolio/pilot seed, SA on the list) for 0.56 s, then ruin & recreate on the
    per-machine sequences (cand_17) for the rest of 0.8 s."""
    t0 = time.time()
    seed = min(_portfolio(jobs, m), _pilot(jobs, m, t0, 0.3), key=lambda x: x[0])
    order = [j for _, j in sorted((s, j) for j, _, s in seed[1])]
    bc, best, decode = _sa(jobs, m, order, t0, 0.56)
    if bc <= seed[0]:
        seed = (bc, decode(best, True))
    return _rr(jobs, m, seed, t0, 0.8)
