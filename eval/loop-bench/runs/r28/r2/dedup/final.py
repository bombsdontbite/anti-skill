from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    app = pairs.append
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    app((gx, y))
    sets = list(groups)
    freq = Counter(chain.from_iterable(sets))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    sets.sort(key=len)
    index = {}
    get = index.get
    rk = rank.get
    for a in sets:
        n = len(a)
        m = (4 * n + 4) // 5
        toks = sorted(a, key=rk)
        p = n - m + 1
        q = n - (8 * n + 8) // 9 + 1
        cands = set()
        for t in toks[:q]:
            lst = get(t)
            if lst is None:
                index[t] = [a]
            else:
                cands.update(lst)
                lst.append(a)
        for t in toks[q:p]:
            lst = get(t)
            if lst is not None:
                cands.update(lst)
        if cands:
            ga = groups[a]
            for b in cands:
                lb = len(b)
                if lb < m:
                    continue
                inter = len(a & b)
                if 5 * inter >= 4 * (n + lb - inter):
                    for i in ga:
                        for j in groups[b]:
                            app((i, j) if i < j else (j, i))
    return pairs
