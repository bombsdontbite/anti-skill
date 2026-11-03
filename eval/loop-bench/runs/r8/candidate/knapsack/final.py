import time

def solve(values, weights, capacities):
    t0 = time.time(); T = 0.45
    n = len(values); d = len(capacities); V = values; W = weights; C = capacities
    R = range(d)

    # Lagrangian multipliers by coordinate descent on the dual
    lam = [sum(V) / sum(sum(w) for w in W)] * d
    for sweep in range(30):
        old = lam[:]
        for k in R:
            base = [V[i] - sum(lam[q] * W[i][q] for q in R if q != k) for i in range(n)]
            items = sorted(((base[i] / W[i][k], W[i][k]) for i in range(n) if base[i] > 0), reverse=True)
            acc = 0; t = 0.0
            for bp, w in items:
                acc += w
                if acc > C[k]:
                    t = bp; break
            lam[k] = t
        if max(abs(a - b) for a, b in zip(lam, old)) < 1e-12: break
    red = [V[i] - sum(lam[k] * W[i][k] for k in R) for i in range(n)]

    def fill(x, left, val, order):
        for i in order:
            if not x[i]:
                wi = W[i]
                if all(wi[k] <= left[k] for k in R):
                    for k in R: left[k] -= wi[k]
                    x[i] = 1; val += V[i]
        return val

    # incumbents: several density greedies, keep best, then swap local search
    best = None
    mults = [[1.0 / C[k] for k in R], lam[:]]
    m = [1.0 / C[k] for k in R]
    for it in range(20):
        dens = [V[i] / (sum(m[k] * W[i][k] for k in R) or 1e-12) for i in range(n)]
        order = sorted(range(n), key=lambda i: -dens[i])
        x = [0] * n; left = list(C); val = fill(x, left, 0, order)
        if best is None or val > best[0]: best = (val, x, left, order)
        used = [(C[k] - left[k]) / C[k] for k in R]
        m = [m[k] * (1 + 0.3 * (used[k] - sum(used) / d)) for k in R]
    if any(l > 0 for l in lam):
        order = sorted(range(n), key=lambda i: -V[i] / (sum(lam[k] * W[i][k] for k in R) or 1e-12))
        x = [0] * n; left = list(C); val = fill(x, left, 0, order)
        if val > best[0]: best = (val, x, left, order)
    val, x, left, order = best
    improved = True
    while improved and time.time() - t0 < T * 0.4:
        improved = False
        for i in order:
            if x[i]: continue
            wi = W[i]
            if all(wi[k] <= left[k] for k in R):
                x[i] = 1
                for k in R: left[k] -= wi[k]
                val += V[i]; improved = True; continue
            bj = -1; bg = 0
            for j in range(n):
                if x[j] and V[i] - V[j] > bg:
                    wj = W[j]
                    if all(wi[k] - wj[k] <= left[k] for k in R):
                        bj = j; bg = V[i] - V[j]
            if bj >= 0:
                wj = W[bj]
                for k in R: left[k] -= wi[k] - wj[k]
                x[i] = 1; x[bj] = 0; val += bg; improved = True
    bval, bx = val, x[:]

    # DFS branch and bound, items in order of decreasing reduced cost, Lagrangian bound
    idx = sorted(range(n), key=lambda i: -abs(red[i]))
    rv = [red[i] for i in idx]
    pos_suffix = [0.0] * (n + 1)
    for p in range(n - 1, -1, -1):
        pos_suffix[p] = pos_suffix[p + 1] + max(0.0, rv[p])
    lamC = lam
    cur = [0] * n
    left = list(C)
    nodes = [0]
    timeout = [False]

    def dfs(p, val):
        nonlocal bval, bx
        nodes[0] += 1
        if nodes[0] & 1023 == 0 and time.time() - t0 > T:
            timeout[0] = True
        if timeout[0]: return
        # bound: val + lam.left + sum positive reduced costs of remaining
        ub = val + sum(lamC[k] * left[k] for k in R) + pos_suffix[p]
        if ub <= bval + 0.5: return
        if p == n:
            if val > bval:
                bval = val; bx = [0] * n
                for q in range(n):
                    if cur[q]: bx[idx[q]] = 1
            return
        i = idx[p]; wi = W[i]
        if rv[p] >= 0:
            if all(wi[k] <= left[k] for k in R):
                for k in R: left[k] -= wi[k]
                cur[p] = 1; dfs(p + 1, val + V[i]); cur[p] = 0
                for k in R: left[k] += wi[k]
            dfs(p + 1, val)
        else:
            dfs(p + 1, val)
            if all(wi[k] <= left[k] for k in R) and ub + rv[p] > bval + 0.5:
                for k in R: left[k] -= wi[k]
                cur[p] = 1; dfs(p + 1, val + V[i]); cur[p] = 0
                for k in R: left[k] += wi[k]

    dfs(0, 0)
    return [i for i in range(n) if bx[i]]
