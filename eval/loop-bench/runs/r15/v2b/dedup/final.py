from collections import Counter
from itertools import chain
from operator import itemgetter


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
    append = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    append((gx, y))
    # Sets of up to 3 tokens only reach 80 % with an identical set.
    sets = [s for s in groups if len(s) > 3]
    if len(sets) < 2:
        return pairs
    freq = Counter(chain.from_iterable(sets))
    rank = {t: r for r, (t, _) in enumerate(sorted(freq.items(), key=itemgetter(1)))}
    key = rank.__getitem__
    sets.sort(key=len)
    index = {}
    get = index.get
    for k, a in enumerate(sets):
        n = len(a)
        probe = n - (4 * n + 4) // 5 + 1
        ins = n - (8 * n + 8) // 9 + 1
        order = sorted(a, key=key)
        cands = set()
        for x in range(probe):
            t = order[x]
            lst = get(t)
            if lst is None:
                if x < ins:
                    index[t] = [k]
            else:
                cands.update(lst)
                if x < ins:
                    lst.append(k)
        if cands:
            ga = groups[a]
            n4 = 4 * n
            for c in cands:
                b = sets[c]
                m = len(b)
                if 5 * m < n4:
                    continue
                inter = len(a & b)
                if 5 * inter >= 4 * (n + m - inter):
                    for i in groups[b]:
                        for j in ga:
                            append((i, j) if i < j else (j, i))
    return pairs
