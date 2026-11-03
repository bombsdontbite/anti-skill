from bisect import bisect_right, insort
from collections import deque

_st = {"cap": None, "win": deque(), "srt": []}
_WIN = 300


def priority(item, bins):
    """Exact fit, then best fit among leftovers a median item could still use, then the rest."""
    cap = bins[-1]
    if _st["cap"] != cap:
        _st["cap"] = cap
        _st["win"] = deque()
        _st["srt"] = []
    win, srt = _st["win"], _st["srt"]
    win.append(item)
    insort(srt, item)
    if len(win) > _WIN:
        old = win.popleft()
        del srt[bisect_right(srt, old) - 1]
    med = srt[len(srt) // 2]
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
        elif r >= med:
            out.append(-float(r))
        else:
            out.append(-float(r) - cap)
    out.append(-3.0 * cap)
    return out
