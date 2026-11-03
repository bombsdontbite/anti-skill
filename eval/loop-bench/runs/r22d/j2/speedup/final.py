from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0)] * len(windows)
    by_start = sorted(sessions, key=_g0)
    # ends are often nearly ordered once sorted by start, which timsort exploits
    by_end = sorted(by_start, key=_g1)
    starts = list(map(_g0, by_start))
    ends = list(map(_g1, by_end))
    rs = list(accumulate(map(_g2, by_start), initial=0))
    ss = list(accumulate(map(mul, starts, map(_g2, by_start)), initial=0))
    re_ = list(accumulate(map(_g2, by_end), initial=0))
    se = list(accumulate(map(mul, ends, map(_g2, by_end)), initial=0))
    out = []
    for lo, hi in windows:
        a = bisect_left(starts, lo)
        b = bisect_left(starts, hi)
        c = bisect_right(ends, lo)
        d = bisect_right(ends, hi)
        out.append((hi * (rs[b] - re_[d]) - ss[b] + se[d] - lo * (rs[a] - re_[c]) + ss[a] - se[c], b - c))
    return out
