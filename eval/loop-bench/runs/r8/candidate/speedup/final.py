from bisect import bisect_left, bisect_right
from itertools import accumulate
from operator import itemgetter, mul


def _prefix(points, rates):
    return list(accumulate(rates, initial=0)), list(accumulate(map(mul, points, rates), initial=0))


def usage_report(sessions, windows):
    # F(x) = sum over starts s <= x of r*(x - s) minus the same over ends e <= x, so
    # usage = F(hi) - F(lo); a point equal to x adds 0, so either bisect side gives F.
    # count = #(start < hi) - #(end <= lo), since start < end and lo < hi.
    # Sorting the session tuples by a C-level int key carries the rate along for free.
    if not sessions:
        return [(0, 0) for _ in windows]
    first, second, third = itemgetter(0), itemgetter(1), itemgetter(2)
    by_start = sorted(sessions, key=first)
    by_end = sorted(sessions, key=second)
    sp = list(map(first, by_start))
    srates = list(map(third, by_start))
    ep = list(map(second, by_end))
    erates = list(map(third, by_end))
    sR, sM = _prefix(sp, srates)
    eR, eM = _prefix(ep, erates)
    out = []
    append = out.append
    bl = bisect_left
    br = bisect_right
    for lo, hi in windows:
        a = bl(sp, hi)
        b = br(ep, hi)
        c = bl(sp, lo, 0, a)
        d = br(ep, lo, 0, b)
        append((hi * (sR[a] - eR[b]) - sM[a] + eM[b] - lo * (sR[c] - eR[d]) + sM[c] - eM[d], a - d))
    return out
