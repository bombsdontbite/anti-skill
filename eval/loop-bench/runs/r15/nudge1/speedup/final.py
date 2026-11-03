from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul

_start = itemgetter(0)
_end = itemgetter(1)
_rate = itemgetter(2)


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0)] * len(windows)
    by_start = sorted(sessions, key=_start)
    by_end = sorted(by_start, key=_end)
    s_pos = list(map(_start, by_start))
    s_rate = list(map(_rate, by_start))
    e_pos = list(map(_end, by_end))
    e_rate = list(map(_rate, by_end))
    s1 = [0, *accumulate(s_rate)]
    s2 = [0, *accumulate(map(mul, s_pos, s_rate))]
    e1 = [0, *accumulate(e_rate)]
    e2 = [0, *accumulate(map(mul, e_pos, e_rate))]
    br = bisect_right
    bl = bisect_left
    report = []
    append = report.append
    for lo, hi in windows:
        i = br(s_pos, hi)
        j = br(e_pos, hi)
        k = br(s_pos, lo)
        m = br(e_pos, lo)
        append((hi * (s1[i] - e1[j]) - s2[i] + e2[j]
                - lo * (s1[k] - e1[m]) + s2[k] - e2[m],
                bl(s_pos, hi, k) - m))
    return report
