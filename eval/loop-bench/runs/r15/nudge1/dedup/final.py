from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    sd = groups.setdefault
    i = 0
    for s in map(frozenset, map(str.split, records)):
        sd(s, []).append(i)
        i += 1
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    if len(groups) < 2:
        return pairs
    freq = Counter(chain.from_iterable(groups))
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rk = rank.__getitem__
    sets = sorted(groups.items(), key=lambda x: len(x[0]))
    sizes = list(map(len, groups))
    sizes.sort()
    index = {}
    iget = index.get
    k = 0
    for s, g in sets:
        n = sizes[k]
        minsize = (4 * n + 4) // 5
        p = n - minsize + 1
        cands = set()
        for t in (sorted(s, key=rk)[:p] if p < n else s):
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                cands.update(lst)
                lst.append(k)
        for c in cands:
            m = sizes[c]
            if m < minsize:
                continue
            s2, g2 = sets[c]
            inter = len(s & s2)
            if 5 * inter >= 4 * (n + m - inter):
                if len(g) == 1 and len(g2) == 1:
                    pairs.append((g2[0], g[0]) if g2[0] < g[0] else (g[0], g2[0]))
                else:
                    for a in g:
                        for b in g2:
                            pairs.append((a, b) if a < b else (b, a))
        k += 1
    return pairs
