import heapq, math, random, time

TLIM = 0.8
WIN = 10
TF = 0.05
NST = 3


def _dispatch(jobs, m, key):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: jobs[j][0])
    free = [(0, k) for k in range(m)]
    ready, perm, i, tot = [], [], 0, 0
    while len(perm) < n:
        t, k = heapq.heappop(free)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        b = min(ready, key=lambda j: key(j, t))
        ready.remove(b)
        r, p, d, w = jobs[b]
        t = max(t, r)
        perm.append((t, b))
        tot += w * max(0, t + p - d)
        heapq.heappush(free, (t + p, k))
    perm.sort()
    return tot, [j for _, j in perm]


def _suffix(perm, lo, snaps, pc, R, P, D, W, store):
    h = list(snaps[lo]); c = pc[lo]
    hr = heapq.heapreplace
    for idx in range(lo, len(perm)):
        j = perm[idx]
        if store:
            h.sort(); snaps[idx] = tuple(h); pc[idx] = c
        t = h[0]; r = R[j]
        e = (t if t > r else r) + P[j]
        hr(h, e)
        if e > D[j]:
            c += W[j] * (e - D[j])
    return c


def _trial(perm, lo, hi, snaps, pc, R, P, D, W, cur, thr):
    # Cost of perm re-decoded from lo, or None once it provably exceeds thr: past the changed span,
    # a free-time vector that dominates the old one cannot finish cheaper than the old rest.
    h = list(snaps[lo]); c = pc[lo]
    hr = heapq.heapreplace
    n = len(perm); m = len(h)
    for idx in range(lo, n):
        if idx > hi and ((idx - hi) & 7) == 1:
            o = snaps[idx]; sh = sorted(h)
            if sh == list(o):
                return c + cur - pc[idx]
            if c + cur - pc[idx] > thr:
                for q in range(m):
                    if sh[q] < o[q]:
                        break
                else:
                    return None
        j = perm[idx]
        t = h[0]; r = R[j]
        e = (t if t > r else r) + P[j]
        hr(h, e)
        if e > D[j]:
            c += W[j] * (e - D[j])
    return c


def _sa(perm, m, R, P, D, W, tend, seed):
    n = len(perm)
    snaps = [None] * n; pc = [0] * n
    snaps[0] = tuple([0] * m)
    cur = _suffix(perm, 0, snaps, pc, R, P, D, W, True)
    bestc, bestp = cur, list(perm)
    rnd = random.Random(seed)
    tstart = time.time(); span = max(1e-3, tend - tstart)
    T0 = max(1.0, cur / n * TF)
    T = T0; it = 0; win = int(WIN)
    while True:
        if (it & 31) == 0:
            now = time.time()
            if now > tend or bestc == 0:
                break
            T = T0 * (1 - (now - tstart) / span) + 1e-9
        it += 1
        i = rnd.randrange(n)
        k = min(n - 1, max(0, i + rnd.randint(-win, win)))
        if k == i:
            continue
        lo = i if i < k else k
        if rnd.random() < 0.5:
            perm[i], perm[k] = perm[k], perm[i]; mv = 0
        else:
            j = perm.pop(i); perm.insert(k, j); mv = 1
        thr = cur - T * math.log(1.0 - rnd.random())
        nc = _trial(perm, lo, i + k - lo, snaps, pc, R, P, D, W, cur, thr)
        if nc is not None and nc <= thr:
            _suffix(perm, lo, snaps, pc, R, P, D, W, True)
            cur = nc
            if cur < bestc:
                bestc = cur; bestp = list(perm)
        elif mv == 0:
            perm[i], perm[k] = perm[k], perm[i]
        else:
            j = perm.pop(k); perm.insert(i, j)
    return bestc, bestp


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; W = [j[3] for j in jobs]
    pbar = sum(P) / n
    keys = [lambda j, t: (D[j], j), lambda j, t: max(P[j], D[j] - t) / W[j]]
    for kk in (0.5, 1.0, 2.0, 4.0):
        keys.append(lambda j, t, kk=kk: -(W[j] / P[j]) * math.exp(-max(0, D[j] - P[j] - t) / (kk * pbar)))
    starts = sorted((_dispatch(jobs, m, key) for key in keys), key=lambda x: x[0])
    nst = int(NST)
    tl = TLIM - (time.time() - t0)
    best = starts[0]
    for s in range(nst):
        res = _sa(list(starts[s][1]), m, R, P, D, W, time.time() + tl / (nst - s) - 0.0, s + 1)
        tl = TLIM - (time.time() - t0)
        if res[0] < best[0]:
            best = res
    free = [(0, k) for k in range(m)]; out = []
    for j in best[1]:
        t, k = heapq.heappop(free)
        s = max(t, R[j]); out.append((j, k, s)); heapq.heappush(free, (s + P[j], k))
    return out
