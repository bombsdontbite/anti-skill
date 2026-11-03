def usage_report(sessions, windows):
    """Offline: visit windows in order of lo and in order of hi, advancing
    monotone pointers over sessions sorted by start and by end."""
    m = len(windows)
    starts = sorted((s, r) for s, _, r in sessions)
    ends = sorted((e, r) for _, e, r in sessions)
    n = len(starts)

    def prefix_at(points, strict_end):
        order = sorted(range(m), key=lambda w: points[w])
        res_f = [0] * m
        res_c = [0] * m
        i = j = k = 0
        rs = rss = re = ree = 0
        for w in order:
            t = points[w]
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
            res_f[w] = t * (rs - re) - (rss - ree)
            res_c[w] = k if strict_end else i
        return res_f, res_c

    los = [w[0] for w in windows]
    his = [w[1] for w in windows]
    f_lo, ends_le_lo = prefix_at(los, True)
    f_hi, starts_lt_hi = prefix_at(his, False)
    return [(f_hi[w] - f_lo[w], starts_lt_hi[w] - ends_le_lo[w]) for w in range(m)]
