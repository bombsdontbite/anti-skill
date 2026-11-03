from collections import Counter
from itertools import chain


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
    sets = sorted(groups, key=len)
    glist = [groups[s] for s in sets]
    for g in glist:
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    freq = Counter(chain.from_iterable(sets))
    big = len(freq)
    rank = {t: c * big + i for i, (t, c) in enumerate(freq.items())}
    lo = 2 * big
    rget = rank.get
    lens = list(map(len, sets))
    index = {}
    iget = index.get
    for k in range(len(sets)):
        x = sets[k]
        n = lens[k]
        toks = sorted(map(rget, x))
        p = n - (4 * n + 4) // 5 + 1
        if toks[p - 1] < lo:
            continue
        minm = (4 * n + 4) // 5
        cand = set()
        for t in toks[:p]:
            if t >= lo:
                lst = iget(t)
                if lst:
                    for y in lst:
                        if lens[y] >= minm:
                            cand.add(y)
        for y in cand:
            if 9 * len(x & sets[y]) >= 4 * (n + lens[y]):
                for a in glist[k]:
                    for b in glist[y]:
                        pairs.append((a, b) if a < b else (b, a))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            if t >= lo:
                lst = iget(t)
                if lst is None:
                    index[t] = [k]
                else:
                    lst.append(k)
    return pairs
