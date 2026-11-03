import math, random, time

TIME = 0.55
K = 5
WIN = 50
ACC = 0.01
QN = 2


def solve(points):
    t0 = time.perf_counter()
    n = len(points)
    if n <= 3:
        return list(range(n))
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    if n > 400:
        # the O(n^2) setup below would not fit the time limit; plain nearest neighbour
        left = set(range(1, n)); tour = [0]
        while left:
            cx, cy = xs[tour[-1]], ys[tour[-1]]
            nxt = min(left, key=lambda j: (xs[j] - cx) ** 2 + (ys[j] - cy) ** 2)
            left.remove(nxt); tour.append(nxt)
        return tour
    D = [[math.hypot(xs[i] - xs[j], ys[i] - ys[j]) for j in range(n)] for i in range(n)]
    neigh = []
    for i in range(n):
        order = sorted((j for j in range(n) if j != i), key=D[i].__getitem__)
        sel = order[:K]; quad = [0, 0, 0, 0]
        for j in order:
            q = (xs[j] >= xs[i]) + 2 * (ys[j] >= ys[i])
            if quad[q] < QN:
                quad[q] += 1
                if j not in sel: sel.append(j)
        sel.sort(key=D[i].__getitem__)
        neigh.append(sel)

    # nearest neighbour start
    left = set(range(1, n)); tour = [0]
    while left:
        row = D[tour[-1]]
        nxt = min(left, key=row.__getitem__)
        left.remove(nxt); tour.append(nxt)

    pos = [0] * n

    def setpos():
        for i, c in enumerate(tour):
            pos[c] = i

    def reverse(i, j):
        # reverse tour[i..j] cyclically, i,j positions
        L = (j - i) % n + 1
        for _ in range(L // 2):
            a, b = tour[i], tour[j]
            tour[i] = b; pos[b] = i
            tour[j] = a; pos[a] = j
            i += 1
            if i == n: i = 0
            j -= 1
            if j < 0: j = n - 1

    def two_opt(active):
        dl = set(active); stack = list(active)
        while stack:
            a = stack.pop()
            if a not in dl:
                continue
            dl.discard(a)
            improved = False
            for direction in (0, 1):
                pa = pos[a]
                if direction == 0:
                    b = tour[(pa + 1) % n]
                else:
                    b = tour[pa - 1]
                dab = D[a][b]
                for c in neigh[a]:
                    dac = D[a][c]
                    if dac >= dab:
                        break
                    pc = pos[c]
                    d = tour[(pc + 1) % n] if direction == 0 else tour[pc - 1]
                    if c == b or d == a:
                        continue
                    delta = dac + D[b][d] - dab - D[c][d]
                    if delta < -1e-12:
                        if direction == 0:
                            reverse((pa + 1) % n, pc)
                        else:
                            reverse(pc, (pa - 1) % n)
                        for x in (a, b, c, d):
                            if x not in dl:
                                dl.add(x); stack.append(x)
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                # or-opt: move segment starting at a of length 1..3
                for seglen in (1, 2, 3):
                    pa = pos[a]
                    s0 = a; s1 = tour[(pa + seglen - 1) % n]
                    p = tour[pa - 1]; q = tour[(pa + seglen) % n]
                    if q == p or seglen >= n - 2:
                        continue
                    gain_rm = D[p][s0] + D[s1][q] - D[p][q]
                    if gain_rm <= 1e-12:
                        continue
                    seg = set(tour[(pa + k) % n] for k in range(seglen))
                    done = False
                    for end, other in ((s0, s1), (s1, s0)):
                        for c in neigh[end]:
                            if c in seg:
                                continue
                            pc = pos[c]
                            for e in (tour[(pc + 1) % n], tour[pc - 1]):
                                if e in seg:
                                    continue
                                # insert between c and e with end adjacent to c
                                add = D[c][end] + D[other][e] - D[c][e]
                                if add < gain_rm - 1e-12:
                                    # rebuild tour list
                                    segl = [tour[(pa + k) % n] for k in range(seglen)]
                                    rest = [x for x in tour if x not in seg]
                                    ic = rest.index(c); ie = (ic + 1) % len(rest)
                                    if rest[ie] == e:
                                        ins = segl if end == s0 else segl[::-1]
                                        # order c, end..other, e
                                        new = rest[:ic + 1] + (ins if end == segl[0] else ins) + rest[ic + 1:]
                                    else:
                                        ins = segl[::-1] if end == s0 else segl
                                        # rest[ic-1]==e : e, other..end, c
                                        new = rest[:ic] + ins + rest[ic:]
                                    tour[:] = new; setpos()
                                    for x in (p, q, c, e, s0, s1):
                                        if x not in dl:
                                            dl.add(x); stack.append(x)
                                    done = True
                                    break
                            if done: break
                        if done: break
                    if done:
                        break

    setpos()
    two_opt(range(n))

    def tlen(t):
        return sum(D[t[i - 1]][t[i]] for i in range(n))

    best = tour[:]; bestlen = tlen(best)
    curt = best[:]; curlen = bestlen
    thr = ACC * bestlen / n
    rnd = random.Random(12345)
    while time.perf_counter() - t0 < TIME:
        L = min(n, WIN)
        st = rnd.randrange(n)
        a, b, c = sorted(rnd.sample(range(1, L), 3))
        rot = tour[st:] + tour[:st]
        new = rot[:a] + rot[b:c] + rot[a:b] + rot[c:]
        tour[:] = new; setpos()
        touched = set()
        for k in (0, a - 1, a, b - 1, b, c - 1, c):
            touched.add(new[k % n])
        two_opt(list(touched))
        l = tlen(tour)
        if l < curlen + thr:
            curlen = l; curt = tour[:]
            if l < bestlen - 1e-12:
                bestlen = l; best = tour[:]
        else:
            tour[:] = curt; setpos()
    return best
