from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_s = itemgetter(0)
_e = itemgetter(1)
_r = itemgetter(2)


def usage_report(sessions, windows):
    by_s = sorted(sessions, key=_s)
    by_e = sorted(by_s, key=_e)
    ss = list(map(_s, by_s))
    es = list(map(_e, by_e))
    ra = list(map(_r, by_s))
    rb = list(map(_r, by_e))
    rs = list(accumulate(ra, initial=0))
    rss = list(accumulate(map(mul, ss, ra), initial=0))
    re_ = list(accumulate(rb, initial=0))
    res = list(accumulate(map(mul, es, rb), initial=0))
    bl = bisect_left
    br = bisect_right
    out = []
    app = out.append
    for lo, hi in windows:
        i = bl(ss, hi)
        j = bl(es, hi)
        k = bl(ss, lo)
        m = br(es, lo)
        app((hi * (rs[i] - re_[j]) - rss[i] + res[j]
             - lo * (rs[k] - re_[m]) + rss[k] - res[m], i - m))
    return out
