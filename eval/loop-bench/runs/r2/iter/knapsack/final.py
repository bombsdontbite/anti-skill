import time
import random


def solve(values, weights, capacities):
    t0 = time.perf_counter()
    TL = 0.6
    n = len(values)
    d = len(capacities)
    caps = list(capacities)
    items = [i for i in range(n) if all(weights[i][k] <= caps[k] for k in range(d))]
    if not items:
        return []
    nw = [[weights[i][k] / caps[k] for k in range(d)] for i in range(n)]
    V = values
    W = [list(w) for w in weights]

    def make_order(mu):
        dens = []
        for i in items:
            load = 0.0
            w = nw[i]
            for k in range(d):
                load += mu[k] * w[k]
            dens.append((-(V[i] / load) if load > 0 else -1e300, i))
        dens.sort()
        return [i for _, i in dens]

    def greedy(order):
        left = caps[:]
        val = 0
        sel = []
        for i in order:
            w = W[i]
            ok = True
            for k in range(d):
                if w[k] > left[k]:
                    ok = False
                    break
            if ok:
                for k in range(d):
                    left[k] -= w[k]
                sel.append(i)
                val += V[i]
        return val, sel

    best_val, best_sel = greedy(make_order([1.0] * d))
    mu = [best_val / d] * d
    lam = 1.0
    best_ub = float("inf")
    best_mu = mu[:]
    stall = 0
    for _ in range(400):
        if time.perf_counter() - t0 > TL * 0.2:
            break
        L = sum(mu)
        g = [1.0] * d
        for i in items:
            w = nw[i]
            rc = V[i]
            for k in range(d):
                rc -= mu[k] * w[k]
            if rc > 0:
                L += rc
                for k in range(d):
                    g[k] -= w[k]
        if L < best_ub - 1e-9:
            best_ub = L
            best_mu = mu[:]
            stall = 0
        else:
            stall += 1
            if stall >= 15:
                lam *= 0.5
                stall = 0
                if lam < 1e-4:
                    break
        gn = sum(x * x for x in g)
        if gn < 1e-18:
            break
        step = lam * (L - best_val) / gn
        if step <= 0:
            step = 1e-6 * L
        mu = [max(0.0, mu[k] - step * g[k]) for k in range(d)]
        if sum(mu) == 0:
            mu = [1e-9] * d
    order = make_order([m_ + 1e-12 * best_val for m_ in best_mu])
    v, s = greedy(order)
    if v > best_val:
        best_val, best_sel = v, s
    m = len(order)
    pos = [0] * n
    for r, i in enumerate(order):
        pos[i] = r

    rng = random.Random(12345)
    x = [False] * n
    left = caps[:]
    cur = 0
    for i in best_sel:
        x[i] = True
        for k in range(d):
            left[k] -= W[i][k]
        cur += V[i]
    rd = range(d)

    def fill(x, left, ban):
        add = 0
        for i in order:
            if not x[i] and i not in ban:
                w = W[i]
                for k in rd:
                    if w[k] > left[k]:
                        break
                else:
                    for k in rd:
                        left[k] -= w[k]
                    x[i] = True
                    add += V[i]
        return add

    cur += fill(x, left, ())
    best_val = cur
    best_x = x[:]
    # boundary: rank of the first item not taken by greedy
    it = 0
    last_imp = 0
    while True:
        it += 1
        if (it & 7) == 0 and time.perf_counter() - t0 > TL:
            break
        ins = [i for i in order if x[i]]
        if not ins:
            break
        nx = x[:]
        nl = left[:]
        nv = cur
        q = 1 + int(rng.random() ** 2 * 3.999)
        ni = len(ins)
        ban = set()
        for _ in range(q):
            # biased toward the low-density tail of the selection
            r = ni - 1 - int(ni * (rng.random() ** 3))
            i = ins[r]
            if not nx[i]:
                continue
            nx[i] = False
            w = W[i]
            for k in rd:
                nl[k] += w[k]
            nv -= V[i]
            ban.add(i)
        # optionally force one out item near the boundary
        if rng.random() < 0.5:
            outs_r = ins[-1] if ins else order[0]
            base = pos[outs_r]
            for _t in range(10):
                j = order[min(m - 1, max(0, base + int(rng.gauss(0, 0.08 * m))))]
                if not nx[j] and j not in ban:
                    w = W[j]
                    nx[j] = True
                    for k in rd:
                        nl[k] -= w[k]
                    nv += V[j]
                    # repair
                    while True:
                        viol = [k for k in rd if nl[k] < 0]
                        if not viol:
                            break
                        best_i = -1
                        for r2 in range(ni - 1, -1, -1):
                            i2 = ins[r2]
                            if nx[i2] and any(W[i2][k] > 0 for k in viol):
                                if rng.random() < 0.6:
                                    best_i = i2
                                    break
                                best_i = i2
                        if best_i < 0:
                            break
                        nx[best_i] = False
                        for k in rd:
                            nl[k] += W[best_i][k]
                        nv -= V[best_i]
                        ban.add(best_i)
                    break
        if any(nl[k] < 0 for k in rd):
            continue
        nv += fill(nx, nl, ban)
        if nv >= cur:
            x, left, cur = nx, nl, nv
            if cur > best_val:
                best_val = cur
                best_x = x[:]
                last_imp = it
        elif it - last_imp > 300 and rng.random() < 0.002:
            x, left, cur = best_x[:], None, best_val
            left = caps[:]
            for i in range(n):
                if x[i]:
                    for k in rd:
                        left[k] -= W[i][k]
            last_imp = it
    return [i for i in range(n) if best_x[i]]
