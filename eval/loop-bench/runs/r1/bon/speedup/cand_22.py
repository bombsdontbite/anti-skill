def usage_report(sessions, windows):
    """Merge identical (start, end) sessions, sort by start, and scan each window
    with an early break once starts reach hi."""
    groups = {}
    for s, e, r in sessions:
        g = groups.get((s, e))
        if g is None:
            groups[(s, e)] = [r, 1]
        else:
            g[0] += r
            g[1] += 1
    items = sorted((s, e, g[0], g[1]) for (s, e), g in groups.items())
    out = []
    for lo, hi in windows:
        usage = 0
        count = 0
        for s, e, r, c in items:
            if s >= hi:
                break
            if e > lo:
                a = s if s > lo else lo
                b = e if e < hi else hi
                usage += r * (b - a)
                count += c
        out.append((usage, count))
    return out
