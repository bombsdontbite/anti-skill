from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Suffix form: H(t) = rate-weighted length of sessions after t;
    usage = H(lo) - H(hi)."""
    by_start = sorted((s, r) for s, _, r in sessions)
    by_end = sorted((e, r) for _, e, r in sessions)
    n = len(by_start)
    S = [s for s, _ in by_start]
    E = [e for e, _ in by_end]
    sR = [0] * (n + 1)
    sRS = [0] * (n + 1)
    eR = [0] * (n + 1)
    eRE = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        s, r = by_start[i]
        sR[i] = sR[i + 1] + r
        sRS[i] = sRS[i + 1] + r * s
        e, r = by_end[i]
        eR[i] = eR[i + 1] + r
        eRE[i] = eRE[i + 1] + r * e

    def H(t):
        i = bisect_right(E, t)
        k = bisect_right(S, t)
        return (eRE[i] - t * eR[i]) - (sRS[k] - t * sR[k])

    out = []
    for lo, hi in windows:
        after_lo = n - bisect_right(E, lo)
        from_hi = n - bisect_left(S, hi)
        out.append((H(lo) - H(hi), after_lo - from_hi))
    return out
