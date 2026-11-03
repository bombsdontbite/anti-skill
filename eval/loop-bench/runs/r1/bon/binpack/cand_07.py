from bisect import bisect_right, insort
from collections import deque

_st = {"cap": None, "win": deque(), "sorted": []}
_WIN = 400


def priority(item, bins):
    """Best fit plus a penalty that grows as fewer recent items would fit the leftover room."""
    cap = bins[-1]
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["win"] = deque()
        _st["sorted"] = []
    win = _st["win"]
    srt = _st["sorted"]
    win.append(item)
    insort(srt, item)
    if len(win) > _WIN:
        old = win.popleft()
        del srt[bisect_right(srt, old) - 1]
    n = float(len(srt))
    lam = 0.3 * cap
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
            continue
        frac = bisect_right(srt, r) / n
        out.append(-r - lam * (1.0 - frac))
    out.append(-5.0 * cap)
    return out
