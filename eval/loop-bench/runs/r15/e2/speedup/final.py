from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0)] * len(windows)
    g0 = itemgetter(0)
    g1 = itemgetter(1)
    g2 = itemgetter(2)
    by_start = sorted(sessions, key=g0)
    by_end = sorted(by_start, key=g1)
    starts = list(map(g0, by_start))
    ends = list(map(g1, by_end))
    rs = list(map(g2, by_start))
    re = list(map(g2, by_end))
    rs_ = list(accumulate(rs, initial=0))
    ps = list(accumulate(map(mul, starts, rs), initial=0))
    re_ = list(accumulate(re, initial=0))
    pe = list(accumulate(map(mul, ends, re), initial=0))
    los, his = zip(*windows)
    A = map(bisect_left, repeat(starts), los)
    B = list(map(bisect_left, repeat(starts), his))
    C = list(map(bisect_right, repeat(ends), los))
    D = map(bisect_right, repeat(ends), his)
    return [((hi * (rs_[b] - re_[d]) - ps[b] + pe[d]) - (lo * (rs_[a] - re_[c]) - ps[a] + pe[c]), b - c)
            for lo, hi, a, b, c, d in zip(los, his, A, B, C, D)]
