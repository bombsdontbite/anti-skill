from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


g0, g1, g2 = itemgetter(0), itemgetter(1), itemgetter(2)


def usage_report(sessions, windows):
    # usage(lo, hi) = F(hi) - F(lo), F(x) = sum over s < x of r(x - s) minus sum over e < x of r(x - e);
    # count = #(start < hi) - #(end <= lo), the two sets being disjoint.
    if not sessions:
        return [(0, 0)] * len(windows)
    ss = sorted(sessions, key=g0); sx = list(map(g0, ss)); sr = list(map(g2, ss))
    es = sorted(sessions, key=g1); ex = list(map(g1, es)); er = list(map(g2, es))
    cr = [0, *accumulate(sr)]
    crs = [0, *accumulate(map(mul, sx, sr))]
    ce = [0, *accumulate(er)]
    ces = [0, *accumulate(map(mul, ex, er))]
    report = []
    app = report.append
    for lo, hi in windows:
        i = bisect_left(sx, hi)
        j = bisect_left(ex, hi)
        k = bisect_left(sx, lo)
        l = bisect_left(ex, lo)
        u = (cr[i] - ce[j]) * hi - crs[i] + ces[j] - (cr[k] - ce[l]) * lo + crs[k] - ces[l]
        app((u, i - bisect_right(ex, lo, l)))
    return report
