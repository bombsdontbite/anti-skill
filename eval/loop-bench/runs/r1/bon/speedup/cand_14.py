def _lower(arr, t):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) >> 1
        if arr[mid] < t:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _upper(arr, t):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) >> 1
        if arr[mid] <= t:
            lo = mid + 1
        else:
            hi = mid
    return lo


def usage_report(sessions, windows):
    """Prefix sums with hand-written binary searches."""
    st = sorted([(s, r) for s, _, r in sessions])
    en = sorted([(e, r) for _, e, r in sessions])
    S = [p[0] for p in st]
    E = [p[0] for p in en]
    n = len(st)
    R1 = [0] * (n + 1)
    M1 = [0] * (n + 1)
    R2 = [0] * (n + 1)
    M2 = [0] * (n + 1)
    for idx in range(n):
        s, r = st[idx]
        R1[idx + 1] = R1[idx] + r
        M1[idx + 1] = M1[idx] + r * s
        e, r = en[idx]
        R2[idx + 1] = R2[idx] + r
        M2[idx + 1] = M2[idx] + r * e
    out = []
    for lo, hi in windows:
        i = _lower(S, lo)
        j = _lower(E, lo)
        f_lo = lo * (R1[i] - R2[j]) - M1[i] + M2[j]
        i2 = _lower(S, hi)
        j2 = _lower(E, hi)
        f_hi = hi * (R1[i2] - R2[j2]) - M1[i2] + M2[j2]
        out.append((f_hi - f_lo, i2 - _upper(E, lo)))
    return out
