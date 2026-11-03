from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    """Prefix sums over sessions sorted by start and by end; F(t) is the
    rate-weighted length of all sessions lying before t, usage = F(hi) - F(lo)."""
    by_start = sorted((s, r) for s, _, r in sessions)
    by_end = sorted((e, r) for _, e, r in sessions)
    S = [s for s, _ in by_start]
    E = [e for e, _ in by_end]
    rs = list(accumulate((r for _, r in by_start), initial=0))
    rss = list(accumulate((r * s for s, r in by_start), initial=0))
    re = list(accumulate((r for _, r in by_end), initial=0))
    ree = list(accumulate((r * e for e, r in by_end), initial=0))

    def F(t):
        i = bisect_left(S, t)
        j = bisect_left(E, t)
        return t * (rs[i] - re[j]) - (rss[i] - ree[j])

    out = []
    for lo, hi in windows:
        out.append((F(hi) - F(lo), bisect_left(S, hi) - bisect_right(E, lo)))
    return out
