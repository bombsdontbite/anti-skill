import math, random, time

TIME = 0.60
K = 8
QK = 3
SEED = 12345
W = 80
GLOBAL = 0.0
ACC_T = 0.0
EQ = False
RESTARTS = 1


def solve(points):
    t0 = time.perf_counter()
    n = len(points)
    if n <= 3:
        return list(range(n))
    D = [[math.dist(p, q) for q in points] for p in points]
    neigh = []
    for i in range(n):
        xi, yi = points[i]
        order = sorted((j for j in range(n) if j != i), key=lambda j, r=D[i]: r[j])
        sel = order[:K]; seen = set(sel)
        quad = [0, 0, 0, 0]
        for j in order:
            q = (points[j][0] >= xi) * 2 + (points[j][1] >= yi)
            if quad[q] < QK:
                quad[q] += 1
                if j not in seen:
                    seen.add(j); sel.append(j)
        sel.sort(key=lambda j, r=D[i]: r[j])
        neigh.append(sel)
    rnd = random.Random(SEED)

    # nearest-neighbour start
    left = set(range(1, n)); tour = [0]
    while left:
        row = D[tour[-1]]
        nxt = min(left, key=lambda j, r=row: r[j])
        left.remove(nxt); tour.append(nxt)
    pos = [0] * n
    for i, c in enumerate(tour):
        pos[c] = i

    def reverse(i, j):
        # reverse positions i..j inclusive (cyclic), choosing the shorter side
        L = (j - i) % n + 1
        if 2 * L > n:
            i, j = (j + 1) % n, (i - 1) % n
            L = n - L
        for _ in range(L // 2):
            a, b = tour[i], tour[j]
            tour[i] = b; pos[b] = i
            tour[j] = a; pos[a] = j
            i += 1
            if i == n: i = 0
            j -= 1
            if j < 0: j = n - 1

    def two_opt(a):
        pa = pos[a]
        Da = D[a]
        for direction in (1, -1):
            b = tour[(pa + direction) % n]
            dab = Da[b]
            for c in neigh[a]:
                dac = Da[c]
                if dac >= dab:
                    break
                pc = pos[c]
                d = tour[(pc + direction) % n]
                if d == a:
                    continue
                delta = dac + D[b][d] - dab - D[c][d]
                if delta < -1e-12:
                    if direction == 1:
                        reverse((pa + 1) % n, pc)
                    else:
                        reverse(pa, (pc - 1) % n)
                    return delta, (a, b, c, d)
        return 0.0, None

    def or_opt(a):
        nonlocal tour
        for L in (1, 2, 3):
            for start_shift in range(L):
                i = (pos[a] - start_shift) % n
                seg = [tour[(i + k) % n] for k in range(L)]
                s0, sL = seg[0], seg[-1]
                p = tour[(i - 1) % n]; nx = tour[(i + L) % n]
                if p == nx or p in seg or nx in seg:
                    continue
                g1 = D[p][s0] + D[sL][nx] - D[p][nx]
                best = -1e-12; mv = None
                for x in (s0, sL):
                    for c in neigh[x]:
                        if c in seg:
                            continue
                        if D[x][c] >= g1:
                            break
                        pc = pos[c]
                        for e in (tour[(pc + 1) % n], tour[(pc - 1) % n]):
                            if e in seg:
                                continue
                            dce = D[c][e]
                            # c-x adjacent: insert seg between c and e
                            if x == s0:
                                add = D[c][s0] + D[sL][e] - dce
                                fwd_end = sL
                            else:
                                add = D[c][sL] + D[s0][e] - dce
                                fwd_end = s0
                            delta = add - g1
                            if delta < best:
                                best = delta; mv = (c, e, x)
                if mv is not None:
                    c, e, x = mv
                    order = tour[i:] + tour[:i]
                    rest = order[L:]
                    # place so that c is adjacent to x and e to the other end
                    ic = rest.index(c)
                    other = sL if x == s0 else s0
                    ins = [x] + ([] if L == 1 else (seg[1:-1] if x == s0 else seg[-2:0:-1])) + ([other] if L > 1 else [])
                    if rest[(ic + 1) % len(rest)] == e:
                        new = rest[:ic + 1] + ins + rest[ic + 1:]
                    else:  # e precedes c
                        new = rest[:ic] + ins[::-1] + rest[ic:]
                    tour[:] = new
                    for k, cc in enumerate(tour):
                        pos[cc] = k
                    return best, (p, nx, c, e, s0, sL)
        return 0.0, None

    def local_search(queue):
        inq = set(queue)
        gain = 0.0
        while queue:
            a = queue.pop()
            inq.discard(a)
            while True:
                d, touched = two_opt(a)
                if touched is None:
                    d, touched = or_opt(a)
                if touched is None:
                    break
                gain += d
                for c in touched:
                    if c not in inq:
                        inq.add(c); queue.append(c)
        return gain

    def tour_len(t):
        return sum(D[t[k - 1]][t[k]] for k in range(n))

    local_search(list(range(n)))
    cur = tour_len(tour)
    best_t = tour[:]; best_len = cur
    deadline = t0 + TIME
    start = time.perf_counter(); span = max(1e-9, deadline - start)
    unit = cur / n
    init_t = tour[:]; init_len = cur; slot = 1
    while True:
        now = time.perf_counter()
        if now >= deadline:
            break
        if RESTARTS > 1 and now >= start + span * slot / RESTARTS:
            slot += 1
            tour[:] = init_t; cur = init_len
            for k, cc in enumerate(tour):
                pos[cc] = k
        saved = tour[:]
        w = min(n - 1, W)
        if GLOBAL and rnd.random() < GLOBAL:
            w = n - 1
        i = rnd.randrange(n)
        cuts = sorted(rnd.sample(range(1, w), 3))
        idx = [(i + c) % n for c in range(w + 1)]
        seq = [tour[k] for k in idx]
        a, b, c = cuts
        newseq = seq[:a] + seq[b:c] + seq[a:b] + seq[c:]
        for k, cc in zip(idx, newseq):
            tour[k] = cc; pos[cc] = k
        touched = [seq[a - 1], seq[a], seq[b - 1], seq[b], seq[c - 1], seq[c]]
        local_search(touched)
        new = tour_len(tour)
        T = ACC_T * unit * (1 - (now - start) / span)
        if new < cur - 1e-12 or (T > 0 and new > cur + 1e-12 and rnd.random() < math.exp(-(new - cur) / T)) or (EQ and abs(new - cur) <= 1e-12):
            cur = new
            if cur < best_len - 1e-12:
                best_len = cur; best_t = tour[:]
        else:
            tour[:] = saved
            for k, cc in enumerate(tour):
                pos[cc] = k
    return best_t
