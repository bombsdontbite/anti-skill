from collections import Counter
from itertools import chain, count, groupby, repeat
from operator import add, mul


def near_duplicates(records):
    groups = {}
    gget = groups.get
    i = 0
    for k in map(frozenset, map(str.split, records)):
        g = gget(k)
        if g is None:
            groups[k] = [i]
        else:
            g.append(i)
        i += 1
    groups.pop(frozenset(), None)
    pairs = []
    append = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for u in range(len(g)):
                gu = g[u]
                for v in g[u + 1:]:
                    append((gu, v))
    big = [a for a in groups if len(a) > 3]
    freq = Counter(chain.from_iterable(big))
    key = dict(zip(freq, map(add, map(mul, freq.values(), repeat(1 << 30)), count()))).get
    index = {}
    get = index.get
    big.sort(key=len)
    for n, same in groupby(big, len):
        if n == 4:
            for a in same:
                t = min(a, key=key)
                lst = get(t)
                if lst is None:
                    index[t] = [a]
                else:
                    lst.append(a)
            continue
        minsz = (4 * n + 4) // 5
        p = n - minsz + 1
        q = n - (8 * n + 8) // 9 + 1
        for a in same:
            toks = sorted(a, key=key)
            cands = set()
            for t in toks[q:p]:
                lst = get(t)
                if lst is not None:
                    cands.update(lst)
            for t in toks[:q]:
                lst = get(t)
                if lst is None:
                    index[t] = [a]
                else:
                    cands.update(lst)
                    lst.append(a)
            for b in cands:
                m = len(b)
                if m >= minsz:
                    inter = len(a & b)
                    if 5 * inter >= 4 * (n + m - inter):
                        ga = groups[a]
                        for j in groups[b]:
                            for i in ga:
                                append((i, j) if i < j else (j, i))
    return pairs
