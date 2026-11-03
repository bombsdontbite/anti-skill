from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0) for _ in windows]
    by_start = sorted(sessions, key=itemgetter(0))
    starts = [s[0] for s in by_start]
    srates = [s[2] for s in by_start]
    ra = [0, *accumulate(srates)]
    rsa = [0, *accumulate(map(mul, srates, starts))]
    by_end = sorted(sessions, key=itemgetter(1))
    ends = [s[1] for s in by_end]
    erates = [s[2] for s in by_end]
    rb = [0, *accumulate(erates)]
    rsb = [0, *accumulate(map(mul, erates, ends))]

    report = []
    append = report.append
    for lo, hi in windows:
        i = bisect_left(starts, hi)
        j = bisect_left(starts, lo)
        k = bisect_left(ends, hi)
        l = bisect_right(ends, lo)
        # integral up to x: x*sum(rate, start<x) - sum(rate*start) - same over end<x
        fh = hi * (ra[i] - rb[k]) - rsa[i] + rsb[k]
        fl = lo * (ra[j] - rb[l]) - rsa[j] + rsb[l]
        append((fh - fl, i - l))
    return report
