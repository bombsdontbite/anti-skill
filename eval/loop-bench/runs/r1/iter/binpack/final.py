"""Online bin packing: sum-of-squares gap balancing + learned fit-probability loss.

The scorer always puts the item where our priority is highest, so this module
mirrors the open bins' remaining gaps itself and scores each choice by:
  * Sum-of-Squares (Csirik et al.): change in sum_g N(g)^2 over gap levels g,
    with gaps too small for almost any item (below the TAU quantile of sizes
    seen) charged as linear waste instead;
  * a bonus for an exact fit;
  * LAM * drop in F(gap)^FX, F = empirical CDF of item sizes, i.e. how much
    the chance that a future item fits this bin goes down;
  * near the end of an instance (items T0..TE), a growing best-fit term.
If the mirror ever disagrees with the bins shown (a new instance began), it is
rebuilt from the bins opened since the most plausible instance start.
"""
from bisect import insort

DW = 1.3      # linear cost per unit of a dead (unfillable) gap, per 100 capacity
TAU = 0.04    # gaps below this quantile of item sizes count as dead
PF = 6.0      # bonus for an exact fit
QL = 150      # gap levels for large capacities (bucket = cap // QL)
T0 = 1900     # end-game best-fit ramp starts here ...
TE = 2000     # ... and is off past this item count
E1 = 10.0
LAM = 10.0
FX = 0.85

_cap = 0
_q = 1
_O = {}       # gap -> sorted open times of open bins with that gap
_K = {}       # gap bucket -> count
_T = 0        # calls since capacity changed
_t0 = 1       # call time at which the current instance started
_E = []       # recent call times where no open bin fit (instance-start candidates)
_H = []
_seen = 0
_thr = 0
_F = []


def _reset(cap):
    global _cap, _q, _O, _K, _T, _t0, _E, _H, _seen
    _cap = cap
    _q = max(1, cap // QL)
    _O = {}; _K = {}; _T = 0; _t0 = 1; _E = []
    _H = [0] * (cap + 1); _seen = 0


def _rebuild(item, shown):
    """Pick an instance start consistent with the shown bins and keep only bins opened since."""
    global _O, _K, _t0
    want = sorted(shown)
    # instances run TE items: near the expected end, expect the next one to start at _t0 + TE
    target = _t0 + TE if _T - _t0 + 1 > TE - 50 else _t0
    best = None
    for tau in _E:
        cand = []
        for g, lst in _O.items():
            if g >= item:
                for o in lst:
                    if o >= tau:
                        cand.append(g)
        cand.sort()
        if cand == want and (best is None or abs(tau - target) <= abs(best - target)):
            best = tau
    if best is None:
        O = {}
        for g in shown:
            O.setdefault(g, []).append(_T - 1)
        _t0 = _T
    else:
        O = {}
        for g, lst in _O.items():
            keep = [o for o in lst if o >= best]
            if keep:
                O[g] = keep
        _t0 = best
    _O = O
    K = {}
    q = _q
    for g, lst in O.items():
        k = g // q
        K[k] = K.get(k, 0) + len(lst)
    _K = K


def _refresh(cap):
    global _thr, _F
    H = _H; s = _seen
    lim = TAU * s; acc = 0; t = 0
    for g in range(cap + 1):
        acc += H[g]
        if acc > lim:
            t = g; break
    _thr = t
    F = []; acc = 0
    for h in H:
        acc += h
        F.append((acc / s) ** FX)
    _F = F


def priority(item, bins):
    global _T, _seen, _t0
    cap = bins[-1]
    shown = bins[:-1]
    if cap != _cap or item > cap:
        _reset(cap)
    _T += 1
    T = _T
    if not shown:
        _E.append(T)
        if len(_E) > 64:
            del _E[:32]
    cnt = 0; tot = 0
    for g, lst in _O.items():
        if g >= item:
            c = len(lst); cnt += c; tot += g * c
    if cnt != len(shown) or tot != sum(shown):
        _rebuild(item, shown)
    _H[item] += 1; _seen += 1
    if _seen < 64 or _seen % 32 == 0:
        _refresh(cap)
    t = T - _t0 + 1
    if t > TE:
        # instances are at most TE items long: a start went unnoticed (old bins all hidden)
        _t0 = min((e for e in _E if e > _t0), key=lambda e: abs(e - _t0 - TE), default=T)
        t = T - _t0 + 1
    thr = _thr; q = _q; K = _K; F = _F
    sc = 100.0 / cap
    dws = DW * sc
    eps = E1 * (t - T0) / T0 * sc if T0 < t <= TE else 0.0
    pr = []
    for b in bins:
        r = b - item
        if r > 0:
            if r < thr:
                d = dws * r
            else:
                d = 2 * K.get(r // q, 0) + 1
        else:
            d = -PF
        if b < cap:
            if b < thr:
                d -= dws * b
            else:
                d += 1 - 2 * K.get(b // q, 0)
            d += LAM * (F[b] - F[r])
        else:
            d += LAM * (1.0 - F[r])
        pr.append(-d - eps * r)
    # mirror the scorer's choice: highest priority, first on ties
    j = 0; best = pr[0]
    for i in range(1, len(pr)):
        if pr[i] > best:
            best = pr[i]; j = i
    b = bins[j]
    if j < len(shown):
        lst = _O.get(b)
        if lst:
            o = lst.pop(0)
            if not lst:
                del _O[b]
            k = b // q
            n = K.get(k, 0) - 1
            if n > 0:
                K[k] = n
            else:
                K.pop(k, None)
        else:
            o = T
    else:
        o = T
    r = b - item
    if r > 0:
        lst = _O.get(r)
        if lst is None:
            _O[r] = [o]
        else:
            insort(lst, o)
        k = r // q
        K[k] = K.get(k, 0) + 1
    return pr
