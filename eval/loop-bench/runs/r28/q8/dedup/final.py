from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    sets = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.__getitem__)
    rank = dict(zip(order, range(len(order))))
    rget = rank.__getitem__
    index = [None] * len(order)
    pairs = []
    app = pairs.append
    for x, a in enumerate(sets):
        ga = groups[a]
        if len(ga) > 1:
            pairs.extend([(ga[p], ga[q]) for p in range(len(ga)) for q in range(p + 1, len(ga))])
        n = len(a)
        if n < 5:
            prefix = (min(map(rget, a)),)
            ki = 1
        else:
            prefix = sorted(map(rget, a))[:n - (4 * n + 4) // 5 + 1]
            ki = n - (8 * n + 8) // 9 + 1
        cands = None
        for p, t in enumerate(prefix):
            lst = index[t]
            if lst is None:
                if p < ki:
                    index[t] = [x]
            else:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
                if p < ki:
                    lst.append(x)
        if cands:
            lim = 4 * n
            for y in cands:
                b = sets[y]
                m = len(b)
                if 5 * m >= lim and 9 * len(a & b) >= 4 * (n + m):
                    gb = groups[b]
                    if len(ga) == 1 and len(gb) == 1:
                        i = ga[0]; j = gb[0]
                        app((i, j) if i < j else (j, i))
                    else:
                        for i in ga:
                            for j in gb:
                                app((i, j) if i < j else (j, i))
    return pairs
