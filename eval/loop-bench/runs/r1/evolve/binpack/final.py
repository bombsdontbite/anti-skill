from collections import Counter

_N = Counter()
_ST = {"min": None}


def _sync(item, bins):
    """Keep _N (gap -> count of open bins) in step; reset when the visible bins disagree."""
    vis = Counter(bins[:-1])
    ok = True
    tot = 0
    for g, c in _N.items():
        if g >= item and c:
            tot += c
            if vis.get(g, 0) != c:
                ok = False
                break
    if ok and tot != len(bins) - 1:
        ok = False
    if not ok:
        _N.clear()
        _N.update(vis)
        _ST["min"] = None
    if _ST["min"] is None or item < _ST["min"]:
        _ST["min"] = item


def _commit(item, bins, pr):
    k = 0
    best = pr[0]
    for i in range(1, len(pr)):
        if pr[i] > best:
            best = pr[i]
            k = i
    g = bins[k]
    if k < len(bins) - 1:
        _N[g] -= 1
        if _N[g] == 0:
            del _N[g]
    if g - item > 0:
        _N[g - item] += 1
    return pr


_K = ((-1, 0.5), (0, 1.0), (1, 0.5))


def _ns(j):
    return 0.5 * _N.get(j - 1, 0) + _N.get(j, 0) + 0.5 * _N.get(j + 1, 0)


def _delta(rem, add, cap):
    """Change in sum of squared kernel-smoothed gap counts when one bin moves from rem to add."""
    ch = {}
    if rem is not None:
        for o, w in _K:
            ch[rem + o] = ch.get(rem + o, 0.0) - w
    if add is not None:
        for o, w in _K:
            ch[add + o] = ch.get(add + o, 0.0) + w
    d = 0.0
    for j, c in ch.items():
        if j <= 0 or j >= cap:
            continue
        v = _ns(j)
        d += 2.0 * v * c + c * c
    return d


def priority(item, bins):
    """Sum-of-squares over smoothed gap counts (neighbouring gaps share), plus a stronger dead-leftover penalty."""
    _sync(item, bins)
    cap = bins[-1]
    mn = _ST["min"]
    n = len(bins)
    pr = []
    for i, g in enumerate(bins):
        r = g - item
        d = _delta(g if i < n - 1 else None, r if r > 0 else None, cap)
        if 0 < r < mn:
            d += 5.0 * r / mn
        pr.append(-d - r / (cap + 1.0))
    return _commit(item, bins, pr)
