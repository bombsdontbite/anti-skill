from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    add = groups.setdefault
    for i, r in enumerate(records):
        add(frozenset(r.split()), []).append(i)
    groups.pop(frozenset(), None)
    sets = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.__getitem__)
    rank = dict(zip(order, range(len(order)))).__getitem__
    sizes = [len(s) for s in sets]
    index = {}
    found = []
    for x, s in enumerate(sets):
        a = sizes[x]
        m = (4 * a + 4) // 5
        cand = None
        for t in sorted(s, key=rank)[:a - m + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
            else:
                if cand is None:
                    cand = set(lst)
                else:
                    cand.update(lst)
                lst.append(x)
        if cand is None:
            continue
        for y in cand:
            if sizes[y] >= m and 9 * len(s & sets[y]) >= 4 * (a + sizes[y]):
                found.append((y, x))
    pairs = []
    for g in groups.values():
        n = len(g)
        if n > 1:
            for u in range(n):
                gu = g[u]
                for v in range(u + 1, n):
                    pairs.append((gu, g[v]))
    for y, x in found:
        gy = groups[sets[y]]
        for i in groups[sets[x]]:
            for j in gy:
                pairs.append((i, j) if i < j else (j, i))
    return pairs
