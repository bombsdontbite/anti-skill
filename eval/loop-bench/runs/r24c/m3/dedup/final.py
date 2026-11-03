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
    empty = groups.pop(frozenset(), ())
    pairs = []
    if len(groups) + len(empty) < len(sets):
        for g in groups.values():
            if len(g) > 1:
                for a in range(len(g)):
                    ga = g[a]
                    for b in g[a + 1:]:
                        pairs.append((ga, b))
    uniq = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(uniq))
    fget = freq.__getitem__
    index = {}
    iget = index.get
    for x, s in enumerate(uniq):
        n = len(s)
        toks = sorted(s, key=fget)
        minsize = (4 * n + 4) // 5
        p = n - minsize + 1
        # Ties in frequency have no fixed order, so the prefix takes every
        # token tied with its last one: a superset of the prefix under any
        # tie-break, which keeps the filter exact.
        f = fget(toks[p - 1])
        if f == 1:
            continue
        while p < n and fget(toks[p]) == f:
            p += 1
        k = 0
        while fget(toks[k]) == 1:
            k += 1
        cand = set()
        for w in toks[k:p]:
            lst = iget(w)
            if lst is None:
                index[w] = [x]
            else:
                cand.update(lst)
                lst.append(x)
        for y in cand:
            t = uniq[y]
            m = len(t)
            if m < minsize:
                continue
            inter = len(s & t)
            if 5 * inter >= 4 * (n + m - inter):
                gx = groups[s]
                gy = groups[t]
                for a in gx:
                    for b in gy:
                        pairs.append((a, b) if a < b else (b, a))
    return pairs
