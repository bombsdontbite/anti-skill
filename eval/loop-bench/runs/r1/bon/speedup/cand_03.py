from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Slope/intercept deltas per coordinate: F(t) = slope(t) * t + icpt(t)."""
    delta = {}
    for s, e, r in sessions:
        d = delta.get(s)
        if d is None:
            delta[s] = [r, -r * s]
        else:
            d[0] += r
            d[1] -= r * s
        d = delta.get(e)
        if d is None:
            delta[e] = [-r, r * e]
        else:
            d[0] -= r
            d[1] += r * e
    keys = sorted(delta)
    slope = [0]
    icpt = [0]
    a = b = 0
    for x in keys:
        d = delta[x]
        a += d[0]
        b += d[1]
        slope.append(a)
        icpt.append(b)
    S = sorted([s for s, _, _ in sessions])
    E = sorted([e for _, e, _ in sessions])
    out = []
    for lo, hi in windows:
        i = bisect_left(keys, hi)
        j = bisect_left(keys, lo)
        u = slope[i] * hi + icpt[i] - slope[j] * lo - icpt[j]
        out.append((u, bisect_left(S, hi) - bisect_right(E, lo)))
    return out
