def usage_report(sessions, windows):
    """Aggregate breakpoints in dicts, then walk them once against the sorted
    distinct query points, extrapolating F linearly past the last breakpoint."""
    if not windows:
        return []
    dslope = {}
    nst = {}
    nen = {}
    for s, e, r in sessions:
        dslope[s] = dslope.get(s, 0) + r
        dslope[e] = dslope.get(e, 0) - r
        nst[s] = nst.get(s, 0) + 1
        nen[e] = nen.get(e, 0) + 1
    xs = sorted(dslope)
    m = len(xs)
    qs = sorted(set([w[0] for w in windows]) | set([w[1] for w in windows]))
    F = {}
    CS = {}
    CE = {}
    k = 0
    f = 0
    slope = 0
    cur = None
    ns = 0
    ne = 0
    for t in qs:
        while k < m and xs[k] < t:
            x = xs[k]
            if cur is not None:
                f += slope * (x - cur)
            cur = x
            slope += dslope[x]
            ns += nst.get(x, 0)
            ne += nen.get(x, 0)
            k += 1
        F[t] = 0 if cur is None else f + slope * (t - cur)
        CS[t] = ns
        CE[t] = ne + nen.get(t, 0)
    return [(F[hi] - F[lo], CS[hi] - CE[lo]) for lo, hi in windows]
