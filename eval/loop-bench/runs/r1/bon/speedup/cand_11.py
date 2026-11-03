import heapq
from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Piecewise-linear table of F at breakpoints from a heap merge of starts and
    ends; queries interpolate from the nearest breakpoint at or below."""
    starts = sorted((s, r) for s, _, r in sessions)
    ends = sorted((e, -r) for _, e, r in sessions)
    xs = []
    Fs = []
    slopes = []
    f = 0
    for x, dr in heapq.merge(starts, ends):
        if xs and xs[-1] == x:
            slopes[-1] += dr
        else:
            if xs:
                f += slopes[-1] * (x - xs[-1])
                cur = slopes[-1]
            else:
                cur = 0
            xs.append(x)
            Fs.append(f)
            slopes.append(cur + dr)
    S = [s for s, _ in starts]
    E = [e for e, _ in ends]

    def F(t):
        k = bisect_right(xs, t) - 1
        if k < 0:
            return 0
        return Fs[k] + slopes[k] * (t - xs[k])

    return [(F(hi) - F(lo), bisect_left(S, hi) - bisect_right(E, lo))
            for lo, hi in windows]
