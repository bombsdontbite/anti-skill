from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import mul, itemgetter

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    A = sorted(sessions, key=_g0)
    ss = list(map(_g0, A))
    rs = list(map(_g2, A))
    B = sorted(A, key=_g1)
    es = list(map(_g1, B))
    re = list(map(_g2, B))
    sr = list(accumulate(rs, initial=0))
    srx = list(accumulate(map(mul, ss, rs), initial=0))
    er = list(accumulate(re, initial=0))
    erx = list(accumulate(map(mul, es, re), initial=0))
    out = []
    app = out.append
    for lo, hi in windows:
        i = bisect_left(ss, hi)
        j = bisect_left(es, hi)
        k = bisect_left(ss, lo, 0, i)
        l = bisect_right(es, lo, 0, j)
        app((hi * (sr[i] - er[j]) - srx[i] + erx[j] - lo * (sr[k] - er[l]) + srx[k] - erx[l], i - l))
    return out
