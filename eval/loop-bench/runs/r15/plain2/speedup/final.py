from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    # G(x) = sum of rate * (clip(x, start, end) - start); usage = G(hi) - G(lo).
    by_start = sorted((s, r) for s, e, r in sessions)
    by_end = sorted((e, r) for s, e, r in sessions)
    starts = [s for s, r in by_start]
    ends = [e for e, r in by_end]
    rs = [0, *accumulate(r for s, r in by_start)]
    rss = [0, *accumulate(s * r for s, r in by_start)]
    re_ = [0, *accumulate(r for e, r in by_end)]
    ree = [0, *accumulate(e * r for e, r in by_end)]

    def g(x):
        i = bisect_right(starts, x)
        j = bisect_right(ends, x)
        return x * (rs[i] - re_[j]) - rss[i] + ree[j]

    report = []
    for lo, hi in windows:
        count = bisect_left(starts, hi) - bisect_right(ends, lo)
        report.append((g(hi) - g(lo), count))
    return report
