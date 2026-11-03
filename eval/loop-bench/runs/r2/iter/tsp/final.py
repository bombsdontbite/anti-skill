import math
import random
import time

BUDGET = 0.72
KN = 5
WIN = 50
QN = 2
NEARK = 12
KICK = 1
ACC = 1.0
PG = 0.1


def solve(points):
    t0 = time.perf_counter()
    n = len(points)
    if n <= 4:
        return list(range(n))
    rng = random.Random(12345)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pts = [(float(p[0]), float(p[1])) for p in points]
    dist = math.dist
    D = [[dist(p, q) for q in pts] for p in pts]
    K = min(KN, n - 1)
    neigh = []
    near = []
    for i in range(n):
        row = D[i]
        idx = sorted(range(n), key=lambda j: row[j])
        idx = [j for j in idx if j != i]
        sel = idx[:K]
        if QN:
            xi = xs[i]
            yi = ys[i]
            cnt = [0, 0, 0, 0]
            for j in idx:
                q = (xs[j] >= xi) * 2 + (ys[j] >= yi)
                if cnt[q] < QN:
                    cnt[q] += 1
                    if j not in sel:
                        sel.append(j)
            sel.sort(key=lambda j: row[j])
        neigh.append(sel)
        near.append(idx[:NEARK])
    eps = 1e-10

    left = set(range(1, n))
    tour = [0]
    cur = 0
    while left:
        row = D[cur]
        nxt = min(left, key=lambda j: row[j])
        left.remove(nxt)
        tour.append(nxt)
        cur = nxt
    pos = [0] * n
    for k in range(n):
        pos[tour[k]] = k

    def tour_len(t):
        s = 0.0
        prev = t[-1]
        for c in t:
            s += D[prev][c]
            prev = c
        return s

    def improve(t1):
        p1 = pos[t1]
        for fw in (True, False):
            if fw:
                p2 = p1 + 1
                if p2 == n:
                    p2 = 0
            else:
                p2 = p1 - 1 if p1 else n - 1
            t2 = tour[p2]
            D1 = D[t1]
            d12 = D1[t2]
            D2 = D[t2]
            for t3 in neigh[t2]:
                g1 = d12 - D2[t3]
                if g1 <= eps:
                    break
                if t3 == t1:
                    continue
                i3 = (pos[t3] - p2) % n if fw else (p2 - pos[t3]) % n
                D3 = D[t3]
                # case A: t4 = pred(t3)
                if i3 > 1:
                    i4 = i3 - 1
                    t4 = tour[(p2 + i4) % n] if fw else tour[(p2 - i4) % n]
                    g1b = g1 + D3[t4]
                    D4 = D[t4]
                    if g1b - D4[t1] > eps:
                        S = tour[p2:] + tour[:p2] if fw else tour[p2::-1] + tour[:p2:-1]
                        new = S[i4::-1] + S[i4 + 1:]
                        tour[:] = new
                        for k in range(n):
                            pos[new[k]] = k
                        return (t1, t2, t3, t4)
                    for t5 in neigh[t4]:
                        g2 = g1b - D4[t5]
                        if g2 <= eps:
                            break
                        if t5 == t1 or t5 == t3:
                            continue
                        i5 = (pos[t5] - p2) % n if fw else (p2 - pos[t5]) % n
                        if i5 < i4:
                            i6 = i5 + 1
                            if i6 == i4:
                                continue
                        else:
                            i6 = i5 - 1
                        t6 = tour[(p2 + i6) % n] if fw else tour[(p2 - i6) % n]
                        if g2 + D[t5][t6] - D1[t6] > eps:
                            S = tour[p2:] + tour[:p2] if fw else tour[p2::-1] + tour[:p2:-1]
                            S2 = S[i4::-1] + S[i4 + 1:]
                            j6 = i4 - i6 if i6 <= i4 else i6
                            new = S2[j6::-1] + S2[j6 + 1:]
                            tour[:] = new
                            for k in range(n):
                                pos[new[k]] = k
                            return (t1, t2, t3, t4, t5, t6)
                # case B: t4 = succ(t3)
                if i3 + 1 < n - 1:
                    i4 = i3 + 1
                    t4 = tour[(p2 + i4) % n] if fw else tour[(p2 - i4) % n]
                    g1b = g1 + D3[t4]
                    D4 = D[t4]
                    for t5 in neigh[t4]:
                        g2 = g1b - D4[t5]
                        if g2 <= eps:
                            break
                        i5 = (pos[t5] - p2) % n if fw else (p2 - pos[t5]) % n
                        if i5 > i3:
                            continue
                        D5 = D[t5]
                        if i5 < i3:
                            i6 = i5 + 1
                            t6 = tour[(p2 + i6) % n] if fw else tour[(p2 - i6) % n]
                            if g2 + D5[t6] - D1[t6] > eps:
                                S = tour[p2:] + tour[:p2] if fw else tour[p2::-1] + tour[:p2:-1]
                                new = S[i3 + 1:] + S[i5 + 1:i3 + 1] + S[:i5 + 1]
                                tour[:] = new
                                for k in range(n):
                                    pos[new[k]] = k
                                return (t1, t2, t3, t4, t5, t6)
                        if i5 > 0:
                            i6 = i5 - 1
                            t6 = tour[(p2 + i6) % n] if fw else tour[(p2 - i6) % n]
                            if g2 + D5[t6] - D1[t6] > eps:
                                S = tour[p2:] + tour[:p2] if fw else tour[p2::-1] + tour[:p2:-1]
                                new = S[i3 + 1:] + S[i5 - 1::-1] + S[i3:i5 - 1:-1] if i5 > 0 else None
                                tour[:] = new
                                for k in range(n):
                                    pos[new[k]] = k
                                return (t1, t2, t3, t4, t5, t6)
        return None

    def local_search(start):
        dlb = [False] * n
        stack = list(start)
        inq = [False] * n
        for c in stack:
            inq[c] = True
        while stack:
            a = stack.pop()
            inq[a] = False
            while True:
                r = improve(a)
                if r is None:
                    break
                for x in r:
                    if not inq[x]:
                        inq[x] = True
                        stack.append(x)

    local_search(range(n))
    cur_len = tour_len(tour)
    best_tour = tour[:]
    best_len = cur_len

    while time.perf_counter() - t0 < BUDGET:
        old = tour[:]
        if rng.random() >= PG:
            c0 = rng.randrange(n)
            cs = [c0] + rng.sample(near[c0], 3)
            ps = sorted(pos[c] for c in cs)
            start = ps[0]
            a1 = ps[1] - start
            a2 = ps[2] - start
            a3 = ps[3] - start
            if a1 < 1 or a2 <= a1 or a3 <= a2:
                continue
            start = (start + 1) % n
            rot = tour[start:] + tour[:start]
        else:
            w = n
            start = rng.randrange(n)
            a1, a2, a3 = sorted(rng.sample(range(1, w), 3))
            rot = tour[start:] + tour[:start]
        new = rot[:a1] + rot[a2:a3] + rot[a1:a2] + rot[a3:]
        touched = (rot[0], rot[a1 - 1], rot[a1], rot[a2 - 1], rot[a2], rot[a3 - 1], rot[a3 % n], rot[-1])
        tour[:] = new
        for k in range(n):
            pos[new[k]] = k
        local_search(touched)
        L = tour_len(tour)
        if L < cur_len * ACC - 1e-12:
            cur_len = L
            if L < best_len - 1e-12:
                best_len = L
                best_tour = tour[:]
        else:
            tour[:] = old
            for k in range(n):
                pos[old[k]] = k
    return best_tour
