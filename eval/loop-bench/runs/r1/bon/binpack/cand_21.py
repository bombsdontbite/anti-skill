from bisect import bisect_right
from collections import deque

_st = {"cap": None, "recent": deque(maxlen=150), "sizes": [], "since": 0}


def priority(item, bins):
    """Best fit with a bonus when a recently seen size would nearly close the leftover."""
    cap = bins[-1]
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["recent"] = deque(maxlen=150)
        _st["sizes"] = []
        _st["since"] = 0
    _st["recent"].append(item)
    _st["since"] += 1
    if _st["since"] >= 25 or not _st["sizes"]:
        _st["sizes"] = sorted(set(_st["recent"]))
        _st["since"] = 0
    sizes = _st["sizes"]
    tol = 0.01 * cap
    bonus = 0.1 * cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        k = bisect_right(sizes, r)
        p = -float(r)
        if k and r - sizes[k - 1] <= tol:
            p += bonus
        out.append(p)
    out.append(-5.0 * cap)
    return out
