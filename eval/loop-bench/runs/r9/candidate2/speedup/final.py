from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    # One key sort by start; the end order is derived by sorting the start-ordered list,
    # which timsort handles faster when ends roughly follow starts.
    if not windows:
        return []
    by_s = sorted(sessions, key=_g0)
    by_e = sorted(by_s, key=_g1)
    starts = list(map(_g0, by_s))
    ends = list(map(_g1, by_e))
    rs = list(map(_g2, by_s))
    re = list(map(_g2, by_e))
    sr = [0, *accumulate(rs)]
    ssr = [0, *accumulate(map(mul, starts, rs))]
    er = [0, *accumulate(re)]
    esr = [0, *accumulate(map(mul, ends, re))]
    los = list(map(_g0, windows))
    his = list(map(_g1, windows))
    br = bisect_right
    return [
        (h * (sr[a] - er[b]) - ssr[a] + esr[b] - l * (sr[c] - er[d]) + ssr[c] - esr[d],
         bisect_left(starts, h) - d)
        for l, h, a, b, c, d in zip(los, his,
                                    map(br, repeat(starts), his), map(br, repeat(ends), his),
                                    map(br, repeat(starts), los), map(br, repeat(ends), los))
    ]
