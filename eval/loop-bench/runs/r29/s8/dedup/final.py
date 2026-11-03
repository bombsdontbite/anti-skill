from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    # distinct sets of 3 or fewer tokens can never reach 0.8
    sets = sorted([s for s in groups if len(s) > 3], key=len)
    sizes = [len(s) for s in sets]
    freq = Counter(chain.from_iterable(sets))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rget = rank.__getitem__
    index = {}
    get = index.get
    for k, s in enumerate(sets):
        n = sizes[k]
        toks = sorted(map(rget, s))
        minsize = (4 * n + 4) // 5
        cands = set()
        for t in toks[:n - minsize + 1]:
            lst = get(t)
            if lst:
                if sizes[lst[0]] < minsize:
                    p = 1
                    L = len(lst)
                    while p < L and sizes[lst[p]] < minsize:
                        p += 1
                    del lst[:p]
                cands.update(lst)
        if cands:
            gi = groups[s]
            for c in cands:
                b = sets[c]
                if 9 * len(s & b) >= 4 * (n + sizes[c]):
                    for i in groups[b]:
                        for j in gi:
                            pairs.append((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst:
                lst.append(k)
            else:
                index[t] = [k]
    return pairs
