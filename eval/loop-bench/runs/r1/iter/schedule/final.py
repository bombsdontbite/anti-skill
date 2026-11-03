import heapq, math, random, time, bisect
from bisect import bisect_right, insort



def decode_full(order, R, P, D, W, m):
    """List-schedule `order`: each job to the machine where it starts earliest (best fit).
    Returns states (sorted free times before each position), prefix costs, total."""
    F = [0] * m
    states = []
    pc = []
    c = 0
    for j in order:
        states.append(list(F))
        pc.append(c)
        r = R[j]
        if F[0] <= r:
            idx = bisect_right(F, r) - 1
            t = r + P[j]
        else:
            idx = 0
            t = F[0] + P[j]
        del F[idx]
        insort(F, t)
        if t > D[j]:
            c += W[j] * (t - D[j])
    states.append(list(F))
    pc.append(c)
    return states, pc, c


def assign(order, R, P, m):
    F = [(0, k) for k in range(m)]
    seqs = [[] for _ in range(m)]
    for j in order:
        r = R[j]
        # machine with earliest start; tie -> latest free time
        best = None
        for idx, (f, k) in enumerate(F):
            s = f if f > r else r
            key = (s, -f)
            if best is None or key < best[0]:
                best = (key, idx)
        idx = best[1]
        f, k = F[idx]
        s = f if f > r else r
        F[idx] = (s + P[j], k)
        seqs[k].append(j)
    return seqs


def perm_search(order, R, P, D, W, m, deadline, rng, T0, Tend, WIN, PINS, KSTAG=0, KL=8, PFAR=0.0, SLACK=-1.0):
    n = len(order)
    order = list(order)
    states, pc, cur = decode_full(order, R, P, D, W, m)
    best = cur
    bestorder = list(order)
    rnd = rng.random
    ri = rng.randrange
    br = bisect_right
    ins_ = insort
    log = math.log
    tstart = time.time()
    span = max(1e-6, deadline - tstart)
    T = T0
    it = 0
    lastimp = 0
    slk = SLACK * cur / n if SLACK >= 0 else 1e300
    while True:
        it += 1
        if (it & 31) == 0:
            now = time.time()
            if now >= deadline:
                break
            T = T0 * (Tend / T0) ** ((now - tstart) / span)
            if best == 0:
                break
            if KSTAG and it - lastimp > KSTAG:
                lastimp = it
                order = list(bestorder)
                a0 = ri(max(1, n - KL))
                L0 = ri(3, KL + 1)
                segk = order[a0:a0 + L0]
                rng.shuffle(segk)
                order[a0:a0 + L0] = segk
                states, pc, cur = decode_full(order, R, P, D, W, m)
                if cur < best:
                    best = cur
                    bestorder = list(order)
        if rnd() < PFAR:
            i = int(rnd() * n)
            k = int(rnd() * n)
            if i == k:
                continue
            if k < i:
                i, k = k, i
            ins = True
        else:
            i = int(rnd() * n)
            k = i + 1 + int(rnd() * WIN)
            if k >= n:
                continue
            ins = rnd() < PINS
        if ins:
            if rnd() < 0.5:
                # move job at i to position k (later)
                seg = order[i + 1:k + 1] + [order[i]]
            else:
                # move job at k to position i (earlier)
                seg = [order[k]] + order[i:k]
        else:
            seg = [order[k]] + order[i + 1:k] + [order[i]]
        thr = -T * log(rnd() + 1e-300)
        F = list(states[i])
        c = pc[i]
        for j in seg:
            r = R[j]
            if F[0] <= r:
                idx = br(F, r) - 1
                t = r + P[j]
            else:
                idx = 0
                t = F[0] + P[j]
            del F[idx]
            ins_(F, t)
            if t > D[j]:
                c += W[j] * (t - D[j])
        p = k + 1
        lim = cur + thr
        lim2 = thr + slk
        ok = True
        if F == states[p]:
            c += cur - pc[p]
        else:
            while p < n:
                if c > lim or c - pc[p] > lim2:
                    ok = False
                    break
                j = order[p]
                r = R[j]
                if F[0] <= r:
                    idx = br(F, r) - 1
                    t = r + P[j]
                else:
                    idx = 0
                    t = F[0] + P[j]
                del F[idx]
                ins_(F, t)
                if t > D[j]:
                    c += W[j] * (t - D[j])
                p += 1
                if F == states[p]:
                    c += cur - pc[p]
                    break
        if not ok or c > lim:
            continue
        order[i:k + 1] = seg
        # rebuild states from i
        F = list(states[i])
        cc = pc[i]
        q = i
        while q < n:
            j = order[q]
            r = R[j]
            if F[0] <= r:
                idx = br(F, r) - 1
                t = r + P[j]
            else:
                idx = 0
                t = F[0] + P[j]
            del F[idx]
            ins_(F, t)
            if t > D[j]:
                cc += W[j] * (t - D[j])
            q += 1
            if q > k and F == states[q]:
                off = cc - pc[q]
                if off:
                    for z in range(q, n + 1):
                        pc[z] += off
                break
            states[q] = list(F)
            pc[q] = cc
        cur = c
        if cur < best:
            best = cur
            bestorder = list(order)
            lastimp = it
    return bestorder, best, it

