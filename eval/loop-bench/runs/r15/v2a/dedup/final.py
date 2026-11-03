from collections import Counter
from itertools import chain
from bisect import bisect_left


def near_duplicates(records):
    splits = list(map(str.split, records))
    freq = Counter(chain.from_iterable(splits))
    order = sorted(freq, key=freq.get)
    rg = dict(zip(order, range(len(order)))).get
    groups = {}
    for i, sp in enumerate(splits):
        s = frozenset(map(rg, sp))
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g) - 1):
                ga = g[a]
                pairs.extend([(ga, b) for b in g[a + 1:]])
    sets = sorted(groups, key=len)
    if not sets:
        return pairs
    first = [0] * (len(sets[-1]) + 2)
    for k, s in enumerate(sets):
        first[len(s) + 1] = k + 1
    for L in range(1, len(first)):
        if first[L] < first[L - 1]:
            first[L] = first[L - 1]
    index = {}
    ig = index.get
    for k, s in enumerate(sets):
        n = len(s)
        toks = sorted(s)
        minlen = (4 * n + 4) // 5
        lo = first[minlen]
        cand = set()
        for t in toks[:n - minlen + 1]:
            lst = ig(t)
            if lst:
                if lst[0] >= lo:
                    cand.update(lst)
                elif lst[-1] >= lo:
                    cand.update(lst[bisect_left(lst, lo):])
        if cand:
            lim = 4 * n
            for c in cand:
                o = sets[c]
                if 9 * len(s & o) >= lim + 4 * len(o):
                    ga = groups[s]; gb = groups[o]
                    if len(ga) == 1 and len(gb) == 1:
                        x = ga[0]; y = gb[0]
                        pairs.append((x, y) if x < y else (y, x))
                    else:
                        for x in ga:
                            for y in gb:
                                pairs.append((x, y) if x < y else (y, x))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = ig(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
    return pairs
