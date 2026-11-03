from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    groups = {}
    for i, s in enumerate(sets):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    if len(groups) < len(sets):
        for g in groups.values():
            if len(g) > 1:
                pairs.extend([(g[a], g[b]) for a in range(len(g)) for b in range(a + 1, len(g))])

    def emit(a, b):
        for i in groups[a]:
            for j in groups[b]:
                pairs.append((i, j) if i < j else (j, i))

    # below 8 tokens a partner is identical or has exactly one token more
    for b in [s for s in groups if 4 < len(s) < 9]:
        for y in b:
            if b - {y} in groups:
                emit(b - {y}, b)
    big = sorted([s for s in groups if len(s) > 7], key=len)
    if len(big) < 2:
        return pairs
    cnt = Counter(chain.from_iterable(big))
    order = sorted(cnt, key=cnt.get)
    key = dict(zip(order, range(len(order)))).get
    index = {}
    get = index.get
    for x, a in enumerate(big):
        n = len(a)
        toks = sorted(a, key=key)
        cands = set()
        for t in toks[:n - (4 * n + 4) // 5 + 1]:
            lst = get(t)
            if lst:
                cands.update(lst)
        for y in cands:
            b = big[y]
            inter = len(a & b)
            if 5 * inter >= 4 * (n + len(b) - inter):
                emit(a, b)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    return pairs
