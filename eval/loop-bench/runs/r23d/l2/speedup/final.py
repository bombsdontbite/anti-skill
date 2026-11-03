from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_s = itemgetter(0)
_e = itemgetter(1)
_r = itemgetter(2)


def usage_report(sessions, windows):
    # F(x) = sum of rate * (clamp(x, start, end) - start); usage = F(hi) - F(lo)
    by_start = sorted(sessions, key=_s)
    by_end = sorted(by_start, key=_e)
    starts = list(map(_s, by_start))
    ends = list(map(_e, by_end))
    rs = list(map(_r, by_start))
    re_ = list(map(_r, by_end))
    R = list(accumulate(rs, initial=0))
    RS = list(accumulate(map(mul, rs, starts), initial=0))
    E = list(accumulate(re_, initial=0))
    EE = list(accumulate(map(mul, re_, ends), initial=0))
    out = []
    app = out.append
    for lo, hi in windows:
        i = bisect_left(starts, hi)
        j = bisect_left(starts, lo)
        k = bisect_left(ends, hi)
        m = bisect_right(ends, lo)
        # sessions ending exactly at lo add zero at lo, so bisect_right serves both terms
        app((hi * (R[i] - E[k]) - RS[i] + EE[k] - lo * (R[j] - E[m]) + RS[j] - EE[m], i - m))
    return out
