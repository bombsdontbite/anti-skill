from collections import Counter
from itertools import chain, combinations


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sets, range(len(sets))))
    pairs = []
    groups = {}
    if len(last) < len(sets):
        for i, s in enumerate(sets):
            if last[s] != i:
                g = groups.get(s)
                if g is None:
                    groups[s] = [i]
                else:
                    g.append(i)
        for s, g in groups.items():
            g.append(last[s])
            if s:
                pairs.extend(combinations(g, 2))
    # Two distinct sets of size <= 3 are never 80 % alike.
    keys = [s for s in last if len(s) > 3]
    if len(keys) < 2:
        return pairs
    freq = Counter(chain.from_iterable(keys))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    get = rank.get
    buckets = {}
    for s in keys:
        n = len(s)
        b = buckets.get(n)
        if b is None:
            buckets[n] = [s]
        else:
            b.append(s)
    index = {}
    iget = index.get
    gget = groups.get
    for n in sorted(buckets):
        minlen = (4 * n + 4) // 5
        plen = n - minlen + 1
        ilen = n - (8 * n + 8) // 9 + 1
        for a in buckets[n]:
            toks = sorted(a, key=get)
            cands = set()
            for t in toks[:ilen]:
                lst = iget(t)
                if lst is None:
                    index[t] = [a]
                else:
                    cands.update(lst)
                    lst.append(a)
            for t in toks[ilen:plen]:
                lst = iget(t)
                if lst is not None:
                    cands.update(lst)
            for b in cands:
                lb = len(b)
                if lb >= minlen and 9 * len(a & b) >= 4 * (n + lb):
                    ga = gget(a)
                    gb = gget(b)
                    if ga is None and gb is None:
                        x = last[a]
                        y = last[b]
                        pairs.append((x, y) if x < y else (y, x))
                    else:
                        for x in gb or (last[b],):
                            for y in ga or (last[a],):
                                pairs.append((x, y) if x < y else (y, x))
    return pairs
