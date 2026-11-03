from collections import Counter, deque

_st = {"cap": None, "recent": deque(maxlen=300), "reach": None, "since": 0}
_TOP = 40
_EVERY = 100


def _rebuild(cap, recent):
    common = [s for s, _ in Counter(recent).most_common(_TOP)]
    ok = [False] * (cap + 1)
    ok[0] = True
    for i in range(len(common)):
        a = common[i]
        if a <= cap:
            ok[a] = True
        for j in range(i, len(common)):
            s = a + common[j]
            if s <= cap:
                ok[s] = True
    reach = [0] * (cap + 1)
    best = 0
    for x in range(cap + 1):
        if ok[x]:
            best = x
        reach[x] = best
    return reach


def priority(item, bins):
    """Best fit judged by the waste left after one or two typical future items fill the gap."""
    cap = int(bins[-1])
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["recent"] = deque(maxlen=300)
        _st["reach"] = None
        _st["since"] = 0
    _st["recent"].append(item)
    _st["since"] += 1
    if (_st["reach"] is None and _st["since"] >= 30) or _st["since"] >= _EVERY:
        _st["reach"] = _rebuild(cap, _st["recent"])
        _st["since"] = 0
    reach = _st["reach"]
    out = []
    for b in bins[:-1]:
        r = int(b - item)
        if r == 0:
            out.append(float(cap) * 2)
        elif reach is None:
            out.append(-float(r))
        else:
            out.append(-(r - reach[r]) - 0.25 * r)
    out.append(-5.0 * cap)
    return out
