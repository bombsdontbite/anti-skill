from bisect import bisect_left, bisect_right
from itertools import accumulate, repeat
from operator import itemgetter, mul, sub

_g0 = itemgetter(0)
_g1 = itemgetter(1)
_g2 = itemgetter(2)


def _pick(idx, arr):
    if len(idx) == 1:
        return (arr[idx[0]],)
    return itemgetter(*idx)(arr)


def usage_report(sessions, windows):
    if not windows:
        return []
    if not sessions:
        return [(0, 0)] * len(windows)
    st = sorted(sessions, key=_g0)
    en = sorted(sessions, key=_g1)
    ss = list(map(_g0, st))
    rs = list(map(_g2, st))
    es = list(map(_g1, en))
    re = list(map(_g2, en))
    sr = [0, *accumulate(rs)]
    srs = [0, *accumulate(map(mul, ss, rs))]
    er = [0, *accumulate(re)]
    ere = [0, *accumulate(map(mul, es, re))]
    n = len(windows)
    los = list(map(_g0, windows))
    his = list(map(_g1, windows))
    i = list(map(bisect_left, repeat(ss, n), his))
    j = list(map(bisect_right, repeat(es, n), his))
    k = list(map(bisect_left, repeat(ss, n), los))
    m = list(map(bisect_right, repeat(es, n), los))
    gh = map(sub, map(mul, his, map(sub, _pick(i, sr), _pick(j, er))),
             map(sub, _pick(i, srs), _pick(j, ere)))
    gl = map(sub, map(mul, los, map(sub, _pick(k, sr), _pick(m, er))),
             map(sub, _pick(k, srs), _pick(m, ere)))
    cnt = map(sub, i, m)
    return list(zip(map(sub, gh, gl), cnt))
