import math, random, time

LIMIT = 0.7
K = 6
Q = 2
R = 3
F = 0.75


def solve(points):
    t0 = time.perf_counter()
    n = len(points)
    if n <= 3:
        return list(range(n))
    D = [[math.dist(a, b) for b in points] for a in points]
    nb = []
    for i in range(n):
        order = sorted(range(n), key=D[i].__getitem__)[1:]
        xi, yi = points[i]
        quad = [[], [], [], []]
        for j in order:
            x, y = points[j]
            q = (x >= xi) + 2 * (y >= yi)
            if len(quad[q]) < Q:
                quad[q].append(j)
        s = set(order[:K])
        for qq in quad:
            s.update(qq)
        nb.append(sorted(s, key=D[i].__getitem__))

    pos = [0] * n

    def setpos():
        for i, c in enumerate(tour):
            pos[c] = i

    def reverse(i, j):
        # reverse tour[i..j] cyclically (i, j positions)
        L = (j - i) % n + 1
        for _ in range(L // 2):
            a, b = tour[i], tour[j]
            tour[i], tour[j] = b, a
            pos[b], pos[a] = i, j
            i += 1
            if i == n:
                i = 0
            j -= 1
            if j < 0:
                j = n - 1

    def two_opt(queue):
        inq = [False] * n
        tot = 0.0
        for c in queue:
            inq[c] = True
        while queue:
            a = queue.pop()
            inq[a] = False
            improved = False
            for dirn in (1, -1):
                pa = pos[a]
                an = tour[(pa + dirn) % n]
                dan = D[a][an]
                for c in nb[a]:
                    dac = D[a][c]
                    if dac >= dan:
                        break
                    pc = pos[c]
                    cn = tour[(pc + dirn) % n]
                    delta = dac + D[an][cn] - dan - D[c][cn]
                    if delta < -1e-12:
                        tot += delta
                        if dirn == 1:
                            reverse((pa + 1) % n, pc)
                        else:
                            reverse(pc, (pa - 1) % n)
                        for x in (a, an, c, cn):
                            if not inq[x]:
                                inq[x] = True
                                queue.append(x)
                        improved = True
                        break
                if improved:
                    break
            if improved:
                continue
            # or-opt: move segment starting at a (len 1..3) between c and its neighbour
            for sl in (1, 2, 3):
                pa = pos[a]
                s0, s1 = a, tour[(pa + sl - 1) % n]
                p = tour[(pa - 1) % n]
                q = tour[(pa + sl) % n]
                if q == s0 or p == s1:
                    break
                rem = D[p][s0] + D[s1][q] - D[p][q]
                seg = set(tour[(pa + k) % n] for k in range(sl))
                done = False
                for end, other in ((s0, s1), (s1, s0)):
                    for c in nb[end]:
                        if c in seg:
                            continue
                        if D[end][c] >= rem:
                            break
                        pc = pos[c]
                        for d in (tour[(pc + 1) % n], tour[(pc - 1) % n]):
                            if d in seg:
                                continue
                            gain = rem - (D[c][end] + D[d][other] - D[c][d])
                            if gain > 1e-12:
                                tot -= gain
                                # rebuild tour: remove segment, insert between c and d
                                segl = [tour[(pa + k) % n] for k in range(sl)]
                                rest = [x for x in tour if x not in seg]
                                ic = rest.index(c)
                                idd = rest.index(d)
                                # want ... c, end..other, d ...
                                ins = segl if end == s0 else segl[::-1]
                                if (ic + 1) % len(rest) == idd:
                                    new = rest[:ic + 1] + ins + rest[ic + 1:]
                                else:  # d precedes c
                                    new = rest[:idd + 1] + ins[::-1] + rest[idd + 1:]
                                tour[:] = new
                                setpos()
                                for x in (p, q, c, d, s0, s1):
                                    if not inq[x]:
                                        inq[x] = True
                                        queue.append(x)
                                done = True
                                break
                        if done:
                            break
                    if done:
                        break
                if done:
                    break
        return tot

    def length(t):
        return sum(D[t[i - 1]][t[i]] for i in range(n))

    def ils(deadline, curL, hot):
        best = tour[:]
        while time.perf_counter() < deadline:
            # segment-local double bridge, done in place on a window of the tour
            L = rnd.randint(8, 30)
            if hot:
                st = (pos[hot[rnd.randrange(len(hot))]] - rnd.randrange(L)) % n
            else:
                st = rnd.randrange(n)
            a, b, c = sorted(rnd.sample(range(1, L), 3))
            idx = [(st + k) % n for k in range(L + 1)]
            w = [tour[i] for i in idx]
            dk = (D[w[a - 1]][w[b]] + D[w[c - 1]][w[a]] + D[w[b - 1]][w[c]]
                  - D[w[a - 1]][w[a]] - D[w[b - 1]][w[b]] - D[w[c - 1]][w[c]])
            w = w[:a] + w[b:c] + w[a:b] + w[c:]
            for i, x in zip(idx, w):
                tour[i] = x
                pos[x] = i
            touched = [w[i] for i in (0, a - 1, a, b - 1, b, c - 1, c)]
            cur = curL + dk + two_opt(touched)
            if cur < curL - 1e-12:
                curL = cur
                best = tour[:]
            else:
                tour[:] = best
                setpos()
        return curL, best

    rnd = random.Random(12345)
    tour = []
    runs = []
    for r in range(R):
        s0 = 0 if r == 0 else rnd.randrange(n)
        left = set(range(n))
        left.remove(s0)
        tour[:] = [s0]
        while left:
            Dc = D[tour[-1]]
            j = min(left, key=Dc.__getitem__)
            left.remove(j)
            tour.append(j)
        setpos()
        two_opt(list(range(n)))
        runs.append(ils(t0 + LIMIT * F * (r + 1) / R, length(tour), None))
    runs.sort()
    bL, best = runs[0]
    # final phase: continue from the best run, kicking only where the runs disagree
    ed = [set() for _ in range(n)]
    for _, t in runs[1:]:
        for i in range(n):
            ed[t[i - 1]].add(t[i])
            ed[t[i]].add(t[i - 1])
    hot = [best[i] for i in range(n)
           if best[i - 1] not in ed[best[i]] or best[(i + 1) % n] not in ed[best[i]]]
    tour[:] = best
    setpos()
    return ils(t0 + LIMIT, bL, hot)[1]
