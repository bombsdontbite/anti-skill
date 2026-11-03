import time, random

K = 20
SG_ITERS = 300
SG_TIME = 0.15
BB_NODES = 400000
BB_END = 0.35
T_END = 0.5
ILS_ITERS = 400
MOVES21 = True
LAM_VARIANTS = 0
LAM_NOISE = 0.05
VAR_SLICE = 0.05
RECENTER = False

def solve(values, weights, capacities):
    t0 = time.perf_counter()
    n = len(values); d = len(capacities); V = values
    if n == 0: return []
    w0 = [w[0] for w in weights]
    w1 = [w[1] if d > 1 else 0 for w in weights]
    w2 = [w[2] if d > 2 else 0 for w in weights]
    c0 = capacities[0]; c1 = capacities[1] if d > 1 else 1; c2 = capacities[2] if d > 2 else 1
    if d > 3:
        return _generic(values, weights, capacities)
    idx = range(n)

    def greedy(order):
        l0, l1, l2 = c0, c1, c2; x = [False] * n; v = 0
        for i in order:
            a = w0[i]; b = w1[i]; c = w2[i]
            if a <= l0 and b <= l1 and c <= l2:
                l0 -= a; l1 -= b; l2 -= c; x[i] = True; v += V[i]
        return x, [l0, l1, l2], v

    best = greedy(sorted(idx, key=lambda i: -V[i] / (w0[i] / c0 + w1[i] / c1 + w2[i] / c2)))
    sv = sum(V)
    la, lb, lc = sv / (d * c0) / 2, (sv / (d * c1) / 2 if d > 1 else 0.0), (sv / (d * c2) / 2 if d > 2 else 0.0)
    bestL = float("inf"); bl = (la, lb, lc); mu = 2.0; noimp = 0; it = 0
    rows = list(zip(V, w0, w1, w2))
    while it < SG_ITERS and time.perf_counter() - t0 < SG_TIME:
        it += 1
        L = la * c0 + lb * c1 + lc * c2; g0 = c0; g1 = c1; g2 = c2
        for v, a, b, c in rows:
            r = v - la * a - lb * b - lc * c
            if r > 0:
                L += r; g0 -= a; g1 -= b; g2 -= c
        if d < 3: g2 = 0 if lc == 0 else g2
        if d < 2: g1 = 0 if lb == 0 else g1
        if L < bestL - 1e-9: bestL = L; bl = (la, lb, lc); noimp = 0
        else:
            noimp += 1
            if noimp > 10: mu *= 0.5; noimp = 0
        if it % 10 == 1:
            A, B, Cc = la, lb, lc
            gr = greedy(sorted(idx, key=lambda i: -V[i] / (A * w0[i] + B * w1[i] + Cc * w2[i] + 1e-12)))
            if gr[2] > best[2]: best = gr
        gg = g0 * g0 + g1 * g1 + g2 * g2
        if gg == 0: break
        tgt = best[2]
        step = mu * (L - tgt) / gg if L > tgt else mu * 1e-3 * L / gg
        la = max(0.0, la - step * g0); lb = max(0.0, lb - step * g1); lc = max(0.0, lc - step * g2)
    la, lb, lc = (max(z, 1e-12) for z in bl)
    sw = [la * w0[i] + lb * w1[i] + lc * w2[i] for i in idx]
    order = sorted(idx, key=lambda i: -V[i] / sw[i])
    gr = greedy(order)
    if gr[2] > best[2]: best = gr

    def core_bb(la, lb, lc, K, incumbent, deadline):
        sw = [la * w0[i] + lb * w1[i] + lc * w2[i] for i in idx]
        order = sorted(idx, key=lambda i: -V[i] / sw[i])
        l0, l1, l2 = c0, c1, c2; brk = None
        for r, i in enumerate(order):
            a = w0[i]; b = w1[i]; c = w2[i]
            if a <= l0 and b <= l1 and c <= l2: l0 -= a; l1 -= b; l2 -= c
            else: brk = r; break
        if brk is None: return None
        lo = max(0, brk - K); hi = min(n, brk + K)
        core = order[lo:hi]; m = len(core)
        l0, l1, l2 = c0, c1, c2; base = 0; fixed = []
        for i in order[:lo]:
            a = w0[i]; b = w1[i]; c = w2[i]
            if a <= l0 and b <= l1 and c <= l2:
                l0 -= a; l1 -= b; l2 -= c; base += V[i]; fixed.append(i)
        cv = [V[i] for i in core]; ca = [w0[i] for i in core]; cb = [w1[i] for i in core]
        cc = [w2[i] for i in core]; cs = [sw[i] for i in core]
        bb = [incumbent - base, None]; sel = [False] * m; cnt = [0]

        def dfs(p, val, l0, l1, l2):
            cnt[0] += 1
            if cnt[0] & 1023 == 0 and (cnt[0] > BB_NODES or time.perf_counter() > deadline): raise TimeoutError
            if val > bb[0]: bb[0] = val; bb[1] = [core[q] for q in range(p) if sel[q]]
            if p == m: return
            cap = la * l0 + lb * l1 + lc * l2; b = val
            for q in range(p, m):
                s = cs[q]
                if s <= cap: cap -= s; b += cv[q]
                else: b += cv[q] * cap / s; break
            if b <= bb[0] + 1e-9: return
            a = ca[p]; bw = cb[p]; c = cc[p]
            if a <= l0 and bw <= l1 and c <= l2:
                sel[p] = True
                dfs(p + 1, val + cv[p], l0 - a, l1 - bw, l2 - c)
                sel[p] = False
            dfs(p + 1, val, l0, l1, l2)
        try: dfs(0, 0, l0, l1, l2)
        except TimeoutError: pass
        if bb[1] is None: return None
        x = [False] * n; v = base
        for i in fixed: x[i] = True
        for i in bb[1]: x[i] = True; v += V[i]
        u0 = c0 - sum(w0[i] for i in idx if x[i]); u1 = c1 - sum(w1[i] for i in idx if x[i]); u2 = c2 - sum(w2[i] for i in idx if x[i])
        return (x, [u0, u1, u2], v)

    r = core_bb(la, lb, lc, K, best[2], t0 + BB_END)
    if r is not None and r[2] > best[2]: best = r
    vr = random.Random(3)
    for _v in range(LAM_VARIANTS):
        if time.perf_counter() - t0 > BB_END: break
        f0 = 1 + LAM_NOISE * (2 * vr.random() - 1); f1 = 1 + LAM_NOISE * (2 * vr.random() - 1); f2 = 1 + LAM_NOISE * (2 * vr.random() - 1)
        r = core_bb(la * f0, lb * f1, lc * f2, K, best[2], min(t0 + BB_END, time.perf_counter() + VAR_SLICE))
        if r is not None and r[2] > best[2]: best = r

    def fill(x, left, cur, ordr):
        l0, l1, l2 = left
        for j in ordr:
            if not x[j]:
                a = w0[j]; b = w1[j]; c = w2[j]
                if a <= l0 and b <= l1 and c <= l2:
                    x[j] = True; cur += V[j]; l0 -= a; l1 -= b; l2 -= c
        left[0] = l0; left[1] = l1; left[2] = l2
        return cur

    byval = sorted(idx, key=lambda j: -V[j])

    def ls(x, left, cur):
        cur = fill(x, left, cur, order)
        while time.perf_counter() - t0 < T_END:
            outs = [j for j in byval if not x[j]]
            done = False
            for i in idx:
                if not x[i]: continue
                vi = V[i]; r0 = left[0] + w0[i]; r1 = left[1] + w1[i]; r2 = left[2] + w2[i]
                for j in outs:
                    if V[j] <= vi: break
                    if w0[j] <= r0 and w1[j] <= r1 and w2[j] <= r2:
                        x[i] = False; x[j] = True; cur += V[j] - vi
                        left[0] = r0 - w0[j]; left[1] = r1 - w1[j]; left[2] = r2 - w2[j]
                        done = True; break
                if done: break
            if not done and MOVES21:
                for i in idx:
                    if not x[i]: continue
                    vi = V[i]; r0 = left[0] + w0[i]; r1 = left[1] + w1[i]; r2 = left[2] + w2[i]
                    gain = 0; add = []
                    for j in outs:
                        a = w0[j]; b = w1[j]; c = w2[j]
                        if a <= r0 and b <= r1 and c <= r2:
                            add.append(j); gain += V[j]; r0 -= a; r1 -= b; r2 -= c
                    if gain > vi:
                        x[i] = False; cur += gain - vi
                        for j in add: x[j] = True
                        left[0] = r0; left[1] = r1; left[2] = r2
                        done = True; break
            if not done: break
            cur = fill(x, left, cur, order)
        return cur

    x, left, cur = best; x = list(x); left = list(left)
    cur = ls(x, left, cur)
    bx = list(x); bv = cur
    if ILS_ITERS:
        rng = random.Random(1)
        eff = [V[i] / sw[i] for i in idx]
        for _ in range(ILS_ITERS):
            if time.perf_counter() - t0 > T_END: break
            y = list(x); ly = list(left); cy = cur
            ins = [i for i in idx if y[i]]
            if not ins: break
            for _k in range(rng.randint(1, 3)):
                i = ins[rng.randrange(len(ins))]
                if y[i]:
                    y[i] = False; cy -= V[i]; ly[0] += w0[i]; ly[1] += w1[i]; ly[2] += w2[i]
            cand = [j for j in idx if not y[j]]
            cand.sort(key=lambda j: -eff[j] * (0.9 + 0.2 * rng.random()))
            cy = fill(y, ly, cy, cand)
            cy = ls(y, ly, cy)
            if cy >= cur:
                x, left, cur = y, ly, cy
                if cur > bv: bv = cur; bx = list(x)
    if RECENTER and time.perf_counter() - t0 < T_END:
        eff2 = [V[i] / sw[i] for i in idx]
        ins = sorted((i for i in idx if bx[i]), key=lambda i: eff2[i])
        outs = sorted((i for i in idx if not bx[i]), key=lambda i: -eff2[i])
        core = sorted(ins[:K] + outs[:K], key=lambda i: -eff2[i]); m = len(core)
        cset = set(core)
        l0, l1, l2 = c0, c1, c2; base = 0; fixed = []
        for i in idx:
            if bx[i] and i not in cset:
                l0 -= w0[i]; l1 -= w1[i]; l2 -= w2[i]; base += V[i]; fixed.append(i)
        cv = [V[i] for i in core]; ca = [w0[i] for i in core]; cb = [w1[i] for i in core]
        cc = [w2[i] for i in core]; cs = [sw[i] for i in core]
        bb = [bv - base, None]; sel = [False] * m; cnt = [0]; dl = t0 + T_END

        def dfs2(p, val, l0, l1, l2):
            cnt[0] += 1
            if cnt[0] & 1023 == 0 and (cnt[0] > BB_NODES or time.perf_counter() > dl): raise TimeoutError
            if val > bb[0]: bb[0] = val; bb[1] = [core[q] for q in range(p) if sel[q]]
            if p == m: return
            cap = la * l0 + lb * l1 + lc * l2; b = val
            for q in range(p, m):
                s_ = cs[q]
                if s_ <= cap: cap -= s_; b += cv[q]
                else: b += cv[q] * cap / s_; break
            if b <= bb[0] + 1e-9: return
            a = ca[p]; bw = cb[p]; c = cc[p]
            if a <= l0 and bw <= l1 and c <= l2:
                sel[p] = True
                dfs2(p + 1, val + cv[p], l0 - a, l1 - bw, l2 - c)
                sel[p] = False
            dfs2(p + 1, val, l0, l1, l2)
        try: dfs2(0, 0, l0, l1, l2)
        except TimeoutError: pass
        if bb[1] is not None:
            bx = [False] * n
            for i in fixed: bx[i] = True
            for i in bb[1]: bx[i] = True
    return [i for i in idx if bx[i]]


def _generic(values, weights, capacities):
    n = len(values); d = len(capacities)
    order = sorted(range(n), key=lambda i: -values[i] / sum(weights[i][k] / capacities[k] for k in range(d)))
    left = list(capacities); out = []
    for i in order:
        if all(weights[i][k] <= left[k] for k in range(d)):
            for k in range(d): left[k] -= weights[i][k]
            out.append(i)
    return out
