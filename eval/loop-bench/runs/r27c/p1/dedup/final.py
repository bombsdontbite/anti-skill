from collections import Counter
from bisect import bisect_left
from itertools import chain, combinations


def near_duplicates(records):
    groups = {}
    gg = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = gg(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    app = pairs.append
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    items = sorted(groups, key=len)
    sizes = list(map(len, items))
    k = bisect_left(sizes, 4)
    freq = Counter(chain.from_iterable(items[k:]))
    rank = dict(zip(sorted(freq, key=freq.get), range(len(freq))))
    rk = rank.get
    first = [bisect_left(sizes, m) for m in range(sizes[-1] + 2)] if sizes else []
    index = {}
    ig = index.get
    k5 = bisect_left(sizes, 5)
    for s in items[k:k5]:
        t = min(map(rk, s))
        lst = ig(t)
        if lst is None:
            index[t] = [k]
        else:
            lst.append(k)
        k += 1
    for s in items[k5:]:
        n = sizes[k]
        minlen = (4 * n + 4) // 5
        pre = sorted(map(rk, s))[:n - minlen + 1]
        kmin = first[minlen]
        cands = set()
        for t in pre:
            lst = ig(t)
            if lst is not None:
                cands.update(lst[bisect_left(lst, kmin):])
        for t in pre[:n - (8 * n + 8) // 9 + 1]:
            lst = ig(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
        if cands:
            n4 = 4 * n
            gk = groups[s]
            for c in cands:
                if 9 * len(s & items[c]) >= n4 + 4 * sizes[c]:
                    for i in groups[items[c]]:
                        for j in gk:
                            app((i, j) if i < j else (j, i))
        k += 1
    return pairs
