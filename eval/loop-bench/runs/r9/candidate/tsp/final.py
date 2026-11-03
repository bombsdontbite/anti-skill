import math
import random
import time

BUDGET = 0.7
K_NEIGH = 6
SEG_MIN, SEG_SPAN = 20, 80
ACCEPT = 0.0
MAX_ITERS = 0
STATS = {}


def _greedy(n, D, neigh):
    edges = sorted((D[i][j], i, j) for i in range(n) for j in neigh[i] if i < j or i not in neigh[j])
    deg = [0] * n
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    adj = [[] for _ in range(n)]
    for _, i, j in edges:
        if deg[i] < 2 and deg[j] < 2:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
                deg[i] += 1
                deg[j] += 1
                adj[i].append(j)
                adj[j].append(i)
    seen = [False] * n
    frags = []
    for s in range(n):
        if not seen[s] and deg[s] < 2:
            f = [s]
            seen[s] = True
            prev, cur = -1, s
            while True:
                nxts = [x for x in adj[cur] if x != prev and not seen[x]]
                if not nxts:
                    break
                prev, cur = cur, nxts[0]
                seen[cur] = True
                f.append(cur)
            frags.append(f)
    tour = frags.pop(0)
    while frags:
        e = tour[-1]
        bi, brev, bd = 0, False, 1e18
        for k, f in enumerate(frags):
            if D[e][f[0]] < bd:
                bi, brev, bd = k, False, D[e][f[0]]
            if D[e][f[-1]] < bd:
                bi, brev, bd = k, True, D[e][f[-1]]
        f = frags.pop(bi)
        tour += f[::-1] if brev else f
    return tour


