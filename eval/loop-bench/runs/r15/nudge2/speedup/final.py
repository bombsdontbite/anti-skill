from bisect import bisect_left
from itertools import accumulate, repeat
from operator import add, and_, lshift, mul, rshift, sub


def usage_report(sessions, windows):
    if not sessions:
        return [(0, 0)] * len(windows)
    starts, ends, rates = zip(*sessions)
    n = len(rates)
    rmin = min(rates)
    if rmin < 0:
        rates = list(map(sub, rates, repeat(rmin, n)))
    b = max(rates).bit_length()
    mask = (1 << b) - 1
    # Shift times so packed sort keys stay below 2**30, where int sorting is fastest.
    if b < 30 and max(ends) >= (1 << (30 - b)):
        base = min(starts)
    else:
        base = 0
    if base and max(ends) - base < (1 << (30 - b)):
        starts = map(sub, starts, repeat(base, n))
        ends = map(sub, ends, repeat(base, n))
        windows = [(lo - base, hi - base) for lo, hi in windows]
    ps = sorted(map(add, map(lshift, starts, repeat(b, n)), rates))
    pe = sorted(map(add, map(lshift, ends, repeat(b, n)), rates))
    sr = list(map(and_, ps, repeat(mask, n)))
    er = list(map(and_, pe, repeat(mask, n)))
    if rmin < 0:
        sr = list(map(add, sr, repeat(rmin, n)))
        er = list(map(add, er, repeat(rmin, n)))
    cr_s = [0, *accumulate(sr)]
    cx_s = [0, *accumulate(map(mul, map(rshift, ps, repeat(b, n)), sr))]
    cr_e = [0, *accumulate(er)]
    cx_e = [0, *accumulate(map(mul, map(rshift, pe, repeat(b, n)), er))]
    out = []
    app = out.append
    for lo, hi in windows:
        h = hi << b
        l = (lo + 1) << b
        i = bisect_left(ps, h)
        j = bisect_left(pe, h)
        k = bisect_left(ps, l, 0, i)
        m = bisect_left(pe, l, 0, j)
        # Sessions starting or ending exactly at lo add nothing to F(lo), so both sides use <= lo.
        app((hi * (cr_s[i] - cr_e[j]) - cx_s[i] + cx_e[j]
             - lo * (cr_s[k] - cr_e[m]) + cx_s[k] - cx_e[m], i - m))
    return out
