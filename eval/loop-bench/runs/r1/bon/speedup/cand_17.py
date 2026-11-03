from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict


def usage_report(sessions, windows):
    """Tables over distinct session coordinates built from Counters; queries
    interpolate F and read counts from prefix arrays."""
    dslope = defaultdict(int)
    starts = Counter()
    ends = Counter()
    for s, e, r in sessions:
        dslope[s] += r
        dslope[e] -= r
        starts[s] += 1
        ends[e] += 1
    xs = sorted(dslope)
    m = len(xs)
    Fx = [0] * m
    after = [0] * m
    CS = [0] * (m + 1)
    CE = [0] * (m + 1)
    f = 0
    slope = 0
    for k in range(m):
        x = xs[k]
        if k:
            f += slope * (x - xs[k - 1])
        Fx[k] = f
        slope += dslope[x]
        after[k] = slope
        CS[k + 1] = CS[k] + starts[x]
        CE[k + 1] = CE[k] + ends[x]

    def F(t):
        k = bisect_right(xs, t) - 1
        if k < 0:
            return 0
        return Fx[k] + after[k] * (t - xs[k])

    out = []
    for lo, hi in windows:
        out.append((F(hi) - F(lo),
                    CS[bisect_left(xs, hi)] - CE[bisect_right(xs, lo)]))
    return out
