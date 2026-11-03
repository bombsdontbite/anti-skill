from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    uniq = sorted(groups, key=len)
    glist = [groups[s] for s in uniq]
    for g in glist:
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    freq = Counter(chain.from_iterable(uniq))
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    index = {}
    iget = index.get
    for x, s in enumerate(uniq):
        n = len(s)
        minsize = (4 * n + 4) // 5
        cands = None
        for t in sorted(s, key=rget)[:n - minsize + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [x]
            else:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
                lst.append(x)
        if cands is None:
            continue
        for y in cands:
            b = uniq[y]
            m = len(b)
            if m >= minsize:
                inter = len(s & b)
                if 5 * inter >= 4 * (n + m - inter):
                    gx = glist[x]
                    for j in glist[y]:
                        for i in gx:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
