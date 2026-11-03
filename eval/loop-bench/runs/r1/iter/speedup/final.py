from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_g0 = itemgetter(0)
_g1 = itemgetter(1)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    st = sorted(sessions, key=_g0)
    en = sorted(sessions, key=_g1)
    sk, _, srr = zip(*st)
    _, ek, err = zip(*en)
    sr = [0, *accumulate(srr)]
    srs = [0, *accumulate(map(mul, sk, srr))]
    er = [0, *accumulate(err)]
    ers = [0, *accumulate(map(mul, ek, err))]
    out = []
    app = out.append
    for lo, hi in windows:
        a = bisect_left(sk, hi)
        c = bisect_left(sk, lo)
        d = bisect_left(ek, hi)
        b = bisect_left(ek, lo)
        app((hi * (sr[a] - er[d]) - srs[a] + ers[d]
             - lo * (sr[c] - er[b]) + srs[c] - ers[b],
             a - bisect_right(ek, lo, b)))
    return out
