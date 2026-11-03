from bisect import bisect_left


def usage_report(sessions, windows):
    """Bisect straight into sorted (pos, rate) tuples with 1-tuple probes;
    count = n - finished before lo - not started by hi."""
    by_start = sorted([(s, r) for s, _, r in sessions])
    by_end = sorted([(e, r) for _, e, r in sessions])
    n = len(by_start)
    ps = [0]
    pss = [0]
    pe = [0]
    pee = [0]
    for s, r in by_start:
        ps.append(ps[-1] + r)
        pss.append(pss[-1] + r * s)
    for e, r in by_end:
        pe.append(pe[-1] + r)
        pee.append(pee[-1] + r * e)

    def F(t):
        probe = (t,)
        i = bisect_left(by_start, probe)
        j = bisect_left(by_end, probe)
        return t * (ps[i] - pe[j]) - pss[i] + pee[j]

    out = []
    for lo, hi in windows:
        done = bisect_left(by_end, (lo + 1,))
        not_yet = n - bisect_left(by_start, (hi,))
        out.append((F(hi) - F(lo), n - done - not_yet))
    return out