def solve(points):
    t0 = time.perf_counter()
    n = len(points)
    if n <= 4:
        return list(range(n))
    rng = random.Random(7)
    D = [[math.dist(p, q) for q in points] for p in points]
    K = min(K_NEIGH, n - 1)
    neigh = [sorted((j for j in range(n) if j != i), key=lambda j: (D[i][j], j))[:K] for i in range(n)]
    nd = [[(c, D[i][c]) for c in neigh[i]] for i in range(n)]
    t = _greedy(n, D, neigh)
    pos = [0] * n
    for i, c in enumerate(t):
        pos[c] = i
    EPS = 1e-10

    def improve(queue):
        total = 0.0
        inq = [False] * n
        for c in queue:
            inq[c] = True
        while queue:
            a = queue.pop()
            inq[a] = False
            ia = pos[a]
            Da = D[a]
            an = t[ia + 1 - n]
            ap = t[ia - 1]
            moved = None
            # 2-opt, successor direction then predecessor direction
            dab = Da[an]
            for c, dac in nd[a]:
                g1 = dab - dac
                if g1 <= EPS:
                    break
                ic = pos[c]
                d = t[ic + 1 - n]
                if d == a or c == an:
                    continue
                Dd = D[d]
                g = g1 + Dd[c] - Dd[an]
                if g > EPS:
                    i, j = ia + 1, ic
                    ln = (j - i) % n + 1
                    if 2 * ln > n:
                        i, j, ln = ic + 1, ia, n - ln
                    i %= n
                    for _ in range(ln >> 1):
                        x, y = t[i], t[j]
                        t[i] = y
                        t[j] = x
                        pos[y] = i
                        pos[x] = j
                        i += 1
                        if i == n:
                            i = 0
                        j -= 1
                        if j < 0:
                            j = n - 1
                    total += g
                    moved = (a, an, c, d)
                    break
            if moved is None:
                dab = Da[ap]
                for c, dac in nd[a]:
                    g1 = dab - dac
                    if g1 <= EPS:
                        break
                    ic = pos[c]
                    d = t[ic - 1]
                    if d == a or c == ap:
                        continue
                    Dd = D[d]
                    g = g1 + Dd[c] - Dd[ap]
                    if g > EPS:
                        i, j = ic, ia - 1
                        ln = (j - i) % n + 1
                        if 2 * ln > n:
                            i, j, ln = ia, ic - 1, n - ln
                        i %= n
                        j %= n
                        for _ in range(ln >> 1):
                            x, y = t[i], t[j]
                            t[i] = y
                            t[j] = x
                            pos[y] = i
                            pos[x] = j
                            i += 1
                            if i == n:
                                i = 0
                            j -= 1
                            if j < 0:
                                j = n - 1
                        total += g
                        moved = (a, ap, c, d)
                        break
            if moved is None:
                # or-opt: move segment t[ia .. ia+L-1] between c and a tour neighbour e of c
                for L in (1, 2, 3):
                    if L > n - 3:
                        break
                    s1 = t[(ia + L - 1) % n]
                    q = t[(ia + L) % n]
                    gain0 = Da[ap] + D[s1][q] - D[ap][q]
                    if gain0 <= EPS:
                        continue
                    for end, other in ((a, s1), (s1, a)):
                        Do = D[other]
                        for c, dc in nd[end]:
                            if dc >= gain0:
                                break
                            ic = pos[c]
                            if (ic - ia) % n < L:
                                continue
                            Dc = D[c]
                            for e in (t[ic + 1 - n], t[ic - 1]):
                                ie = pos[e]
                                if (ie - ia) % n < L:
                                    continue
                                g = gain0 - dc - Do[e] + Dc[e]
                                if g > EPS:
                                    seg = [t[(ia + k) % n] for k in range(L)]
                                    rest = [t[(ia + L + k) % n] for k in range(n - L)]
                                    jc = (ic - ia - L) % n
                                    je = (ie - ia - L) % n
                                    if je == jc + 1:
                                        ins = seg if end == seg[0] else seg[::-1]
                                        t[:] = rest[:jc + 1] + ins + rest[jc + 1:]
                                    else:
                                        ins = seg if end == seg[-1] else seg[::-1]
                                        t[:] = rest[:je + 1] + ins + rest[je + 1:]
                                    for k, x in enumerate(t):
                                        pos[x] = k
                                    total += g
                                    moved = (ap, q, c, e, a, s1)
                                    break
                            if moved:
                                break
                        if moved:
                            break
                    if moved:
                        break
            if moved:
                for x in moved:
                    if not inq[x]:
                        inq[x] = True
                        queue.append(x)
        return total

    improve(list(range(n)))
    cur_len = sum(D[t[k - 1]][t[k]] for k in range(n))
    cur, cur_pos = t[:], pos[:]
    best, best_len = cur[:], cur_len
    if n < 8:
        return best
    thr = ACCEPT * best_len / n
    iters = 0
    while time.perf_counter() - t0 < BUDGET:
        iters += 1
        if MAX_ITERS and iters > MAX_ITERS:
            break
        seglen = min(n - 1, SEG_MIN + rng.randrange(SEG_SPAN))
        if rng.random() < 0.05 or seglen >= n - 1:
            st = rng.randrange(n)
            cur = cur[st:] + cur[:st]
            for k, x in enumerate(cur):
                cur_pos[x] = k
            st = 0
        else:
            st = rng.randrange(n - seglen)
        p1, p2, p3 = sorted(rng.sample(range(st + 1, st + seglen), 3))
        t[:] = cur
        pos[:] = cur_pos
        p3n = p3 % n
        kick = (D[t[p1 - 1]][t[p2]] + D[t[p3 - 1]][t[p1]] + D[t[p2 - 1]][t[p3n]]
                - D[t[p1 - 1]][t[p1]] - D[t[p2 - 1]][t[p2]] - D[t[p3 - 1]][t[p3n]])
        t[p1:p3] = cur[p2:p3] + cur[p1:p2]
        for k in range(p1, p3):
            pos[t[k]] = k
        m = p1 + p3 - p2
        L = cur_len + kick - improve([t[p1 - 1], t[p1], t[m - 1], t[m], t[p3 - 1], t[p3n]])
        if L < cur_len - EPS or (thr and L < best_len + thr):
            cur, cur_len = t[:], L
            cur_pos = pos[:]
            if L < best_len - EPS:
                best, best_len = cur, L
    STATS['iters'] = iters
    return best
