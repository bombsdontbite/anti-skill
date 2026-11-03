from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

g0 = itemgetter(0)
g1 = itemgetter(1)
g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0)] * len(windows)
    a = sorted(sessions, key=g0)
    starts = list(map(g0, a))
    rs = list(map(g2, a))
    sr = list(accumulate(rs, initial=0))
    srs = list(accumulate(map(mul, starts, rs), initial=0))
    a.sort(key=g1)
    ends = list(map(g1, a))
    rs = list(map(g2, a))
    er = list(accumulate(rs, initial=0))
    ere = list(accumulate(map(mul, ends, rs), initial=0))
    bl = bisect_left
    br = bisect_right
    out = []
    app = out.append
    for lo, hi in windows:
        i = bl(starts, hi)
        j = br(ends, hi)
        k = bl(starts, lo, 0, i)
        l = br(ends, lo, 0, j)
        app((hi * (sr[i] - er[j]) - srs[i] + ere[j]
             - lo * (sr[k] - er[l]) + srs[k] - ere[l],
             i - l))
    return out
