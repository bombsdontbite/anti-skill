from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import mul


def usage_report(sessions, windows):
    """Prefix sums built with zip/accumulate/operator.mul; one comprehension answers."""
    if not sessions:
        return [(0, 0) for _ in windows]
    ss, sr = zip(*sorted((s, r) for s, _, r in sessions))
    es, er = zip(*sorted((e, r) for _, e, r in sessions))
    A = [0, *accumulate(sr)]
    B = [0, *accumulate(map(mul, ss, sr))]
    C = [0, *accumulate(er)]
    D = [0, *accumulate(map(mul, es, er))]

    def F(t):
        i = bisect_left(ss, t)
        j = bisect_left(es, t)
        return t * (A[i] - C[j]) - B[i] + D[j]

    return [(F(hi) - F(lo), bisect_left(ss, hi) - bisect_right(es, lo))
            for lo, hi in windows]
