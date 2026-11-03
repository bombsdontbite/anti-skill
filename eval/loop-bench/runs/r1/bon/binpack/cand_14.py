from bisect import bisect_right, insort
from collections import deque

_st = {"cap": None, "win": deque(), "srt": []}
_WIN = 500


def priority(item, bins):
    """Best fit; leftovers below the 10th percentile of recent sizes are penalised in proportion."""
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
    q = float(srt[len(srt) // 10])
    out = []
    for b in bins[:-1]:
        r = b - item
        if r == 0:
            out.append(float(cap))
        elif r < q:
            out.append(-r - 0.5 * cap * (q - r) / q)
        else:
            out.append(-float(r))
    out.append(-5.0 * cap)
    return out
