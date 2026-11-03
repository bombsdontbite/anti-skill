from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul, lt

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def usage_report(sessions, windows):
    if not windows:
        return []
    if not sessions:
        return [(0, 0)] * len(windows)
    a = sorted(sessions, key=_g0)
    st = list(map(_g0, a))
    if not all(map(lt, st, map(_g1, a))):
        sessions = [t for t in sessions if t[0] < t[1]]
        if not sessions:
            return [(0, 0)] * len(windows)
        a = sorted(sessions, key=_g0)
        st = list(map(_g0, a))
    sr_ = list(map(_g2, a))
    b = sorted(a, key=_g1)
    en = list(map(_g1, b))
    er_ = list(map(_g2, b))
    sr = list(accumulate(sr_, initial=0))
    srs = list(accumulate(map(mul, st, sr_), initial=0))
    er = list(accumulate(er_, initial=0))
    ers = list(accumulate(map(mul, en, er_), initial=0))
    out = []
    ap = out.append
    for lo, hi in windows:
        if hi <= lo:
            ap((0, 0))
            continue
        i = bisect_left(st, hi)
        j = bisect_left(en, hi)
        k = bisect_left(st, lo)
        l = bisect_right(en, lo)
        ap((hi * (sr[i] - er[j]) - srs[i] + ers[j] - lo * (sr[k] - er[l]) + srs[k] - ers[l], i - l))
    return out
