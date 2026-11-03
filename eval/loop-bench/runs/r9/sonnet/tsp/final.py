import math
import random
import time

TIME = 0.5
K = 10
EPS = 1e-9
THR = 0.5
MAXIT = 0
LAST_IT = [0]
MAXSEG = 50
PSPAT = 0.5
SEED = 12345
QN = 2


def solve(points):
    t_start = time.perf_counter()
    n = len(points)
    if n <= 3:
        return list(range(n))
    D = [[math.dist(p, q) for q in points] for p in points]
    mx = max(max(r) for r in D)
    EPS = 1e-12 * mx if mx > 0 else 1e-12
    K_ = min(K, n - 1)
    neigh = []
    for i in range(n):
        row = D[i]
        order = sorted(range(n), key=lambda j: row[j])
        base = [j for j in order if j != i]
        chosen = base[:K_]
        if QN:
            px, py = points[i]
            cnt = [0, 0, 0, 0]
            extra = []
            for j in base:
                qx, qy = points[j]
                qd = (1 if qx >= px else 0) + (2 if qy >= py else 0)
                if cnt[qd] < QN:
                    cnt[qd] += 1
                    if j not in chosen:
                        extra.append(j)
                if sum(cnt) >= 4 * QN:
                    break
            chosen = chosen + extra
            chosen.sort(key=lambda j: row[j])
        neigh.append(chosen)

    # nearest neighbour start
    left = set(range(1, n))
    tour = [0]
    while left:
        row = D[tour[-1]]
        nxt = min(left, key=lambda j: (row[j], j))
        left.remove(nxt)
        tour.append(nxt)
    pos = [0] * n
    for i, c in enumerate(tour):
        pos[c] = i

    def reverse(i, j):
        inner = (j - i) % n + 1
        if inner * 2 > n:
            i, j = (j + 1) % n, (i - 1) % n
            inner = n - inner
        for _ in range(inner // 2):
            a = tour[i]
            b = tour[j]
            tour[i] = b
            pos[b] = i
            tour[j] = a
            pos[a] = j
            i += 1
            if i == n:
                i = 0
            j -= 1
            if j < 0:
                j = n - 1

    def improve(a):
        """Try one improving move around city a; return (gain, touched) or None."""
        row = D[a]
        pa = pos[a]
        # 2-opt, successor side
        b = tour[(pa + 1) % n]
        dab = row[b]
        for c in neigh[a]:
            dac = row[c]
            if dac >= dab:
                break
            d = tour[(pos[c] + 1) % n]
            if c == b or d == a:
                continue
            delta = dab + D[c][d] - dac - D[b][d]
            if delta > EPS:
                reverse(pos[b], pos[c])
                return delta, (a, b, c, d)
        # 2-opt, predecessor side
        b = tour[pa - 1]
        dab = row[b]
        for c in neigh[a]:
            dac = row[c]
            if dac >= dab:
                break
            d = tour[pos[c] - 1]
            if c == b or d == a:
                continue
            delta = dab + D[c][d] - dac - D[b][d]
            if delta > EPS:
                reverse(pos[a], pos[d])
                return delta, (a, b, c, d)
        # Or-opt: segments of length 1..3 starting at a going forward
        for L in (1, 2, 3):
            if pa + L > n or L + 2 >= n:
                break
            seg = tour[pa:pa + L]
            s0 = seg[0]
            sL = seg[-1]
            p = tour[pa - 1]
            q = tour[(pa + L) % n]
            remove = D[p][s0] + D[sL][q] - D[p][q]
            if remove <= EPS:
                continue
            segset = set(seg)
            for e, f in ((s0, sL), (sL, s0)):
                re = D[e]
                for c in neigh[e]:
                    dce = re[c]
                    if dce >= remove:
                        break
                    if c in segset:
                        continue
                    pc = pos[c]
                    for m in (tour[(pc + 1) % n], tour[pc - 1]):
                        if m in segset:
                            continue
                        delta = remove - (dce + D[f][m] - D[c][m])
                        if delta > EPS:
                            fwd = tour[(pc + 1) % n] == m
                            rest = tour[pa + L:] + tour[:pa]
                            # rest runs q ... p cyclically; edge (c,m) is inside it
                            ic = rest.index(c)
                            if fwd:
                                ins = seg if e == s0 else seg[::-1]
                                new = rest[:ic + 1] + ins + rest[ic + 1:]
                            else:
                                ins = seg[::-1] if e == s0 else seg
                                new = rest[:ic] + ins + rest[ic:]
                            tour[:] = new
                            for i2, c2 in enumerate(tour):
                                pos[c2] = i2
                            return delta, (a, p, q, c, m, s0, sL)
        return None

    def local_search(queue, inq):
        total = 0.0
        while queue:
            a = queue.pop()
            inq[a] = False
            while True:
                r = improve(a)
                if r is None:
                    break
                total += r[0]
                for x in r[1]:
                    if not inq[x]:
                        inq[x] = True
                        queue.append(x)
        return total

    inq = [True] * n
    queue = list(range(n - 1, -1, -1))
    local_search(queue, inq)

    if TIME <= 0 or n < 8:
        return tour

    deadline = t_start + TIME
    rng = random.Random(SEED)
    inq = [False] * n
    maxseg = max(1, min(MAXSEG, n // 2))
    avg_edge = sum(D[tour[i - 1]][tour[i]] for i in range(n)) / n
    cur = 0.0
    best = 0.0
    best_t = tour[:]
    it = 0
    thr = THR * avg_edge
    while True:
        it += 1
        now = time.perf_counter()
        if MAXIT:
            if it > MAXIT:
                break
            frac = it / MAXIT
        else:
            if now >= deadline:
                break
            frac = (now - t_start) / TIME
        saved_t = tour[:]
        saved_p = pos[:]
        if rng.random() < PSPAT:
            c0 = rng.randrange(n)
            u = rng.choice(neigh[c0])
            w = rng.choice(neigh[u] if rng.random() < 0.5 else neigh[c0])
            ps = sorted({pos[c0], pos[u], pos[w]})
            if len(ps) < 3:
                continue
            i = ps[0]
            l1 = ps[1] - ps[0]
            l2 = ps[2] - ps[1]
        else:
            i = rng.randrange(n)
            l1 = rng.randint(1, maxseg)
            l2 = rng.randint(1, maxseg)
        rolled = tour[i:] + tour[:i]
        A = rolled[:1]
        S1 = rolled[1:1 + l1]
        S2 = rolled[1 + l1:1 + l1 + l2]
        R = rolled[1 + l1 + l2:]
        if not R:
            continue
        old = D[A[0]][S1[0]] + D[S1[-1]][S2[0]] + D[S2[-1]][R[0]]
        new_ = D[A[0]][S2[0]] + D[S2[-1]][S1[0]] + D[S1[-1]][R[0]]
        tour[:] = A + S2 + S1 + R
        for k, c in enumerate(tour):
            pos[c] = k
        queue = []
        for x in (A[0], S1[0], S1[-1], S2[0], S2[-1], R[0]):
            if not inq[x]:
                inq[x] = True
                queue.append(x)
        gain = local_search(queue, inq) - (new_ - old)
        allow = thr * (1.0 - frac) * rng.random()
        if gain < -allow - EPS:
            tour[:] = saved_t
            pos[:] = saved_p
        else:
            cur -= gain
            if cur < best - EPS:
                best = cur
                best_t = tour[:]
    LAST_IT[0] = it
    return best_t
