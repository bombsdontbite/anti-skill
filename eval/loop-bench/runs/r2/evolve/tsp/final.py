import math
import random
import time

BUDGET = 0.75
K = 12
MAXSEG = 30
INIT = 'nn'
ACC_T = 0.0
KICK = 'seg'
CLOCK = time.perf_counter
ORL = 3
STALL = 0
OR_FIRST = False


def greedy(n, D):
    edges = sorted((D[i][j], i, j) for i in range(n) for j in range(i + 1, n))
    deg = [0] * n
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    adj = [[] for _ in range(n)]
    cnt = 0
    for d, i, j in edges:
        if deg[i] < 2 and deg[j] < 2:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
                deg[i] += 1; deg[j] += 1
                adj[i].append(j); adj[j].append(i)
                cnt += 1
                if cnt == n - 1:
                    break
    start = [i for i in range(n) if deg[i] < 2][0]
    tour = [start]; prev = -1; cur = start
    while len(tour) < n:
        nxt = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
        tour.append(nxt); prev, cur = cur, nxt
    return tour


def repos(t, pos):
    for i, c in enumerate(t):
        pos[c] = i


def ls_run(t, pos, D, neigh, active, oropt=True):
    n = len(t)
    queue = list(active); inq = [False] * n
    for a in queue:
        inq[a] = True
    gain_total = 0.0
    while queue:
        a = queue.pop()
        inq[a] = False
        improved = False
        for direction in (1, -1):
            ia = pos[a]
            b = t[(ia + direction) % n]
            dab = D[a][b]
            for c in neigh[a]:
                dac = D[a][c]
                if dac >= dab:
                    break
                ic = pos[c]
                d = t[(ic + direction) % n]
                if d == a or c == b or c == a:
                    continue
                delta = dac + D[b][d] - dab - D[c][d]
                if delta < -1e-10:
                    if direction == 1:
                        x, y = b, c
                        if pos[x] > pos[y]:
                            x, y = d, a
                    else:
                        x, y = a, d
                        if pos[x] > pos[y]:
                            x, y = c, b
                    i, j = pos[x], pos[y]
                    t[i:j + 1] = t[i:j + 1][::-1]
                    for k in range(i, j + 1):
                        pos[t[k]] = k
                    gain_total -= delta
                    for x in (a, b, c, d):
                        if not inq[x]:
                            inq[x] = True; queue.append(x)
                    improved = True
                    break
            if improved:
                break
        if improved or not oropt:
            continue
        for L in range(1, ORL + 1):
            ia = pos[a]
            seg = [t[(ia + k) % n] for k in range(L)]
            p = t[(ia - 1) % n]; q = t[(ia + L) % n]
            if q == p or q in seg or p in seg:
                break
            s0 = seg[0]; s1 = seg[-1]
            g_rm = D[p][s0] + D[s1][q] - D[p][q]
            if g_rm <= 1e-10:
                continue
            best = None
            for e, o in ((s0, s1), (s1, s0)):
                for c in neigh[e]:
                    dec = D[e][c]
                    if dec >= g_rm:
                        break
                    if c in seg:
                        continue
                    jc = pos[c]
                    for c2 in (t[(jc + 1) % n], t[(jc - 1) % n]):
                        if c2 in seg:
                            continue
                        delta = dec + D[o][c2] - D[c][c2] - g_rm
                        if delta < -1e-10 and (best is None or delta < best[0]):
                            best = (delta, c, c2, e)
            if best is not None:
                delta, c, c2, e = best
                r0 = (ia + L) % n
                rot = t[r0:] + t[:r0]
                rest = rot[:n - L]
                ic = rest.index(c)
                sg = seg if e == s0 else seg[::-1]
                if rest[(ic + 1) % len(rest)] == c2:
                    new = rest[:ic + 1] + sg + rest[ic + 1:]
                else:
                    new = rest[:ic] + sg[::-1] + rest[ic:]
                t[:] = new
                repos(t, pos)
                gain_total -= delta
                for x in (p, q, c, c2, s0, s1):
                    if not inq[x]:
                        inq[x] = True; queue.append(x)
                improved = True
                break
        if improved and not inq[a]:
            inq[a] = True; queue.append(a)
    return gain_total


def tour_len(t, D):
    return sum(D[t[i - 1]][t[i]] for i in range(len(t)))


def setup(points, k):
    n = len(points)
    D = [[math.dist(p, q) for q in points] for p in points]
    k = min(k, n - 1)
    neigh = [[j for _, j in sorted(zip(D[i], range(n))) if j != i][:k] for i in range(n)]
    return D, neigh


def nn_tour(n, D):
    left = set(range(1, n)); t = [0]
    while left:
        r = D[t[-1]]
        nx = min(left, key=lambda j: r[j]); left.remove(nx); t.append(nx)
    return t


def solve(points):
    t0 = CLOCK()
    n = len(points)
    if n <= 7:
        return list(range(n))
    D, neigh = setup(points, K)
    t = greedy(n, D) if INIT == 'greedy' else nn_tour(n, D)
    pos = [0] * n; repos(t, pos)
    ls_run(t, pos, D, neigh, range(n))
    cur = tour_len(t, D)
    best_t = t[:]; best = cur
    rng = random.Random(12345)
    m = max(1, min(MAXSEG, n // 4))
    thr = ACC_T * cur / n
    since = 0
    while True:
        el = CLOCK() - t0
        if el >= BUDGET:
            break
        saved = t[:]; saved_len = cur
        if KICK == 'seg':
            i = rng.randrange(n)
            l1 = rng.randint(1, m); l2 = rng.randint(1, m); l3 = rng.randint(1, m)
            r = t[i:] + t[:i]
            A = r[:1]; B = r[1:1 + l1]; C = r[1 + l1:1 + l1 + l2]
            Dd = r[1 + l1 + l2:1 + l1 + l2 + l3]; E = r[1 + l1 + l2 + l3:]
        else:
            a = rng.randrange(n)
            near = neigh[a]
            ps = {pos[a]}
            while len(ps) < 4:
                ps.add(pos[near[rng.randrange(len(near))]] if rng.random() < 0.7 else rng.randrange(n))
            p1, p2, p3, p4 = sorted(ps)
            r = t
            A = r[:p1 + 1]; B = r[p1 + 1:p2 + 1]; C = r[p2 + 1:p3 + 1]; Dd = r[p3 + 1:p4 + 1]; E = r[p4 + 1:]
        ends = set()
        for s_ in (A, B, C, Dd, E):
            if s_:
                ends.add(s_[0]); ends.add(s_[-1])
        t[:] = A + Dd + C + B + E
        repos(t, pos)
        ls_run(t, pos, D, neigh, list(ends))
        L = tour_len(t, D)
        T = thr * (1.0 - el / BUDGET)
        since += 1
        if L < best - 1e-12:
            best = L; best_t = t[:]; since = 0
        if L < cur - 1e-12 or (T > 0 and L < cur + T) or (STALL and since >= STALL and L < best * 1.02):
            cur = L
            if STALL and since >= STALL:
                since = 0
        else:
            t[:] = saved; cur = saved_len
            repos(t, pos)
    return best_t
