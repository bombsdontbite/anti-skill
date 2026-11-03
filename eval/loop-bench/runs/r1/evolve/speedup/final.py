from bisect import bisect_left, bisect_right


def usage_report(sessions, windows):
    # 14 x 16: a session inside one query gap only adds a constant r*(e-s) beyond it
    P = sorted({p for lo, hi in windows if lo < hi for p in (lo, hi)})
    m = len(P)
    BR = [0] * (m + 1)
    BX = [0] * (m + 1)
    bc = [0] * (m + 1)
    ec = [0] * (m + 1)
    for s, e, r in sessions:
        if s < e:
            i = bisect_right(P, s)
            j = bisect_left(P, e, i)
            if i == j:
                BX[i] += r * (s - e)
                bc[i] += 1
                ec[i] += 1
            else:
                BR[i] += r
                BR[j] -= r
                BX[i] += r * s
                BX[j] -= r * e
                bc[i] += 1
                ec[j] += 1
    F = {}
    NS = {}
    NE = {}
    a = b = c = g = 0
    for k in range(m):
        a += BR[k]; b += BX[k]; c += bc[k]; g += ec[k]
        x = P[k]
        F[x] = x * a - b
        NS[x] = c
        NE[x] = g
    out = []
    for lo, hi in windows:
        if lo < hi:
            out.append((F[hi] - F[lo], NS[hi] - NE[lo]))
        else:
            out.append((0, 0))
    return out
