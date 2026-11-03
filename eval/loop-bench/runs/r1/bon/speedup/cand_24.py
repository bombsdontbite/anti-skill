from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    """Roles reversed: each session scatters into difference arrays indexed by the
    sorted distinct query points (log of the few window endpoints, not of n)."""
    if not windows:
        return []
    Q = sorted(set([w[0] for w in windows]) | set([w[1] for w in windows]))
    q = len(Q)
    dA = [0] * (q + 1)
    dB = [0] * (q + 1)
    dS = [0] * (q + 1)
    dE = [0] * (q + 1)
    for s, e, r in sessions:
        a = bisect_right(Q, s)
        b = bisect_left(Q, e)
        rs = r * s
        dA[a] += r
        dA[b] -= r
        dB[a] -= rs
        dB[b] += r * e
        dS[a] += 1
        dE[b] += 1
    F = {}
    CS = {}
    CE = {}
    A = B = ns = ne = 0
    for k in range(q):
        A += dA[k]
        B += dB[k]
        ns += dS[k]
        ne += dE[k]
        t = Q[k]
        F[t] = A * t + B
        CS[t] = ns
        CE[t] = ne
    return [(F[hi] - F[lo], CS[hi] - CE[lo]) for lo, hi in windows]
