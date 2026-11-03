from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Finished sessions contribute their full weighted length, the rest t - s:
    F(t) = t*(R[s<t] - R[e<=t]) - RS[s<t] + RS[e<=t] + RL[e<=t]."""
    by_start = sorted((s, r) for s, _, r in sessions)
    by_end = sorted((e, s, r) for s, e, r in sessions)
    S = [s for s, _ in by_start]
    E = [e for e, _, _ in by_end]
    PR = [0]
    PRS = [0]
    a = b = 0
    for s, r in by_start:
        a += r
        b += r * s
        PR.append(a)
        PRS.append(b)
    QR = [0]
    QRS = [0]
    QRL = [0]
    a = b = c = 0
    for e, s, r in by_end:
        a += r
        b += r * s
        c += r * (e - s)
        QR.append(a)
        QRS.append(b)
        QRL.append(c)

    def F(t):
        i = bisect_left(S, t)
        j = bisect_right(E, t)
        return t * (PR[i] - QR[j]) - PRS[i] + QRS[j] + QRL[j]

    out = []
    for lo, hi in windows:
        out.append((F(hi) - F(lo), bisect_left(S, hi) - bisect_right(E, lo)))
    return out
