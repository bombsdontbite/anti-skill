def usage_report(sessions, windows):
    """One merged event sort: ends, then queries, then starts at equal positions,
    so a query sees starts strictly before it and ends at or before it."""
    if not windows:
        return []
    ev = []
    push = ev.append
    for s, e, r in sessions:
        push((s, 2, r))
        push((e, 0, r))
    for lo, hi in windows:
        push((lo, 1, 0))
        push((hi, 1, 0))
    ev.sort()
    F = {}
    CS = {}
    CE = {}
    slope = 0
    f = 0
    ns = 0
    ne = 0
    prev = ev[0][0]
    for x, typ, r in ev:
        if x != prev:
            f += slope * (x - prev)
            prev = x
        if typ == 0:
            slope -= r
            ne += 1
        elif typ == 1:
            F[x] = f
            CS[x] = ns
            CE[x] = ne
        else:
            slope += r
            ns += 1
    return [(F[hi] - F[lo], CS[hi] - CE[lo]) for lo, hi in windows]
