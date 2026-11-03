from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_k0 = itemgetter(0)
_k1 = itemgetter(1)
_k2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    a_ = sorted(sessions, key=_k0)
    b_ = sorted(sessions, key=_k1)
    starts = list(map(_k0, a_))
    ends = list(map(_k1, b_))
    ra = list(map(_k2, a_))
    rb = list(map(_k2, b_))
    sr = [0, *accumulate(ra)]
    srx = [0, *accumulate(map(mul, starts, ra))]
    er = [0, *accumulate(rb)]
    erx = [0, *accumulate(map(mul, ends, rb))]
    bl = bisect_left
    br = bisect_right
    return [((sr[a] - er[b]) * hi - srx[a] + erx[b] - (sr[c] - er[d]) * lo + srx[c] - erx[d], a - d)
            for lo, hi in windows
            for a, b, c, d in ((bl(starts, hi), bl(ends, hi), bl(starts, lo), br(ends, lo)),)]
