import bisect, heapq, math, random, time

LIMIT = 0.6


def dispatch(jobs, m, keyf):
    n = len(jobs)
    order = sorted(range(n), key=lambda j: jobs[j][0])
    free = [(0, k) for k in range(m)]
    ready, out, i, tot, now = [], [], 0, 0, 0
    while len(out) < n:
        t, k = heapq.heappop(free)
        t = max(t, now)
        if not ready and jobs[order[i]][0] > t:
            t = jobs[order[i]][0]
        while i < n and jobs[order[i]][0] <= t:
            ready.append(order[i]); i += 1
        now = t
        b = min(ready, key=lambda j: keyf(j, t))
        ready.remove(b)
        r, p, d, w = jobs[b]
        out.append((b, k, t))
        tot += w * max(0, t + p - d)
        heapq.heappush(free, (t + p, k))
    return tot, out


def schedule(jobs, m):
    t0 = time.time()
    n = len(jobs)
    pbar = sum(j[1] for j in jobs) / n
    rules = [lambda j, t: (jobs[j][2], j), lambda j, t: -jobs[j][3] / jobs[j][1]]
    for K in (0.5, 1, 2, 3, 5):
        rules.append(lambda j, t, K=K: -jobs[j][3] / jobs[j][1] * math.exp(-max(0, jobs[j][2] - jobs[j][1] - t) / (K * pbar)))
    best_c, best_out = min((dispatch(jobs, m, f) for f in rules), key=lambda x: x[0])
    if best_c == 0:
        return best_out
    seq = [j for j, k, s in sorted(best_out, key=lambda x: (x[2], x[0]))]
    R = [j[0] for j in jobs]; P = [j[1] for j in jobs]; D = [j[2] for j in jobs]; Wt = [j[3] for j in jobs]
    ins = bisect.insort

    # pre[i] = sorted machine free times before position i; pc[i] = cost of seq[:i]; late[i] flag
    pre = [None] * (n + 1); pc = [0] * (n + 1); late = [False] * n

    def rebuild(i, hi=n):
        free = pre[i][:]; c = pc[i]
        for x in range(i, n):
            j = seq[x]
            f = free.pop(0)
            e = (f if f > R[j] else R[j]) + P[j]
            ins(free, e)
            if e > D[j]:
                c += Wt[j] * (e - D[j]); late[x] = True
            else:
                late[x] = False
            if x >= hi and free == pre[x + 1]:
                dl = c - pc[x + 1]
                if dl:
                    for y in range(x + 1, n + 1):
                        pc[y] += dl
                return
            pre[x + 1] = free[:]; pc[x + 1] = c

    def trial(lo, hi):
        """Cost of seq after a change confined to positions lo..hi; stop once the state rejoins."""
        free = pre[lo][:]; c = pc[lo]
        for x in range(lo, n):
            j = seq[x]
            f = free.pop(0)
            e = (f if f > R[j] else R[j]) + P[j]
            ins(free, e)
            if e > D[j]:
                c += Wt[j] * (e - D[j])
            if x >= hi and free == pre[x + 1]:
                return c + pc[n] - pc[x + 1]
        return c

    pre[0] = [0] * m
    rebuild(0)
    cur = pc[n]
    best, best_seq = cur, seq[:]
    rnd = random.Random(1)
    W = 3 * m
    T0 = max(1.0, min(0.006 * cur, 0.5 * pbar * sum(Wt) / n))
    it = 0
    T = T0
    while True:
        it += 1
        if it & 63 == 0:
            el = time.time() - t0
            if el > LIMIT or best == 0:
                break
            T = T0 * (1 - el / LIMIT) ** 2 + 1e-9
        a = rnd.randrange(n)
        if it & 1:
            b = min(n - 1, max(0, a + rnd.randint(-W, W)))
        else:
            for _ in range(8):
                if late[a]:
                    break
                a = rnd.randrange(n)
            b = max(0, a - rnd.randint(1, W))
        if a == b:
            continue
        mv = rnd.random()
        if mv < 0.1:
            b = rnd.randrange(n)
            if a == b:
                continue
        sw = mv > 0.7
        if sw:
            seq[a], seq[b] = seq[b], seq[a]
        else:
            x = seq.pop(a); seq.insert(b, x)
        lo, hi = (a, b) if a < b else (b, a)
        c = trial(lo, hi)
        if c <= cur or rnd.random() < math.exp((cur - c) / T):
            cur = c
            rebuild(lo, hi)
            if c < best:
                best, best_seq = c, seq[:]
        elif sw:
            seq[a], seq[b] = seq[b], seq[a]
        else:
            x = seq.pop(b); seq.insert(a, x)
    if best > best_c:
        return best_out
    free = [0] * m; out = []
    for j in best_seq:
        k = free.index(min(free)); s = max(free[k], R[j]); free[k] = s + P[j]
        out.append((j, k, s))
    return out
