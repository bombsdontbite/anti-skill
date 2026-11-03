from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    keys = sorted(groups, key=len)
    lens = list(map(len, keys))
    rank = {t: r for r, (t, _) in enumerate(reversed(Counter(chain.from_iterable(keys)).most_common()))}
    rget = rank.get
    nk = len(keys)
    maxn = lens[-1] if keys else 0
    firstat = [nk] * (maxn + 2)
    for k in range(nk - 1, -1, -1):
        firstat[lens[k]] = k
    for n in range(maxn, -1, -1):
        if firstat[n] > firstat[n + 1]:
            firstat[n] = firstat[n + 1]
    index = {}
    iget = index.get
    for k, s in enumerate(keys):
        n = lens[k]
        minsize = (4 * n + 4) // 5
        lo = firstat[minsize]
        cands = set()
        for t in sorted(map(rget, s))[:n - minsize + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                if lst[-1] >= lo:
                    if lst[0] >= lo:
                        cands.update(lst)
                    else:
                        p = len(lst) - 2
                        while lst[p] >= lo:
                            p -= 1
                        cands.update(lst[p + 1:])
                lst.append(k)
        if cands:
            m = 4 * n
            for c in cands:
                b = keys[c]
                if 9 * len(s & b) >= m + 4 * lens[c]:
                    gi = groups[s]
                    gj = groups[b]
                    for i in gi:
                        for j in gj:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
