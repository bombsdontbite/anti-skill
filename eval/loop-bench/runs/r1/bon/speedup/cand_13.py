from bisect import bisect_left, bisect_right


def _brute(sessions, windows):
    out = []
    for lo, hi in windows:
        usage = 0
        count = 0
        for s, e, r in sessions:
            a = s if s > lo else lo
            b = e if e < hi else hi
            if b > a:
                usage += r * (b - a)
                count += 1
        out.append((usage, count))
    return out


def _indexed(sessions, windows):
    by_start = sorted((s, r) for s, _, r in sessions)
    by_end = sorted((e, r) for _, e, r in sessions)
    S = []
    E = []
    a = [0]
    b = [0]
    c = [0]
    d = [0]
    x = y = 0
    for s, r in by_start:
        S.append(s)
        x += r
        y += r * s
        a.append(x)
        b.append(y)
    x = y = 0
    for e, r in by_end:
        E.append(e)
        x += r
        y += r * e
        c.append(x)
        d.append(y)
    out = []
    bl = bisect_left
    for lo, hi in windows:
        i1 = bl(S, lo)
        j1 = bl(E, lo)
        i2 = bl(S, hi)
        j2 = bl(E, hi)
        f_lo = lo * (a[i1] - c[j1]) - b[i1] + d[j1]
        f_hi = hi * (a[i2] - c[j2]) - b[i2] + d[j2]
        out.append((f_hi - f_lo, i2 - bisect_right(E, lo)))
    return out


def usage_report(sessions, windows):
    """Tiny inputs go to a plain loop; anything sizeable to sorted prefix sums."""
    if len(sessions) * len(windows) <= 256:
        return _brute(sessions, windows)
    return _indexed(sessions, windows)
