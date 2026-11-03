import heapq, math, random, time
def _edf(jobs, m):
    order = sorted(range(len(jobs)), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i = [], [], 0
    cost = 0
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
        if t + jobs[j][1] > jobs[j][2]: cost += jobs[j][3] * (t + jobs[j][1] - jobs[j][2])
        heapq.heappush(free, (t + jobs[j][1], k))
    return cost, out



def _dispatch(jobs, m, prio):
    # non-delay list scheduling; prio(j, t) -> larger is better
    order = sorted(range(len(jobs)), key=lambda j: (jobs[j][0], j))
    free = [(0, k) for k in range(m)]
    ready, out, i, n = [], [], 0, len(jobs)
    cost = 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        if not ready and i < n and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        bj = max(ready, key=lambda j: prio(j, t))
        ready.remove(bj)
        r, p, d, w = jobs[bj]
        t = max(t, r)
        out.append((bj, k, t))
        if t + p > d: cost += w * (t + p - d)
        heapq.heappush(free, (t + p, k))
    return cost, out


def dispatch_best(jobs, m):
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / max(1, n)
    rules = [lambda j, t: -jobs[j][2],
             lambda j, t: jobs[j][3] / jobs[j][1],
             lambda j, t: -(jobs[j][2] - jobs[j][1] - t)]
    for kk in (0.25, 0.5, 1.0, 2.0, 4.0):
        def atc(j, t, kp=kk * pbar):
            r, p, d, w = jobs[j]
            return w / p * math.exp(-max(d - p - t, 0) / kp)
        rules.append(atc)
    best = _edf(jobs, m)
    for pr in rules:
        c, out = _dispatch(jobs, m, pr)
        if best is None or c < best[0]:
            best = (c, out)
    return best



def _perm_sa(jobs, m, budget=0.7, seed=1, win=6, tfac=0.1, pswap=0.3, kick=0, klen=8, pblock=0.2, init=None, t0=None):
    if t0 is None: t0 = time.perf_counter()
    rnd = random.Random(seed)
    n = len(jobs)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    if init is None:
        best_c, out = dispatch_best(jobs, m)
        pi = [j for j, k, s in out]
    else:
        out = init; best_c = sum(W[j] * max(0, s + P[j] - D[j]) for j, k, s in out)
        pi = [j for j, k, s in sorted(out, key=lambda x: (x[2], x[1]))]
    hrep = heapq.heapreplace

    # S[i]: heap array of machine free times before position i; C[i]: cost of pi[:i]
    def build(pi):
        fr = [0] * m; c = 0; S = [list(fr)]; C = [0]
        for j in pi:
            f = fr[0]
            e = (f if f > R[j] else R[j]) + P[j]
            if e > D[j]: c += W[j] * (e - D[j])
            hrep(fr, e); S.append(list(fr)); C.append(c)
        return S, C

    S, C = build(pi)
    cur = C[n]

    def ev(pi, frm, to):
        fr = list(S[frm]); c = C[frm]
        for idx in range(frm, n):
            j = pi[idx]
            f = fr[0]
            e = (f if f > R[j] else R[j]) + P[j]
            if e > D[j]: c += W[j] * (e - D[j])
            hrep(fr, e)
            if idx >= to and fr == S[idx + 1]:
                return c + cur - C[idx + 1]
        return c

    def commit(pi, frm, to, delta):
        fr = list(S[frm]); c = C[frm]
        for idx in range(frm, n):
            j = pi[idx]
            f = fr[0]
            e = (f if f > R[j] else R[j]) + P[j]
            if e > D[j]: c += W[j] * (e - D[j])
            hrep(fr, e)
            if idx >= to and fr == S[idx + 1]:
                if delta:
                    for q in range(idx + 1, n + 1): C[q] += delta
                return
            S[idx + 1] = list(fr); C[idx + 1] = c

    best = cur; bpi = list(pi)
    T0 = max(1.0, cur / n) * tfac + 1e-9
    deadline = t0 + budget
    it = 0; T = T0; last = 0
    while True:
        it += 1
        if (it & 63) == 0:
            now = time.perf_counter()
            if now > deadline: break
            T = T0 * (1 - (now - t0) / budget) + 1e-9
            if kick and it - last > kick:
                # restart descent from a perturbed copy of the best
                pi = list(bpi); a = rnd.randrange(n - klen); seg = pi[a:a + klen]; rnd.shuffle(seg)
                pi[a:a + klen] = seg
                S, C = build(pi); cur = C[n]; last = it
        i = rnd.randrange(n); k = i + rnd.randint(-win, win)
        if k < 0 or k >= n or k == i: continue
        npi = list(pi)
        u = rnd.random()
        if pblock and u < pblock:
            L = rnd.randint(2, 3)
            if i + L > n or k + L > n: continue
            blk = npi[i:i + L]; del npi[i:i + L]; npi[k:k] = blk
            frm = min(i, k); to = max(i, k) + L - 1
        elif pswap and u < pblock + pswap:
            npi[i], npi[k] = npi[k], npi[i]
        else:
            j = npi.pop(i); npi.insert(k, j)
        if not (pblock and u < pblock):
            frm = min(i, k); to = max(i, k)
        c = ev(npi, frm, to)
        d = c - cur
        if d <= 0 or (tfac > 0 and rnd.random() < math.exp(-d / T)):
            pi = npi
            commit(pi, frm, to, d)
            cur = c
            if d < 0: last = it
            if cur < best: best = cur; bpi = list(pi)
    fr = [(0, k) for k in range(m)]; res = []
    for j in bpi:
        f, k = heapq.heappop(fr); s = f if f > R[j] else R[j]
        res.append((j, k, s)); heapq.heappush(fr, (s + P[j], k))
    if best > best_c:
        return out
    return res

def _mach_sa(jobs, m, budget=0.7, seed=1, tfac=0.5, init=None, t0=None, ptail=0.15):
    if t0 is None: t0 = time.perf_counter()
    rnd = random.Random(seed)
    n = len(jobs)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    if init is None:
        best_c, out = dispatch_best(jobs, m)
    else:
        out = init; best_c = sum(W[j] * max(0, s + P[j] - D[j]) for j, k, s in out)
    seqs = [[] for _ in range(m)]
    for j, k, s in sorted(out, key=lambda x: x[2]):
        seqs[k].append(j)
    E = [None] * m; C = [None] * m

    def rebuild(k):
        seq = seqs[k]; e = []; c = []; t = 0; cc = 0
        for j in seq:
            s = t if t > R[j] else R[j]
            t = s + P[j]
            if t > D[j]: cc += W[j] * (t - D[j])
            e.append(t); c.append(cc)
        E[k] = e; C[k] = c

    for k in range(m): rebuild(k)

    def evalm(k, s, mid, q):
        # cost of seqs[k][:s] + mid + seqs[k][q:]
        seq = seqs[k]; e = E[k]; c = C[k]
        if s > 0:
            t = e[s - 1]; cc = c[s - 1]
        else:
            t = 0; cc = 0
        for j in mid:
            st = t if t > R[j] else R[j]
            t = st + P[j]
            if t > D[j]: cc += W[j] * (t - D[j])
        L = len(seq); i = q
        while i < L:
            j = seq[i]
            st = t if t > R[j] else R[j]
            t2 = st + P[j]
            if t2 == e[i]:
                return cc + c[L - 1] - (c[i - 1] if i > 0 else 0)
            t = t2
            if t > D[j]: cc += W[j] * (t - D[j])
            i += 1
        return cc

    mc = [C[k][-1] if C[k] else 0 for k in range(m)]
    cur = sum(mc)
    T0 = max(1.0, cur / max(1, n)) * tfac + 1e-9
    it = 0
    best = cur; best_seqs = [list(s) for s in seqs]
    deadline = t0 + budget
    T = T0
    while True:
        it += 1
        if (it & 255) == 0:
            now = time.perf_counter()
            if now > deadline: break
            frac = (now - t0) / budget
            T = T0 * (1 - frac) + 1e-3
        a = rnd.randrange(m)
        la = len(seqs[a])
        if la == 0: continue
        i = rnd.randrange(la)
        j = seqs[a][i]
        mv = rnd.random()
        if mv < ptail:
            b = rnd.randrange(m)
            if b == a or i == 0: continue
            lb = len(seqs[b])
            eb = E[b]; tj = E[a][i - 1]
            lo, hi = 0, lb
            while lo < hi:
                md = (lo + hi) // 2
                if eb[md] < tj: lo = md + 1
                else: hi = md
            k2 = lo + 1 + rnd.randint(-1, 1)
            if k2 < 0: k2 = 0
            if k2 > lb: k2 = lb
            ta = seqs[a][i:]; tb = seqs[b][k2:]
            na = evalm(a, i, tb, la)
            nb = evalm(b, k2, ta, lb)
            delta = na + nb - mc[a] - mc[b]
            if delta <= 0 or rnd.random() < math.exp(-delta / T):
                seqs[a][i:] = tb; seqs[b][k2:] = ta; rebuild(a); rebuild(b)
                mc[a] = na; mc[b] = nb; cur += delta
        elif mv < 0.5 + ptail / 2:
            # relocate j to machine b near position
            b = rnd.randrange(m)
            if b == a:
                k2 = i + rnd.randint(-6, 6)
                if k2 < 0 or k2 >= la or k2 == i: continue
                if k2 > i:
                    mid = seqs[a][i + 1:k2 + 1] + [j]; s0, q0 = i, k2 + 1
                else:
                    mid = [j] + seqs[a][k2:i]; s0, q0 = k2, i + 1
                na = evalm(a, s0, mid, q0)
                delta = na - mc[a]
                if delta <= 0 or rnd.random() < math.exp(-delta / T):
                    seqs[a][s0:q0] = mid; rebuild(a); mc[a] = na; cur += delta
            else:
                lb = len(seqs[b])
                # find position in b by end-time near j's current end
                eb = E[b]; tj = E[a][i]
                lo, hi = 0, lb
                while lo < hi:
                    md = (lo + hi) // 2
                    if eb[md] < tj: lo = md + 1
                    else: hi = md
                k2 = lo + rnd.randint(-3, 3)
                if k2 < 0: k2 = 0
                if k2 > lb: k2 = lb
                na = evalm(a, i, [], i + 1)
                nb = evalm(b, k2, [j], k2)
                delta = na + nb - mc[a] - mc[b]
                if delta <= 0 or rnd.random() < math.exp(-delta / T):
                    del seqs[a][i]; seqs[b].insert(k2, j); rebuild(a); rebuild(b)
                    mc[a] = na; mc[b] = nb; cur += delta
        else:
            b = rnd.randrange(m)
            lb = len(seqs[b])
            if lb == 0: continue
            if b == a:
                k2 = i + rnd.randint(-4, 4)
                if k2 < 0 or k2 >= la or k2 == i: continue
                x, y = min(i, k2), max(i, k2)
                mid = seqs[a][x:y + 1]; mid[0], mid[-1] = mid[-1], mid[0]
                na = evalm(a, x, mid, y + 1)
                delta = na - mc[a]
                if delta <= 0 or rnd.random() < math.exp(-delta / T):
                    seqs[a][x:y + 1] = mid; rebuild(a); mc[a] = na; cur += delta
            else:
                eb = E[b]; tj = E[a][i]
                lo, hi = 0, lb
                while lo < hi:
                    md = (lo + hi) // 2
                    if eb[md] < tj: lo = md + 1
                    else: hi = md
                k2 = lo + rnd.randint(-2, 2)
                if k2 < 0: k2 = 0
                if k2 >= lb: k2 = lb - 1
                j2 = seqs[b][k2]
                na = evalm(a, i, [j2], i + 1)
                nb = evalm(b, k2, [j], k2 + 1)
                delta = na + nb - mc[a] - mc[b]
                if delta <= 0 or rnd.random() < math.exp(-delta / T):
                    seqs[a][i] = j2; seqs[b][k2] = j; rebuild(a); rebuild(b)
                    mc[a] = na; mc[b] = nb; cur += delta
        if cur < best:
            best = cur; best_seqs = [list(s) for s in seqs]
    res = []
    for k in range(m):
        t = 0
        for j in best_seqs[k]:
            s = t if t > R[j] else R[j]
            res.append((j, k, s)); t = s + P[j]
    if best > best_c:
        return out
    return res

def _win_dp(jobs, m, init, budget=0.7, t0=None, L=8):
    # Exact-ish reorder of L consecutive jobs on one machine (subset DP), kept only if the
    # machine's true cost drops.
    if t0 is None: t0 = time.perf_counter()
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    seqs = [[] for _ in range(m)]
    for j, k, s in sorted(init, key=lambda x: x[2]):
        seqs[k].append(j)

    def mcost(seq):
        t = 0; c = 0
        for j in seq:
            t = (t if t > R[j] else R[j]) + P[j]
            if t > D[j]: c += W[j] * (t - D[j])
        return c

    INF = float("inf")
    improved = True
    while improved and time.perf_counter() - t0 < budget:
        improved = False
        for k in range(m):
            seq = seqs[k]
            base = mcost(seq)
            a = 0
            while a < len(seq) - 1:
                if time.perf_counter() - t0 > budget: break
                win = seq[a:a + L]; l = len(win)
                t = 0
                for j in seq[:a]:
                    t = (t if t > R[j] else R[j]) + P[j]
                N = 1 << l
                cost = [INF] * N; end = [0] * N; last = [-1] * N
                cost[0] = 0; end[0] = t
                for S in range(N):
                    cs = cost[S]
                    if cs == INF: continue
                    es = end[S]
                    for b in range(l):
                        bit = 1 << b
                        if S & bit: continue
                        j = win[b]
                        e = (es if es > R[j] else R[j]) + P[j]
                        c = cs + (W[j] * (e - D[j]) if e > D[j] else 0)
                        T = S | bit
                        if c < cost[T] or (c == cost[T] and e < end[T]):
                            cost[T] = c; end[T] = e; last[T] = b
                order = []; S = N - 1
                while S:
                    b = last[S]; order.append(win[b]); S ^= 1 << b
                order.reverse()
                if order != win:
                    cand = seq[:a] + order + seq[a + l:]
                    cc = mcost(cand)
                    if cc < base:
                        seqs[k] = seq = cand; base = cc; improved = True
                a += max(1, L // 2)
    res = []
    for k in range(m):
        t = 0
        for j in seqs[k]:
            s = t if t > R[j] else R[j]
            res.append((j, k, s)); t = s + P[j]
    return res


def _cost(jobs, out):
    return sum(jobs[j][3] * max(0, s + jobs[j][1] - jobs[j][2]) for j, k, s in out)


def schedule(jobs, m):
    t0 = time.perf_counter()
    o = _mach_sa(jobs, m, budget=0.3, t0=t0)
    o = _perm_sa(jobs, m, budget=0.62, init=o, t0=t0)
    o2 = _win_dp(jobs, m, o, budget=0.7, t0=t0)
    return o2 if _cost(jobs, o2) <= _cost(jobs, o) else o
