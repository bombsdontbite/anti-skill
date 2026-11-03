from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    app = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for p in range(len(g)):
                gp = g[p]
                for q in range(p + 1, len(g)):
                    app((gp, g[q]))
    uniq = [s for s in groups if len(s) >= 4]
    if not uniq:
        return pairs
    freq = Counter(chain.from_iterable(uniq))
    uniq.sort(key=len)
    m = len(uniq[-1]) + 1
    rank = {t: k * m for k, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rk = rank.__getitem__
    index = {}
    get = index.get
    for x, sx in enumerate(uniq):
        a = len(sx)
        toks = sorted(map(rk, sx))
        cands = set()
        for b in range((4 * a + 4) // 5, a + 1):
            for t in toks[:a - (4 * (a + b) + 8) // 9 + 1]:
                lst = get(t + b)
                if lst:
                    cands.update(lst)
        if cands:
            gx = groups[sx]
            for y in cands:
                sy = uniq[y]
                if 9 * len(sx & sy) >= 4 * (a + len(sy)):
                    for i in groups[sy]:
                        for j in gx:
                            app((i, j) if i < j else (j, i))
        for t in toks[:a - (8 * a + 8) // 9 + 1]:
            t += a
            lst = get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    return pairs
