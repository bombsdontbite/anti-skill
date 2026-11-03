from collections import Counter
from itertools import chain
from bisect import bisect_left

def near_duplicates(records):
    sets = [frozenset(r.split()) for r in records]
    groups = {}
    for i, s in enumerate(sets):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    keys = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(keys))
    byf = sorted(freq, key=freq.get)
    n1 = bisect_left([freq[w] for w in byf], 2)
    rank = {w: r for r, w in enumerate(byf)}
    fk = rank.get
    index = [None] * len(byf)
    lens = [len(k) for k in keys]
    for ki in range(bisect_left(lens, 4), len(keys)):
        la = lens[ki]
        minlen = (4 * la + 4) // 5
        toks = sorted(map(fk, keys[ki]))
        u = bisect_left(toks, n1)
        p = la - minlen + 1
        if u >= p:
            continue
        cands = set()
        for w in toks[u:p]:
            lst = index[w]
            if lst is None:
                index[w] = [ki]
            else:
                cands.update(lst)
                lst.append(ki)
        if cands:
            a = keys[ki]
            ga = groups[a]
            for kj in cands:
                lb = lens[kj]
                if lb < minlen:
                    continue
                b = keys[kj]
                if 9 * len(a & b) >= 4 * (la + lb):
                    for x in groups[b]:
                        for y in ga:
                            pairs.append((x, y) if x < y else (y, x))
    return pairs
