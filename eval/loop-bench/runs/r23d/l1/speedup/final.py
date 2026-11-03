from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import floordiv, mul


def usage_report(sessions, windows):
    if not windows:
        return []
    B = len(sessions) + 1
    K = B * B
    d = {}
    g = d.get
    for s, e, r in sessions:
        t = r * K
        d[s] = g(s, 0) + t + B
        d[e] = g(e, 0) + 1 - t
    p = sorted(d)
    v = list(map(g, p))
    cv = [0]
    cv += accumulate(v)
    cw = [0]
    cw += accumulate(map(mul, p, map(floordiv, v, repeat(K))))
    out = []
    for lo, hi in windows:
        ih = bisect_left(p, hi)
        jl = bisect_right(p, lo)
        vh = cv[ih]
        vl = cv[jl]
        out.append((hi * (vh // K) - cw[ih] - lo * (vl // K) + cw[jl],
                    vh // B % B - vl % B))
    return out
