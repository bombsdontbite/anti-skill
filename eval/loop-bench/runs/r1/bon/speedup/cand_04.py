def usage_report(sessions, windows):
    """Coordinate compression of every endpoint; integrate the active rate
    between consecutive coordinates."""
    if not sessions:
        return [(0, 0) for _ in windows]
    dslope = {}
    nstart = {}
    nend = {}
    for s, e, r in sessions:
        dslope[s] = dslope.get(s, 0) + r
        dslope[e] = dslope.get(e, 0) - r
        nstart[s] = nstart.get(s, 0) + 1
        nend[e] = nend.get(e, 0) + 1
    coords = set(dslope)
    for lo, hi in windows:
        coords.add(lo)
        coords.add(hi)
    xs = sorted(coords)
    F = {}
    CS = {}
    CE = {}
    f = 0
    slope = 0
    prev = xs[0]
    cs = 0
    ce = 0
    for x in xs:
        f += slope * (x - prev)
        F[x] = f
        CS[x] = cs
        ce += nend.get(x, 0)
        CE[x] = ce
        cs += nstart.get(x, 0)
        slope += dslope.get(x, 0)
        prev = x
    return [(F[hi] - F[lo], CS[hi] - CE[lo]) for lo, hi in windows]
