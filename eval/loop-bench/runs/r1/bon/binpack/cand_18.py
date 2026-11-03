from collections import Counter

_st = {"cap": None, "cnt": Counter(), "n": 0, "fill": None, "since": 0}


def _rebuild(cap, cnt, n):
    floor = max(1, n // 100)
    present = [False] * (cap + 1)
    for s, c in cnt.items():
        if c >= floor and s <= cap:
            present[s] = True
    fill = [0] * (cap + 1)
    best = 0
    for x in range(cap + 1):
        if present[x]:
            best = x
        fill[x] = best
    return fill


def priority(item, bins):
    """Rank a leftover by what remains after the largest common size that fits it."""
    cap = int(bins[-1])
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["cnt"] = Counter()
        _st["n"] = 0
        _st["fill"] = None
        _st["since"] = 0
    _st["cnt"][item] += 1
    _st["n"] += 1
    _st["since"] += 1
    if _st["fill"] is None or _st["since"] >= 50:
        _st["fill"] = _rebuild(cap, _st["cnt"], _st["n"])
        _st["since"] = 0
    fill = _st["fill"]
    out = []
    for b in bins[:-1]:
        r = int(b - item)
        if r == 0:
            out.append(float(cap) * 2)
        else:
            out.append(-(r - fill[r]) - 0.2 * r)
    out.append(-float(cap) * 5)
    return out
