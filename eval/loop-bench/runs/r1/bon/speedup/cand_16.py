from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    """Columnar: compute F at every lo and every hi with map, then zip differences."""
    if not windows:
        return []
    order_s = sorted(sessions, key=lambda x: x[0])
    order_e = sorted(sessions, key=lambda x: x[1])
    S = [x[0] for x in order_s]
    E = [x[1] for x in order_e]
    A = list(accumulate([x[2] for x in order_s], initial=0))
    B = list(accumulate([x[0] * x[2] for x in order_s], initial=0))
    C = list(accumulate([x[2] for x in order_e], initial=0))
    D = list(accumulate([x[1] * x[2] for x in order_e], initial=0))

    def F(t):
        i = bisect_left(S, t)
        j = bisect_left(E, t)
        return t * (A[i] - C[j]) - B[i] + D[j]

    los = [w[0] for w in windows]
    his = [w[1] for w in windows]
    f_lo = list(map(F, los))
    f_hi = list(map(F, his))
    cs = [bisect_left(S, h) for h in his]
    ce = [bisect_right(E, l) for l in los]
    usage = [a - b for a, b in zip(f_hi, f_lo)]
    count = [a - b for a, b in zip(cs, ce)]
    return list(zip(usage, count))
