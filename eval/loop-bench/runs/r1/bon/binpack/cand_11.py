from collections import Counter

_st = {"cap": None, "cnt": Counter(), "n": 0}


def priority(item, bins):
    """Best fit with a bonus when the leftover equals a size that has been arriving often."""
    cap = bins[-1]
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["cnt"] = Counter()
        _st["n"] = 0
    cnt = _st["cnt"]
    cnt[item] += 1
    _st["n"] += 1
    n = float(_st["n"])
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        bonus = min(0.3 * cap, 2.0 * cap * cnt.get(r, 0) / n)
        out.append(-r + bonus)
    out.append(-5.0 * cap)
    return out
