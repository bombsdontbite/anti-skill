import math
import random
import time

BUDGET = 0.6


def solve(points):
    t0 = time.perf_counter()
    deadline = t0 + BUDGET
    n = len(points)
    if n <= 3:
        return list(range(n))
    rng = random.Random(12345)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    hyp = math.hypot
    D = [[hyp(xs[i] - xs[j], ys[i] - ys[j]) for j in range(n)] for i in range(n)]
    K = min(10, n - 1)
    neigh = []
    for i in range(n):
        row = D[i]
        order = sorted(range(n), key=row.__getitem__)
        neigh.append([j for j in order if j != i][:K])

    # nearest neighbour start
    left = set(range(1, n))
    tour = [0]
    cur = 0
    while left:
        row = D[cur]
        nxt = min(left, key=row.__getitem__)
        left.remove(nxt)
        tour.append(nxt)
        cur = nxt

    pos = [0] * n
    for i, c in enumerate(tour):
        pos[c] = i

    def reverse(t, ps, i, j):
        # reverse tour positions i..j (forward, wrapping)
        L = (j - i) % n + 1
        if 2 * L > n:
            i, j = (j + 1) % n, (i - 1) % n
            L = n - L
        for _ in range(L // 2):
            a = t[i]
            b = t[j]
            t[i] = b
            ps[b] = i
            t[j] = a
            ps[a] = j
            i += 1
            if i == n:
                i = 0
            j -= 1
            if j < 0:
                j = n - 1

    def local_search(t, ps, queue):
        # 2-opt + or-opt with neighbour lists and a work queue; returns total gain
        inq = [False] * n
        for c in queue:
            inq[c] = True
        gain_total = 0.0
        eps = 1e-12
        while queue:
            a = queue.pop()
            inq[a] = False
            improved = True
            while improved:
                improved = False
                Da = D[a]
                na = neigh[a]
                pa = ps[a]
                # 2-opt, successor direction
                b = t[(pa + 1) % n]
                dab = Da[b]
                for c in na:
                    g1 = dab - Da[c]
                    if g1 <= eps:
                        break
                    pc = ps[c]
                    d = t[(pc + 1) % n]
                    if d == a:
                        continue
                    delta = g1 + D[c][d] - D[b][d]
                    if delta > eps:
                        reverse(t, ps, (pa + 1) % n, pc)
                        gain_total += delta
                        for x in (a, b, c, d):
                            if not inq[x]:
                                inq[x] = True
                                queue.append(x)
                        improved = True
                        break
                if improved:
                    continue
                # 2-opt, predecessor direction
                pa = ps[a]
                b = t[pa - 1]
                dab = Da[b]
                for c in na:
                    g1 = dab - Da[c]
                    if g1 <= eps:
                        break
                    pc = ps[c]
                    d = t[pc - 1]
                    if d == a:
                        continue
                    delta = g1 + D[c][d] - D[b][d]
                    if delta > eps:
                        reverse(t, ps, pa, (pc - 1) % n)
                        gain_total += delta
                        for x in (a, b, c, d):
                            if not inq[x]:
                                inq[x] = True
                                queue.append(x)
                        improved = True
                        break
                if improved:
                    continue
                # or-opt: move segment starting at a (forward) of length 1..3
                pa = ps[a]
                for seglen in (1, 2, 3):
                    s1 = a
                    s2 = t[(pa + seglen - 1) % n]
                    p = t[pa - 1]
                    nx = t[(pa + seglen) % n]
                    if nx == p or seglen + 2 > n:
                        break
                    rem = D[p][s1] + D[s2][nx] - D[p][nx]
                    if rem <= eps:
                        continue
                    segset = [t[(pa + k) % n] for k in range(seglen)]
                    best = eps
                    bestmv = None
                    for end in (s1, s2):
                        De = D[end]
                        for c in neigh[end]:
                            dc = De[c]
                            if dc >= rem:
                                break
                            if c in segset:
                                continue
                            pc = ps[c]
                            for d in (t[(pc + 1) % n], t[pc - 1]):
                                if d in segset:
                                    continue
                                # insert between c and d with end adjacent to c
                                other = s2 if end == s1 else s1
                                g = rem - (dc + D[other][d] - D[c][d])
                                if g > best:
                                    best = g
                                    bestmv = (c, d, end)
                    if bestmv is not None:
                        c, d, end = bestmv
                        # rebuild tour
                        seg = segset
                        rest = [x for x in t if x not in seg] if False else None
                        start = (pa + seglen) % n
                        rest = [t[(start + k) % n] for k in range(n - seglen)]
                        # rest starts at nx and ends at p
                        ic = rest.index(c)
                        idd = ic + 1 if ic + 1 < len(rest) else 0
                        if rest[idd] == d:
                            # c before d in rest: insert after c, seg oriented with end first
                            ins = seg if end == s1 else seg[::-1]
                            new = rest[:ic + 1] + ins + rest[ic + 1:]
                        else:
                            # d before c: insert before c, seg oriented with end last
                            ins = seg[::-1] if end == s1 else seg
                            new = rest[:ic] + ins + rest[ic:]
                        t[:] = new
                        for i2, x in enumerate(t):
                            ps[x] = i2
                        gain_total += best
                        for x in (p, nx, c, d, s1, s2):
                            if not inq[x]:
                                inq[x] = True
                                queue.append(x)
                        improved = True
                        break
        return gain_total

    def tour_len(t):
        s = 0.0
        prev = t[-1]
        for c in t:
            s += D[prev][c]
            prev = c
        return s

    local_search(tour, pos, list(range(n)))
    cur_len = tour_len(tour)
    best_tour = tour[:]
    best_len = cur_len

    seg_max = max(2, min(50, n // 4))
    it = 0
    while True:
        it += 1
        if (it & 7) == 0 and time.perf_counter() > deadline:
            break
        t = tour[:]
        # localized double bridge
        r = rng.randrange(n)
        l1 = rng.randint(1, seg_max)
        l2 = rng.randint(1, seg_max)
        l3 = rng.randint(1, seg_max)
        if l1 + l2 + l3 >= n - 1:
            continue
        t = t[r:] + t[:r]
        i = l1
        j = i + l2
        k = j + l3
        a0, a1 = t[i - 1], t[i]
        b0, b1 = t[j - 1], t[j]
        c0, c1 = t[k - 1], t[k]
        delta = (D[a0][b1] + D[c0][a1] + D[b0][c1]) - (D[a0][a1] + D[b0][b1] + D[c0][c1])
        t = t[:i] + t[j:k] + t[i:j] + t[k:]
        ps = [0] * n
        for i2, x in enumerate(t):
            ps[x] = i2
        new_len = cur_len + delta
        new_len -= local_search(t, ps, [a0, a1, b0, b1, c0, c1])
        if new_len < cur_len - 1e-10:
            tour = t
            cur_len = new_len
            if cur_len < best_len:
                best_len = cur_len
                best_tour = t[:]
    return best_tour
