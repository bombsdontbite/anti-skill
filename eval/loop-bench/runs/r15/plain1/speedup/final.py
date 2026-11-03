from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    """For each window, the rate-weighted overlap with every session and how many sessions touch it.

    sessions: list of (start, end, rate) ints, start < end, half-open [start, end).
    windows:  list of (lo, hi) ints, lo < hi, half-open [lo, hi).
    Returns a list of (usage, count): usage = sum of rate * overlap length, count = number of
    sessions whose overlap with the window is longer than zero.
    """
    # usage = G(hi) - G(lo), G(x) = sum rate * (clamp(x, s, e) - s)
    by_s = sorted((s, r) for s, e, r in sessions)
    by_e = sorted((e, r) for s, e, r in sessions)
    ss = [s for s, r in by_s]
    es = [e for e, r in by_e]
    rs = [0, *accumulate(r for s, r in by_s)]
    rss = [0, *accumulate(s * r for s, r in by_s)]
    re = [0, *accumulate(r for e, r in by_e)]
    ree = [0, *accumulate(e * r for e, r in by_e)]

    def g(x):
        i = bisect_left(ss, x)
        j = bisect_left(es, x)
        return x * (rs[i] - re[j]) - rss[i] + ree[j]

    report = []
    for lo, hi in windows:
        count = bisect_left(ss, hi) - bisect_right(es, lo)
        report.append((g(hi) - g(lo), count))
    return report
