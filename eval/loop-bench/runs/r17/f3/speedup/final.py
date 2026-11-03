from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_by_start = itemgetter(0)
_by_end = itemgetter(1)
_rate = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    st = sorted(sessions, key=_by_start)
    starts = list(map(_by_start, st))
    rates = list(map(_rate, st))
    ps_r = [0, *accumulate(rates)]
    ps_rs = [0, *accumulate(map(mul, rates, starts))]
    en = sorted(st, key=_by_end)
    ends = list(map(_by_end, en))
    er = list(map(_rate, en))
    pe_r = [0, *accumulate(er)]
    pe_re = [0, *accumulate(map(mul, er, ends))]

    out = []
    append = out.append
    for lo, hi in windows:
        k = bisect_left(starts, lo)
        i = bisect_left(starts, hi, k)
        m = bisect_right(ends, lo)
        j = bisect_left(ends, hi, m)
        append((hi * (ps_r[i] - pe_r[j]) - ps_rs[i] + pe_re[j]
                - lo * (ps_r[k] - pe_r[m]) + ps_rs[k] - pe_re[m], i - m))
    return out
