from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0) for _ in windows]
    # at x = P[i] the prefix sums cover starts < x and ends <= x; a start at x adds 0 usage
    P = sorted({x for w in windows for x in w})
    m = len(P) + 1
    A = [0] * m
    B = [0] * m
    CS = [0] * m
    CE = [0] * m
    bl = bisect_left
    br = bisect_right
    Q = P + [float('inf')]
    for s, e, r in sessions:
        k = br(P, s)
        if e <= Q[k]:
            # start and end in the same gap: only the constant term changes
            B[k] += r * (s - e)
            CS[k] += 1
            CE[k] += 1
        else:
            A[k] += r
            B[k] += r * s
            CS[k] += 1
            k = bl(P, e, k)
            A[k] -= r
            B[k] -= r * e
            CE[k] += 1
    F = {x: (x * a - b, cs, ce) for x, a, b, cs, ce in
         zip(P, accumulate(A), accumulate(B), accumulate(CS), accumulate(CE))}
    out = []
    for lo, hi in windows:
        fl = F[lo]
        fh = F[hi]
        out.append((fh[0] - fl[0], fh[1] - fl[2]))
    return out
