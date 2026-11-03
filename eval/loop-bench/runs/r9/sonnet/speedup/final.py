from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    delta = {}
    get = delta.get
    starts = []
    ends = []
    for s, e, r in sessions:
        delta[s] = get(s, 0) + r
        delta[e] = get(e, 0) - r
        starts.append(s)
        ends.append(e)
    starts.sort()
    ends.sort()
    pts = sorted(delta)
    slope = []
    val = []
    sl = 0
    f = 0
    prev = None
    for p in pts:
        if prev is not None:
            f += sl * (p - prev)
        val.append(f)
        sl += delta[p]
        slope.append(sl)
        prev = p
    br = bisect_right
    bl = bisect_left
    out = []
    for lo, hi in windows:
        a = br(pts, hi) - 1
        b = br(pts, lo) - 1
        fh = val[a] + slope[a] * (hi - pts[a]) if a >= 0 else 0
        fl = val[b] + slope[b] * (lo - pts[b]) if b >= 0 else 0
        out.append((fh - fl, bl(starts, hi) - br(ends, lo)))
    return out
