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
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend([(a, b) for k, a in enumerate(g) for b in g[k + 1:]])
    if len(groups) < 2:
        return pairs
    keys = sorted(groups, key=len)
    n = len(keys)
    K = len(keys[-1]) + 2
    start = [n] * K
    for x in range(n - 1, -1, -1):
        start[len(keys[x])] = x
    for a in range(K - 2, -1, -1):
        if start[a] > start[a + 1]:
            start[a] = start[a + 1]
    probe = [a - (4 * a + 4) // 5 + 1 for a in range(K)]
    indexed = [a - (8 * a + 8) // 9 + 1 for a in range(K)]
    first = [start[(4 * a + 4) // 5] for a in range(K)]
    freq = Counter(chain.from_iterable(keys))
    order = sorted(freq, key=freq.get)
    rank = dict(zip(order, range(len(order))))
    ones = list(freq.values()).count(1)
    rk = rank.get
    index = {}
    get = index.get
    P = [sorted(map(rk, s))[:probe[len(s)]] for s in keys]
    for x in [x for x, p in enumerate(P) if p[-1] >= ones]:
        s = keys[x]
        p = P[x]
        a = len(s)
        cands = set()
        f = first[a]
        for t in p:
            lst = get(t)
            if lst:
                if lst[0] < f:
                    k = 1
                    m = len(lst)
                    while k < m and lst[k] < f:
                        k += 1
                    del lst[:k]
                cands.update(lst)
        for t in p[:indexed[a]]:
            if t >= ones:
                lst = get(t)
                if lst is None:
                    index[t] = [x]
                else:
                    lst.append(x)
        if cands:
            ga = groups[s]
            for y in cands:
                b = keys[y]
                if 9 * len(s & b) >= 4 * (a + len(b)):
                    for i in ga:
                        for j in groups[b]:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
