from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0)] * len(windows)
    ss = sorted(sessions, key=_g0)
    starts = list(map(_g0, ss))
    rates = list(map(_g2, ss))
    srx = list(accumulate(map(mul, starts, rates), initial=0))
    sr = list(accumulate(rates, initial=0))
    ss = sorted(sessions, key=_g1)
    ends = list(map(_g1, ss))
    rates = list(map(_g2, ss))
    erx = list(accumulate(map(mul, ends, rates), initial=0))
    er = list(accumulate(rates, initial=0))
    out = []
    for lo, hi in windows:
        i = bisect_left(starts, hi)
        j = bisect_left(ends, hi)
        k = bisect_left(starts, lo, 0, i)
        m = bisect_right(ends, lo, 0, j)
        out.append((hi * (sr[i] - er[j]) - srx[i] + erx[j]
                    - lo * (sr[k] - er[m]) + srx[k] - erx[m], i - m))
    return out
