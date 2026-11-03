from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    g0 = itemgetter(0)
    g1 = itemgetter(1)
    g2 = itemgetter(2)
    st = sorted(sessions, key=g0)
    # start order is close to end order, so this sort is cheaper
    en = sorted(st, key=g1)
    starts = list(map(g0, st))
    srate = list(map(g2, st))
    ends = list(map(g1, en))
    erate = list(map(g2, en))
    sr = [0, *accumulate(srate)]
    srs = [0, *accumulate(map(mul, starts, srate))]
    er = [0, *accumulate(erate)]
    ere = [0, *accumulate(map(mul, ends, erate))]
    out = []
    app = out.append
    for lo, hi in windows:
        i1 = bisect_left(starts, hi)
        i0 = bisect_left(starts, lo)
        j1 = bisect_right(ends, hi)
        j0 = bisect_right(ends, lo)
        app(((hi * (sr[i1] - er[j1]) - srs[i1] + ere[j1]) - (lo * (sr[i0] - er[j0]) - srs[i0] + ere[j0]), i1 - j0))
    return out
