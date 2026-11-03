from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul, sub, add, getitem

_k0 = itemgetter(0)
_k1 = itemgetter(1)


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0) for _ in windows]
    starts, _, r1 = zip(*sorted(sessions, key=_k0))
    _, ends, r2 = zip(*sorted(sessions, key=_k1))
    rs = list(accumulate(r1, initial=0))
    rss = list(accumulate(map(mul, r1, starts), initial=0))
    re_ = list(accumulate(r2, initial=0))
    res = list(accumulate(map(mul, r2, ends), initial=0))
    los, his = zip(*windows)
    pts = los + his
    a = list(map(bisect_left, repeat(starts), pts))
    b = list(map(bisect_right, repeat(ends), pts))
    slope = map(sub, map(getitem, repeat(rs), a), map(getitem, repeat(re_), b))
    const = map(sub, map(getitem, repeat(res), b), map(getitem, repeat(rss), a))
    F = list(map(add, map(mul, pts, slope), const))
    m = len(los)
    return list(zip(map(sub, F[m:], F[:m]), map(sub, a[m:], b[:m])))
