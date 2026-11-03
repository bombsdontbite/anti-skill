import heapq, math, random, time, bisect

TL = 0.75
TC = 0.1
PG = 0.15


def _dispatch(jobs, m, prio):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: jobs[j][0])
    free = [(0, k) for k in range(m)]
    seqs = [[] for _ in range(m)]
    ready, done, i = [], 0, 0
    while done < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        best = min(ready, key=lambda j: prio(j, t))
        ready.remove(best)
        st = max(t, jobs[best][0])
        seqs[k].append(best); done += 1
        heapq.heappush(free, (st + jobs[best][1], k))
    return seqs


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]

    def full(seq):
        t = 0; c = 0; E = []; C = []
        for j in seq:
            r = R[j]
            if r > t: t = r
            t += P[j]
            if t > D[j]: c += W[j] * (t - D[j])
            E.append(t); C.append(c)
        return E, C

    def ev(seq, p, qe, off, E, C):
        """Cost of seq, equal to the stored one before p; from qe on, seq[q] is old[q+off]."""
        if p > 0:
            t = E[p - 1]; c = C[p - 1]
        else:
            t = 0; c = 0
        tot = C[-1] if C else 0
        for q in range(p, len(seq)):
            j = seq[q]
            r = R[j]
            if r > t: t = r
            t += P[j]
            if t > D[j]: c += W[j] * (t - D[j])
            if q >= qe and t == E[q + off]:
                return c + tot - C[q + off]
        return c

    pbar = sum(P) / n
    rules = [lambda j, t: (D[j], j)]
    for K in (0.1, 0.3, 0.5, 1, 2, 3, 5):
        rules.append(lambda j, t, K=K: -(W[j] / P[j]) * math.exp(-max(0, D[j] - P[j] - t) / (K * pbar)))
    best = None
    for pr in rules:
        s = _dispatch(jobs, m, pr)
        c = sum(full(q)[1][-1] if q else 0 for q in s)
        if best is None or c < best[0]:
            best = (c, s)
    seqs = [list(q) for q in best[1]]
    EC = [full(q) for q in seqs]
    mc = [x[1][-1] if x[1] else 0 for x in EC]
    cur = sum(mc)
    bestc, bests = cur, [list(q) for q in seqs]
    rnd = random.Random(12345)
    rand = rnd.random; rr = rnd.randrange; ri = rnd.randint
    L = 8
    it = 0
    T0 = TC * (sum(W) / n) * pbar
    ts = time.time(); span = TL - (ts - t0)
    T = T0
    exp = math.exp
    while cur > 0:
        if it & 255 == 0:
            fr = (time.time() - ts) / span
            if fr >= 1: break
            T = T0 * (1 - fr) ** 2 + 1e-9
        it += 1
        a = rr(m)
        sa = seqs[a]; la = len(sa)
        if la == 0: continue
        mv = rand()
        if mv < 0.6:
            i = rr(la)
            if mv < PG:
                k = rr(la)
            else:
                k = i + ri(-L, L)
            if k == i or k < 0 or k >= la: continue
            if mv < 0.4:
                na = list(sa); j = na.pop(i); na.insert(k, j)
            elif mv < 0.5:
                bl = ri(2, 3)
                if i + bl > la: continue
                blk = sa[i:i + bl]; rest = sa[:i] + sa[i + bl:]
                if k > len(rest): k = len(rest)
                na = rest[:k] + blk + rest[k:]
                qe = max(i, k) + bl - 1
                if na == sa: continue
            else:
                na = list(sa); na[i], na[k] = na[k], na[i]
            p = i if i < k else k
            if not (0.4 <= mv < 0.5): qe = i if i > k else k
            Ea, Ca = EC[a]
            ca = ev(na, p, qe, 0, Ea, Ca); d = ca - mc[a]
            if d <= 0 or rand() < exp(-d / T):
                seqs[a] = na; EC[a] = full(na); mc[a] = ca; cur += d
        else:
            b = rr(m)
            if b == a: continue
            sb = seqs[b]
            i = rr(la); j = sa[i]
            Ea, Ca = EC[a]; Eb, Cb = EC[b]
            st = Ea[i] - P[j]
            k = bisect.bisect_left(Eb, st) + ri(-2, 2)
            if k < 0: k = 0
            if mv < 0.8 or not sb:
                if k > len(sb): k = len(sb)
                na = sa[:i] + sa[i + 1:]; nb = sb[:k] + [j] + sb[k:]
                ca = ev(na, i, i, 1, Ea, Ca); cb = ev(nb, k, k + 1, -1, Eb, Cb)
            else:
                if k >= len(sb): k = len(sb) - 1
                na = list(sa); nb = list(sb); na[i], nb[k] = sb[k], j
                ca = ev(na, i, i, 0, Ea, Ca); cb = ev(nb, k, k, 0, Eb, Cb)
            d = ca + cb - mc[a] - mc[b]
            if d <= 0 or rand() < exp(-d / T):
                seqs[a] = na; seqs[b] = nb; EC[a] = full(na); EC[b] = full(nb)
                mc[a] = ca; mc[b] = cb; cur += d
        if cur < bestc:
            bestc = cur; bests = [list(q) for q in seqs]
    out = []
    for k, q in enumerate(bests):
        t = 0
        for j in q:
            t = max(t, R[j]); out.append((j, k, t)); t += P[j]
    return out
