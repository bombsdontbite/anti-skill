from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul

_s, _e, _r = itemgetter(0), itemgetter(1), itemgetter(2)


def _prefix(rows, key):
    pos = list(map(key, rows))
    rates = list(map(_r, rows))
    return pos, list(accumulate(rates, initial=0)), list(accumulate(map(mul, rates, pos), initial=0))


def usage_report(sessions, windows):
    by_start = sorted(sessions, key=_s)
    starts, sr, srs = _prefix(by_start, _s)
    # Ends roughly follow starts, so Timsort finds runs in the start order.
    ends, er, ere = _prefix(sorted(by_start, key=_e), _e)
    los = list(map(_s, windows))
    his = list(map(_e, windows))
    n = len(windows)
    # Sessions starting or ending exactly at x add nothing to the integral up to x.
    a = map(bisect_left, repeat(starts, n), los)
    c = map(bisect_right, repeat(ends, n), los)
    b = map(bisect_left, repeat(starts, n), his)
    d = map(bisect_left, repeat(ends, n), his)
    return [(hi * (sr[b] - er[d]) - srs[b] + ere[d] - lo * (sr[a] - er[c]) + srs[a] - ere[c], b - c)
            for lo, hi, a, c, b, d in zip(los, his, a, c, b, d)]
