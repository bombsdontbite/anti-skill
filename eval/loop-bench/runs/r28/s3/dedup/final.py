from collections import Counter
from itertools import chain, combinations


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    pairs = []
    for s, g in groups.items():
        if len(g) > 1 and s:
            pairs.extend(combinations(g, 2))
    # distinct sets below 4 tokens are never 80 % alike
    keys = [s for s in groups if len(s) >= 4]
    if len(keys) < 2:
        return pairs
    freq = Counter(chain.from_iterable(keys))
    order = sorted(freq)
    order.sort(key=freq.get)
    rank = dict(zip(order, range(len(order)))).get
    keys.sort(key=len)
    index = {}
    for s in keys:
        n = len(s)
        minm = (4 * n + 4) // 5
        toks = sorted(s, key=rank)
        cands = set()
        for t in toks[:n - minm + 1]:
            lst = index.get(t)
            if lst:
                # sets come in size order, so ones too small now stay too small
                if len(lst[0]) < minm:
                    k = 1
                    while k < len(lst) and len(lst[k]) < minm:
                        k += 1
                    del lst[:k]
                cands.update(lst)
        # a later, no smaller set needs 8/9 of this one in common
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
        if cands:
            gx = groups[s]
            for b in cands:
                if 9 * len(s & b) >= 4 * (n + len(b)):
                    for j in groups[b]:
                        for i in gx:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
