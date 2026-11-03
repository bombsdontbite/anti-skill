from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Aggregate rates and counts per distinct start and end before prefixing."""
    sr = {}
    sc = {}
    er = {}
    ec = {}
    for s, e, r in sessions:
        sr[s] = sr.get(s, 0) + r
        sc[s] = sc.get(s, 0) + 1
        er[e] = er.get(e, 0) + r
        ec[e] = ec.get(e, 0) + 1
    S = sorted(sr)
    E = sorted(er)
    PSR = [0]
    PSRS = [0]
    PSC = [0]
    a = b = c = 0
    for s in S:
        r = sr[s]
        a += r
        b += r * s
        c += sc[s]
        PSR.append(a)
        PSRS.append(b)
        PSC.append(c)
    PER = [0]
    PERE = [0]
    PEC = [0]
    a = b = c = 0
    for e in E:
        r = er[e]
        a += r
        b += r * e
        c += ec[e]
        PER.append(a)
        PERE.append(b)
        PEC.append(c)

    def F(t):
        i = bisect_left(S, t)
        j = bisect_left(E, t)
        return t * (PSR[i] - PER[j]) - PSRS[i] + PERE[j]

    out = []
    for lo, hi in windows:
        out.append((F(hi) - F(lo),
                    PSC[bisect_left(S, hi)] - PEC[bisect_right(E, lo)]))
    return out
