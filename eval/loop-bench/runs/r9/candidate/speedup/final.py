from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    # The rate integral F(t) is only needed at window endpoints. A session adds slope +r and
    # constant -r*s from the first endpoint > s, and slope -r, constant +r*e from the first
    # endpoint >= e; prefix sums over those difference arrays give F at every endpoint.
    qs = sorted({p for w in windows for p in w})
    k = len(qs) + 1
    dr = [0] * k; dc = [0] * k; cs = [0] * k; ce = [0] * k
    br = bisect_right; bl = bisect_left
    for s, e, r in sessions:
        i = br(qs, s)
        j = bl(qs, e, i)
        dr[i] += r; dr[j] -= r
        dc[i] -= r * s; dc[j] += r * e
        cs[i] += 1; ce[j] += 1
    F = {}; idx = {}
    for t, q, a, b in zip(range(k), qs, accumulate(dr), accumulate(dc)):
        F[q] = q * a + b; idx[q] = t
    S = list(accumulate(cs)); E = list(accumulate(ce))
    return [(F[hi] - F[lo], S[idx[hi]] - E[idx[lo]]) for lo, hi in windows]
