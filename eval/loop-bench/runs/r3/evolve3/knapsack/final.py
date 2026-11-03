import time


def _duals(values, weights, capacities, iters=200):
    d = len(capacities); n = len(values)
    tot = [sum(weights[i][k] for i in range(n)) for k in range(d)]
    lam = [sum(values) / (d * tot[k]) for k in range(d)]
    best = float("inf"); best_lam = lam[:]
    step = 1.0
    for _ in range(iters):
        val = sum(lam[k] * capacities[k] for k in range(d)); g = list(capacities)
        for i in range(n):
            w = weights[i]
            red = values[i] - sum(lam[k] * w[k] for k in range(d))
            if red > 0:
                val += red
                for k in range(d):
                    g[k] -= w[k]
        if val < best:
            best = val; best_lam = lam[:]
        else:
            step *= 0.9
        nrm = sum(x * x for x in g)
        if nrm == 0:
            break
        a = step * 0.05 * best / nrm
        lam = [max(0.0, lam[k] - a * g[k]) for k in range(d)]
    return best_lam


def _greedy(order, weights, capacities, d):
    left = list(capacities); chosen = [False] * len(weights)
    for i in order:
        w = weights[i]
        if all(w[k] <= left[k] for k in range(d)):
            for k in range(d):
                left[k] -= w[k]
            chosen[i] = True
    return chosen, left


def _local(values, weights, chosen, left, d, deadline):
    n = len(values)
    improved = True
    while improved and time.perf_counter() < deadline:
        improved = False
        ins = [i for i in range(n) if chosen[i]]
        outs = [j for j in range(n) if not chosen[j]]
        # add
        for j in outs:
            w = weights[j]
            if all(w[k] <= left[k] for k in range(d)):
                chosen[j] = True
                for k in range(d):
                    left[k] -= w[k]
                improved = True
        if improved:
            continue
        # 1-1 swap: best improving
        best = 0; bp = None
        outs.sort(key=lambda j: -values[j])
        for i in ins:
            wi = weights[i]; vi = values[i]
            room = [left[k] + wi[k] for k in range(d)]
            for j in outs:
                if values[j] <= vi + best:
                    break
                wj = weights[j]
                if all(wj[k] <= room[k] for k in range(d)):
                    best = values[j] - vi; bp = (i, j)
                    break
        if bp:
            i, j = bp
            chosen[i] = False; chosen[j] = True
            for k in range(d):
                left[k] += weights[i][k] - weights[j][k]
            improved = True
    return chosen, left



def _bb(values, weights, capacities, lam, inc_v, inc, deadline):
    """DFS branch and bound, surrogate Dantzig bound; all real constraints checked."""
    d = len(capacities); n = len(values)
    s = [sum(lam[k] * weights[i][k] for k in range(d)) or 1e-12 for i in range(n)]
    S = sum(lam[k] * capacities[k] for k in range(d))
    order = sorted(range(n), key=lambda i: -values[i] / s[i])
    V = [values[i] for i in order]; SW = [s[i] for i in order]; Wt = [weights[i] for i in order]
    best = [inc_v, set(inc)]
    left = list(capacities); take = []
    cnt = [0]

    def bound(pos, sl, val):
        while pos < n and SW[pos] <= sl:
            sl -= SW[pos]; val += V[pos]; pos += 1
        if pos < n:
            val += V[pos] * sl / SW[pos]
        return val

    def rec(pos, sl, val):
        cnt[0] += 1
        if (cnt[0] & 1023) == 0 and time.perf_counter() > deadline:
            raise TimeoutError
        if val > best[0]:
            best[0] = val; best[1] = set(order[p] for p in take)
        if pos >= n or sl <= 0:
            return
        if bound(pos, sl, val) <= best[0] + 1e-9:
            return
        w = Wt[pos]
        if all(w[k] <= left[k] for k in range(d)):
            for k in range(d):
                left[k] -= w[k]
            take.append(pos)
            rec(pos + 1, sl - SW[pos], val + V[pos])
            take.pop()
            for k in range(d):
                left[k] += w[k]
        rec(pos + 1, sl, val)



    try:
        rec(0, S, 0)
    except TimeoutError:
        pass
    return best[0], best[1]


def solve(values, weights, capacities):
    t0 = time.perf_counter(); deadline = t0 + 0.6
    d = len(capacities); n = len(values)
    lam = _duals(values, weights, capacities)
    def dens(i):
        load = sum(lam[k] * weights[i][k] for k in range(d))
        return values[i] / load if load > 0 else float("inf")
    order = sorted(range(n), key=lambda i: (-dens(i), i))
    chosen, left = _greedy(order, weights, capacities, d)
    chosen, left = _local(values, weights, chosen, left, d, deadline)
    inc = [i for i in range(n) if chosen[i]]
    v, sol = _bb(values, weights, capacities, lam, sum(values[i] for i in inc), inc, deadline)
    return sorted(sol)
