from operator import itemgetter

_k0 = itemgetter(0)
_k1 = itemgetter(1)


def usage_report(sessions, windows):
    if not sessions or not windows:
        return [(0, 0)] * len(windows)
    L = sorted(sessions, key=_k0)
    Q = sorted(set([w[0] for w in windows] + [w[1] for w in windows]))
    FS = {}
    CS = {}
    it = iter(Q)
    x = next(it)
    a = b = c = 0
    try:
        for s, _, r in L:
            while s >= x:
                FS[x] = x * a - b
                CS[x] = c
                x = next(it)
            a += r
            b += r * s
            c += 1
        FS[x] = x * a - b
        CS[x] = c
        for x in it:
            FS[x] = x * a - b
            CS[x] = c
    except StopIteration:
        pass
    FE = {}
    CE = {}
    it = iter(Q)
    x = next(it)
    a = b = c = 0
    L.sort(key=_k1)
    try:
        for _, e, r in L:
            while e > x:
                FE[x] = x * a - b
                CE[x] = c
                x = next(it)
            a += r
            b += r * e
            c += 1
        FE[x] = x * a - b
        CE[x] = c
        for x in it:
            FE[x] = x * a - b
            CE[x] = c
    except StopIteration:
        pass
    return [(FS[hi] - FE[hi] - FS[lo] + FE[lo], CS[hi] - CE[lo]) for lo, hi in windows]
