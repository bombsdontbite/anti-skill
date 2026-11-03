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
    sets = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.__getitem__)
    rget = dict(zip(order, range(len(order)))).__getitem__
    index = {}
    iget = index.get
    lens = [len(s) for s in sets]
    out = []
    push = out.append
    for k, s in enumerate(sets):
        n = lens[k]
        m = (4 * n + 4) // 5
        pre = sorted(s, key=rget)[:n - m + 1]
        cands = set()
        for t in pre:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                cands.update(lst)
                lst.append(k)
        if cands:
            lim = 4 * n
            for c in cands:
                lb = lens[c]
                if lb >= m and 9 * len(s & sets[c]) >= lim + 4 * lb:
                    push((c, k))
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend([(a, b) for x, a in enumerate(g) for b in g[x + 1:]])
    for c, k in out:
        gc = groups[sets[c]]
        gk = groups[sets[k]]
        if len(gc) == 1 and len(gk) == 1:
            i = gc[0]; j = gk[0]
            pairs.append((i, j) if i < j else (j, i))
        else:
            for i in gc:
                for j in gk:
                    pairs.append((i, j) if i < j else (j, i))
    return pairs