TIME_LIMIT = 0.8
T0F = 0.3
TENDF = 1e-3
WIN = 2
PFAR = 0.1
PHOT = 0.8
PX = 0.0
NC = 1
FP = 0.7
PT0F = 0.15
PWIN = 6
PPFAR = 0.0
SLACK = 0.5
KS = [float(x) for x in "0.2,0.5,1,2,3,5".split(",")]
Q1 = PX + 0.1
Q2 = Q1 + 0.4
Q3 = Q2 + 0.1


def _dispatch(jobs, m, rule, K, pbar):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: jobs[j][0])
    free = [(0, k) for k in range(m)]
    ready = []
    seqs = [[] for _ in range(m)]
    i = 0
    done = 0
    while done < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i])
            i += 1
        best = -1
        bv = None
        for idx, j in enumerate(ready):
            r, p, d, w = jobs[j]
            if rule == 0:
                v = -d
            else:
                sl = d - p - t
                if sl < 0:
                    sl = 0
                v = w / (p if p > 0 else 0.5) * math.exp(-sl / (K * pbar))
            if bv is None or v > bv:
                bv = v
                best = idx
        j = ready[best]
        ready[best] = ready[-1]
        ready.pop()
        seqs[k].append(j)
        done += 1
        heapq.heappush(free, (max(t, jobs[j][0]) + jobs[j][1], k))
    return seqs


