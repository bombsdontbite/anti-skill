from collections import Counter

_st = {"cap": None, "gaps": Counter()}


def _visible_total(gaps, item):
    t = 0
    for g, c in gaps.items():
        if g >= item:
            t += c
    return t


def priority(item, bins):
    """Sum-of-squares: keep the number of open bins at each gap level as even as possible.

    The full gap histogram (including bins too full to show) is tracked from our own choices,
    and rebuilt from the visible bins whenever it disagrees with them.
    """
    cap = bins[-1]
    gaps = _st["gaps"]
    vis = Counter(bins[:-1])
    ok = _st["cap"] == cap and _visible_total(gaps, item) == len(bins) - 1
    if ok:
        for g, c in vis.items():
            if gaps.get(g, 0) != c:
                ok = False
                break
    if not ok:
        gaps = Counter(vis)
        _st["gaps"] = gaps
        _st["cap"] = cap

    out = []
    scale = 10.0 * cap
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            delta = -2 * gaps[b] + 1
        else:
            delta = 2 * (gaps.get(r, 0) - gaps[b]) + 2
        out.append(-delta - r / scale)
    r = cap - item
    delta = 2 * gaps.get(r, 0) + 1
    out.append(-delta - r / scale - 1e-9)

    best = 0
    for k in range(1, len(out)):
        if out[k] > out[best]:
            best = k
    if best < len(bins) - 1:
        h = bins[best]
        gaps[h] -= 1
        if gaps[h] == 0:
            del gaps[h]
    nr = bins[best] - item
    if nr > 0:
        gaps[nr] = gaps.get(nr, 0) + 1
    return out
