from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    ss = sorted(sessions, key=_g0)
    se = sorted(ss, key=_g1)
    st = tuple(map(_g0, ss))
    sr = list(map(_g2, ss))
    en = tuple(map(_g1, se))
    er = list(map(_g2, se))
    A = list(accumulate(sr, initial=0))
    C = list(accumulate(map(mul, st, sr), initial=0))
    B = list(accumulate(er, initial=0))
    D = list(accumulate(map(mul, en, er), initial=0))
    out = []
    app = out.append
    for lo, hi in windows:
        i = bisect_left(st, hi)
        j = bisect_left(en, hi)
        k = bisect_left(st, lo)
        l = bisect_right(en, lo)
        app((hi * (A[i] - B[j]) - C[i] + D[j] - lo * (A[k] - B[l]) + C[k] - D[l], i - l))
    return out
