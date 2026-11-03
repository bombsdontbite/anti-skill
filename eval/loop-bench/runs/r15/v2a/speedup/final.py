from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    g0, g1, g2 = itemgetter(0), itemgetter(1), itemgetter(2)
    a = sorted(sessions, key=g0)
    b = sorted(a, key=g1)
    starts = list(map(g0, a))
    sr = list(map(g2, a))
    ends = list(map(g1, b))
    er = list(map(g2, b))
    # F(x) = x * (rs - re) - (rss - res) over points <= x; points equal to x add 0,
    # so one bisect per point serves both F and the count
    rs = list(accumulate(sr, initial=0))
    rss = list(accumulate(map(mul, starts, sr), initial=0))
    re = list(accumulate(er, initial=0))
    res = list(accumulate(map(mul, ends, er), initial=0))
    out = []
    for lo, hi in windows:
        i = bisect_left(starts, hi)
        j = bisect_left(ends, hi)
        k = bisect_left(starts, lo)
        m = bisect_right(ends, lo)
        out.append((hi * (rs[i] - re[j]) - rss[i] + res[j] - lo * (rs[k] - re[m]) + rss[k] - res[m], i - m))
    return out