def _order(seqs, R, P):
    # global dispatch order: by start time on the semi-active per-machine schedule
    ev = []
    for q in seqs:
        t = 0
        for j in q:
            if R[j] > t:
                t = R[j]
            ev.append((t, j))
            t += P[j]
    ev.sort()
    return [j for _, j in ev]


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    if n == 0:
        return []
    R = [j[0] for j in jobs]
    P = [j[1] for j in jobs]
    D = [j[2] for j in jobs]
    W = [j[3] for j in jobs]
    pbar = max(1.0, sum(P) / n)

    def mcost(seq):
        t = 0
        c = 0
        for j in seq:
            r = R[j]
            if r > t:
                t = r
            t += P[j]
            if t > D[j]:
                c += W[j] * (t - D[j])
        return c

    def prof(seq):
        comp = []
        pc = []
        t = 0
        c = 0
        for j in seq:
            r = R[j]
            if r > t:
                t = r
            t += P[j]
            if t > D[j]:
                c += W[j] * (t - D[j])
            comp.append(t)
            pc.append(c)
        return comp, pc

    cands = []
    for rule, K in [(0, 1)] + [(1, K) for K in KS]:
        s = _dispatch(jobs, m, rule, K, pbar)
        o = _order(s, R, P)
        c = decode_full(o, R, P, D, W, m)[2]
        cands.append((c, o))
    cands.sort(key=lambda x: x[0])
    c0, o = cands[0]
    prng = random.Random(1)
    PT0 = max(1.0, c0 / n * PT0F)
    order, pbest, _ = perm_search(o, R, P, D, W, m, t0 + TIME_LIMIT * FP, prng, PT0, PT0 * 1e-3, PWIN, 0.5, 0, 8, PPFAR, SLACK)
    best = assign(order, R, P, m)
    seqs = [list(q) for q in best]
    COMP = []
    PC = []
    for q in seqs:
        a, b = prof(q)
        COMP.append(a)
        PC.append(b)
    costs = [PC[k][-1] if PC[k] else 0 for k in range(m)]
    cur = sum(costs)
    bestc = cur
    bestseqs = [list(q) for q in seqs]
    rng = random.Random(12345)
    T0 = max(1.0, cur / n * T0F)
    Tend = T0 * TENDF
    T = T0
    it = 0
    lastcyc = 0
    hot = []
    nh = 0
    deadline = t0 + TIME_LIMIT
    tstart = time.time()
    span = deadline - tstart
    rnd = rng.random
    ri = rng.randrange
    exp = math.exp
    log = math.log

    def tail(seq, comp, pc, tot, s, t, c):
        # continue old seq from position s with current time t and cost c
        L = len(seq)
        while s < L:
            j = seq[s]
            r = R[j]
            if r > t:
                t = r
            t += P[j]
            if t > D[j]:
                c += W[j] * (t - D[j])
            if t == comp[s]:
                return c + tot - pc[s]
            s += 1
        return c

    def step(j, t, c):
        r = R[j]
        if r > t:
            t = r
        t += P[j]
        if t > D[j]:
            c += W[j] * (t - D[j])
        return t, c

    while True:
        it += 1
        if (it & 127) == 0:
            now = time.time()
            if now >= deadline:
                break
            fr = (now - tstart) / span * NC
            cyc = int(fr)
            if cyc != lastcyc:
                lastcyc = cyc
                seqs = [list(q) for q in bestseqs]
                COMP = []
                PC = []
                for q in seqs:
                    x, y = prof(q)
                    COMP.append(x)
                    PC.append(y)
                costs = [PC[k][-1] if PC[k] else 0 for k in range(m)]
                cur = sum(costs)
            T = T0 * (Tend / T0) ** (fr - cyc)
            if bestc == 0:
                break
        if (it & 511) == 1:
            hot = []
            for kk in range(m):
                q = seqs[kk]
                cq = COMP[kk]
                bs = 0
                last = -1
                for p in range(len(q)):
                    j = q[p]
                    if p and cq[p] - P[j] > cq[p - 1]:
                        if last >= 0:
                            hot.extend((kk, x) for x in range(bs, last + 1))
                        bs = p
                        last = -1
                    if cq[p] > D[j]:
                        last = p
                if last >= 0:
                    hot.extend((kk, x) for x in range(bs, last + 1))
            nh = len(hot)
        if nh and rnd() < PHOT:
            a, i = hot[ri(nh)]
            sa = seqs[a]
            La = len(sa)
            if i >= La:
                continue
        else:
            a = ri(m)
            sa = seqs[a]
            La = len(sa)
            if not La:
                continue
            i = ri(La)
        mv = rnd()
        if m == 1 or (Q1 > mv >= PX) or (Q2 <= mv < Q3):
            b = a
        else:
            b = ri(m - 1)
            if b >= a:
                b += 1
        thr = -T * log(rnd() + 1e-300)
        ca = COMP[a]
        pa = PC[a]
        if mv < PX:
            if a == b:
                continue
            sb = seqs[b]
            Lb = len(sb)
            k = bisect.bisect_left(COMP[b], ca[i] - P[sa[i]]) + ri(-1, 2)
            if k < 0 or k > Lb:
                continue
            na_ = sa[:i] + sb[k:]
            nb_ = sb[:k] + sa[i:]
            t = ca[i - 1] if i else 0
            c = pa[i - 1] if i else 0
            for jj in sb[k:]:
                r = R[jj]
                if r > t:
                    t = r
                t += P[jj]
                if t > D[jj]:
                    c += W[jj] * (t - D[jj])
            na = c
            cbm = COMP[b]
            pbm = PC[b]
            t = cbm[k - 1] if k else 0
            c = pbm[k - 1] if k else 0
            for jj in sa[i:]:
                r = R[jj]
                if r > t:
                    t = r
                t += P[jj]
                if t > D[jj]:
                    c += W[jj] * (t - D[jj])
            nb = c
            delta = na + nb - costs[a] - costs[b]
            if delta <= thr:
                seqs[a] = na_
                seqs[b] = nb_
                COMP[a], PC[a] = prof(na_)
                COMP[b], PC[b] = prof(nb_)
                costs[a] = na
                costs[b] = nb
                cur += delta
        elif mv < Q2:
            j = sa[i]
            if a == b:
                if La < 2:
                    continue
                if rnd() < PFAR:
                    k = ri(La - 1)
                    if k >= i:
                        k += 1
                else:
                    k = i + ri(1, WIN + 1) * (1 if rnd() < 0.5 else -1)
                    if k < 0 or k >= La:
                        continue
                # remove i, insert so that j ends at index k
                if i < k:
                    t = ca[i - 1] if i else 0
                    c = pa[i - 1] if i else 0
                    for p in range(i + 1, k + 1):
                        t, c = step(sa[p], t, c)
                    t, c = step(j, t, c)
                    nc = tail(sa, ca, pa, costs[a], k + 1, t, c) if (k + 1 < La and t != ca[k]) else (c + costs[a] - pa[k])
                else:
                    t = ca[k - 1] if k else 0
                    c = pa[k - 1] if k else 0
                    t, c = step(j, t, c)
                    for p in range(k, i):
                        t, c = step(sa[p], t, c)
                    nc = tail(sa, ca, pa, costs[a], i + 1, t, c) if (i + 1 < La and t != ca[i]) else (c + costs[a] - pa[i])
                delta = nc - costs[a]
                if delta <= thr:
                    del sa[i]
                    sa.insert(k, j)
                    COMP[a], PC[a] = prof(sa)
                    costs[a] = nc
                    cur += delta
            else:
                sb = seqs[b]
                Lb = len(sb)
                if rnd() < PFAR:
                    k = ri(Lb + 1)
                else:
                    k = bisect.bisect_left(COMP[b], ca[i]) + ri(-WIN, WIN + 1)
                    if k < 0 or k > Lb:
                        continue
                # removal from a
                if i + 1 < La:
                    t = ca[i - 1] if i else 0
                    c = pa[i - 1] if i else 0
                    na = tail(sa, ca, pa, costs[a], i + 1, t, c)
                else:
                    na = pa[i - 1] if i else 0
                cbm = COMP[b]
                pbm = PC[b]
                t = cbm[k - 1] if k else 0
                c = pbm[k - 1] if k else 0
                r = R[j]
                if r > t:
                    t = r
                t += P[j]
                if t > D[j]:
                    c += W[j] * (t - D[j])
                lim = thr - na + costs[a]
                cb0 = costs[b]
                if c - (pbm[k - 1] if k else 0) > lim:
                    continue
                p = k
                ok = True
                while p < Lb:
                    jj = sb[p]
                    r = R[jj]
                    if r > t:
                        t = r
                    t += P[jj]
                    if t > D[jj]:
                        c += W[jj] * (t - D[jj])
                    if t == cbm[p]:
                        c += cb0 - pbm[p]
                        break
                    if c - pbm[p] > lim:
                        ok = False
                        break
                    p += 1
                if not ok:
                    continue
                nb = c
                delta = na + nb - costs[a] - costs[b]
                if delta <= thr:
                    del sa[i]
                    sb.insert(k, j)
                    COMP[a], PC[a] = prof(sa)
                    COMP[b], PC[b] = prof(sb)
                    costs[a] = na
                    costs[b] = nb
                    cur += delta
        else:
            if a == b:
                if La < 2:
                    continue
                if rnd() < PFAR:
                    k = ri(La - 1)
                    if k >= i:
                        k += 1
                else:
                    k = i + ri(1, WIN + 1) * (1 if rnd() < 0.5 else -1)
                    if k < 0 or k >= La:
                        continue
                if k < i:
                    i, k = k, i
                t = ca[i - 1] if i else 0
                c = pa[i - 1] if i else 0
                t, c = step(sa[k], t, c)
                for p in range(i + 1, k):
                    t, c = step(sa[p], t, c)
                t, c = step(sa[i], t, c)
                nc = tail(sa, ca, pa, costs[a], k + 1, t, c) if (k + 1 < La and t != ca[k]) else (c + costs[a] - pa[k])
                delta = nc - costs[a]
                if delta <= thr:
                    sa[i], sa[k] = sa[k], sa[i]
                    COMP[a], PC[a] = prof(sa)
                    costs[a] = nc
                    cur += delta
            else:
                sb = seqs[b]
                Lb = len(sb)
                if not Lb:
                    continue
                if rnd() < PFAR:
                    k = ri(Lb)
                else:
                    k = bisect.bisect_left(COMP[b], ca[i]) + ri(-WIN, WIN + 1)
                    if k < 0 or k >= Lb:
                        continue
                ja = sa[i]
                jb = sb[k]
                t = ca[i - 1] if i else 0
                c = pa[i - 1] if i else 0
                t, c = step(jb, t, c)
                na = tail(sa, ca, pa, costs[a], i + 1, t, c) if (i + 1 < La and t != ca[i]) else (c + costs[a] - pa[i])
                cbm = COMP[b]
                pbm = PC[b]
                t = cbm[k - 1] if k else 0
                c = pbm[k - 1] if k else 0
                t, c = step(ja, t, c)
                nb = tail(sb, cbm, pbm, costs[b], k + 1, t, c) if (k + 1 < Lb and t != cbm[k]) else (c + costs[b] - pbm[k])
                delta = na + nb - costs[a] - costs[b]
                if delta <= thr:
                    sa[i] = jb
                    sb[k] = ja
                    COMP[a], PC[a] = prof(sa)
                    COMP[b], PC[b] = prof(sb)
                    costs[a] = na
                    costs[b] = nb
                    cur += delta
        if cur < bestc:
            bestc = cur
            bestseqs = [list(q) for q in seqs]
    out = []
    for k, q in enumerate(bestseqs):
        t = 0
        for j in q:
            if R[j] > t:
                t = R[j]
            out.append((j, k, t))
            t += P[j]

    return out
