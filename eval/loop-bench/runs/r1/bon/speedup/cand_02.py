def usage_report(sessions, windows):
    """Sweep the sorted distinct window endpoints with three monotone pointers."""
    if not windows:
        return []
    starts = sorted((s, r) for s, e, r in sessions)
    ends = sorted((e, r) for s, e, r in sessions)
    n = len(starts)
    pts = sorted(set([lo for lo, _ in windows] + [hi for _, hi in windows]))
    Fv = {}
    cs = {}
    ce = {}
    i = j = k = 0
    rs = rss = re = ree = 0
    for t in pts:
        while i < n and starts[i][0] < t:
            s, r = starts[i]
            rs += r
            rss += r * s
            i += 1
        while j < n and ends[j][0] < t:
            e, r = ends[j]
            re += r
            ree += r * e
            j += 1
        if k < j:
            k = j
        while k < n and ends[k][0] <= t:
            k += 1
        Fv[t] = t * (rs - re) - (rss - ree)
        cs[t] = i
        ce[t] = k
    return [(Fv[hi] - Fv[lo], cs[hi] - ce[lo]) for lo, hi in windows]
