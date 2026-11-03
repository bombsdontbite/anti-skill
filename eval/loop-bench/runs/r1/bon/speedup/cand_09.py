from bisect import bisect_left, bisect_right
from itertools import accumulate


def usage_report(sessions, windows):
    """Prefix sums with a memo per endpoint value, since windows share edges."""
    starts = sorted((s, r) for s, _, r in sessions)
    ends = sorted((e, r) for _, e, r in sessions)
    S = [x for x, _ in starts]
    E = [x for x, _ in ends]
    A = list(accumulate((r for _, r in starts), initial=0))
    B = list(accumulate((x * r for x, r in starts), initial=0))
    C = list(accumulate((r for _, r in ends), initial=0))
    D = list(accumulate((x * r for x, r in ends), initial=0))
    memo = {}
    cs_memo = {}
    ce_memo = {}
    out = []
    for lo, hi in windows:
        fl = memo.get(lo)
        if fl is None:
            i = bisect_left(S, lo)
            j = bisect_left(E, lo)
            fl = lo * (A[i] - C[j]) - B[i] + D[j]
            memo[lo] = fl
        fh = memo.get(hi)
        if fh is None:
            i = bisect_left(S, hi)
            j = bisect_left(E, hi)
            fh = hi * (A[i] - C[j]) - B[i] + D[j]
            memo[hi] = fh
        a = cs_memo.get(hi)
        if a is None:
            a = cs_memo[hi] = bisect_left(S, hi)
        b = ce_memo.get(lo)
        if b is None:
            b = ce_memo[lo] = bisect_right(E, lo)
        out.append((fh - fl, a - b))
    return out
