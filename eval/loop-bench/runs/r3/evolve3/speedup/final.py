from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)


def usage_report(sessions, windows):
    # F(x) = x*(R[i]-RE[k]) - RS[i] + RES[k]; F at lo and hi from prefix sums, count from bisects.
    ss = [x for x in sessions if x[0] < x[1]]
    ss.sort(key=_g0)
    S = [x[0] for x in ss]
    R = [0]
    RS = [0]
    a = b = 0
    for s, e, r in ss:
        a += r; b += r * s
        R.append(a); RS.append(b)
    ss.sort(key=_g1)
    E = [x[1] for x in ss]
    RE = [0]
    RES = [0]
    a = b = 0
    for s, e, r in ss:
        a += r; b += r * e
        RE.append(a); RES.append(b)
    out = []
    for lo, hi in windows:
        if hi <= lo:
            out.append((0, 0))
            continue
        i = bisect_left(S, hi); j = bisect_left(S, lo, 0, i)
        k = bisect_left(E, hi); l = bisect_left(E, lo, 0, k)
        out.append((hi * (R[i] - RE[k]) - RS[i] + RES[k] - lo * (R[j] - RE[l]) + RS[j] - RES[l],
                    i - bisect_right(E, lo, l, k)))
    return out
