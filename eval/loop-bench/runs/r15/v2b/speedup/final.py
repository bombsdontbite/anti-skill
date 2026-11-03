from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul, sub


def usage_report(sessions, windows):
    n = len(windows)
    if not sessions or not n:
        return [(0, 0)] * n
    ss = sorted(sessions, key=itemgetter(0))
    starts, _, rs = zip(*ss)
    _, ends, re = zip(*sorted(ss, key=itemgetter(1)))
    sr = list(accumulate(rs, initial=0))
    srt = list(accumulate(map(mul, starts, rs), initial=0))
    er = list(accumulate(re, initial=0))
    ert = list(accumulate(map(mul, ends, re), initial=0))
    los, his = zip(*windows)
    ih = list(map(bisect_left, repeat(starts, n), his))
    IH = itemgetter(*ih, 0)
    JH = itemgetter(*map(bisect_left, repeat(ends, n), his), 0)
    IL = itemgetter(*map(bisect_left, repeat(starts, n), los), 0)
    JL = itemgetter(*map(bisect_left, repeat(ends, n), los), 0)
    # F(t) = t * (rate of sessions running at t) - sum of rate * (start or end) behind t
    fh = map(sub, map(mul, his, map(sub, IH(sr), JH(er))), map(sub, IH(srt), JH(ert)))
    fl = map(sub, map(mul, los, map(sub, IL(sr), JL(er))), map(sub, IL(srt), JL(ert)))
    count = map(sub, ih, map(bisect_right, repeat(ends, n), los))
    return list(zip(map(sub, fh, fl), count))
