from itertools import groupby


def usage_report(sessions, windows):
    """Integer-keyed event sort (pos*3 + kind), groupby per position, then a
    single sweep that records F and both counts at each query position."""
    if not windows:
        return []
    ev = []
    for s, e, r in sessions:
        ev.append((s * 3 + 2, r))
        ev.append((e * 3, -r))
    for lo, hi in windows:
        ev.append((lo * 3 + 1, 0))
        ev.append((hi * 3 + 1, 0))
    ev.sort()
    F = {}
    CS = {}
    CE = {}
    slope = 0
    f = 0
    ns = 0
    ne = 0
    prev = None
    for key, grp in groupby(ev, key=lambda p: p[0]):
        x, kind = divmod(key, 3)
        if prev is not None:
            f += slope * (x - prev)
        prev = x
        if kind == 1:
            F[x] = f
            CS[x] = ns
            CE[x] = ne
        else:
            for _, dr in grp:
                slope += dr
                if kind == 2:
                    ns += 1
                else:
                    ne += 1
    return [(F[hi] - F[lo], CS[hi] - CE[lo]) for lo, hi in windows]
