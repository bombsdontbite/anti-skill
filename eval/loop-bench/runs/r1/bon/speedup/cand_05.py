from bisect import bisect_left


def usage_report(sessions, windows):
    """Brute force, pruned: only sessions starting before hi are scanned."""
    ss = sorted(sessions)
    S = [x[0] for x in ss]
    out = []
    for lo, hi in windows:
        k = bisect_left(S, hi)
        usage = 0
        count = 0
        for s, e, r in ss[:k]:
            if e > lo:
                a = s if s > lo else lo
                b = e if e < hi else hi
                usage += r * (b - a)
                count += 1
        out.append((usage, count))
    return out
