from bisect import bisect_left, bisect_right
from functools import partial
from itertools import accumulate
from operator import itemgetter, mul


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0)] * len(windows)
    by_start = sorted(sessions, key=itemgetter(0))
    xs, _, rs = zip(*by_start)
    _, ys, re_ = zip(*sorted(by_start, key=itemgetter(1)))
    Rs = [0]
    Rs += accumulate(rs)
    Ws = [0]
    Ws += accumulate(map(mul, rs, xs))
    Re = [0]
    Re += accumulate(re_)
    We = [0]
    We += accumulate(map(mul, re_, ys))
    los, his = zip(*windows)
    A = map(partial(bisect_left, xs), his)
    B = map(partial(bisect_left, xs), los)
    C = map(partial(bisect_left, ys), his)
    D = map(partial(bisect_right, ys), los)
    return [(hi * (Rs[a] - Re[c]) - Ws[a] + We[c] - lo * (Rs[b] - Re[d]) + Ws[b] - We[d], a - d)
            for lo, hi, a, b, c, d in zip(los, his, A, B, C, D)]
