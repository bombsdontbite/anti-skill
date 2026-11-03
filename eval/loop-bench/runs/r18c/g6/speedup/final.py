from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


def usage_report(sessions, windows):
    n = len(sessions)
    if not n:
        return [(0, 0) for _ in windows]
    by_start = sorted(sessions, key=itemgetter(0))
    starts, _, rs = zip(*by_start)
    pr = [0, *accumulate(rs)]
    prs = [0, *accumulate(map(mul, starts, rs))]
    _, ends, rs = zip(*sorted(by_start, key=itemgetter(1)))
    qr = [0, *accumulate(rs)]
    qre = [0, *accumulate(map(mul, ends, rs))]
    out = []
    for lo, hi in windows:
        i = bisect_left(starts, hi)
        j = bisect_left(ends, hi)
        k = bisect_left(starts, lo)
        l = bisect_right(ends, lo)
        out.append((hi * (pr[i] - qr[j]) - prs[i] + qre[j] - lo * (pr[k] - qr[l]) + prs[k] - qre[l], i - l))
    return out
