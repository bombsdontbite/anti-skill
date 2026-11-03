from collections import Counter
from itertools import chain


def near_duplicates(records):
    byrec = {}
    for idx, r in enumerate(records):
        g = byrec.get(r)
        if g is None:
            byrec[r] = [idx]
        else:
            g.append(idx)
    groups = {}
    for r, g in byrec.items():
        s = frozenset(r.split())
        if s:
            h = groups.get(s)
            if h is None:
                groups[s] = g
            else:
                h += g
    pairs = []
    big = []
    for s, g in groups.items():
        if len(g) > 1:
            g.sort()
            for x in range(len(g)):
                gx = g[x]
                for y in range(x + 1, len(g)):
                    pairs.append((gx, g[y]))
        if len(s) > 3:
            big.append(s)
    freq = Counter(chain.from_iterable(big))
    order = sorted(freq, key=freq.__getitem__)
    rank = dict(zip(order, range(len(order))))
    ns = 0
    for t in order:
        if freq[t] > 1:
            break
        ns += 1
    key = rank.__getitem__
    big.sort(key=len)
    index = {}
    get = index.get
    for k, s in enumerate(big):
        n = len(s)
        p = n - (4 * n + 4) // 5 + 1
        toks = sorted(map(key, s))
        lo = 0
        while lo < p and toks[lo] < ns:
            lo += 1
        if lo == p:
            continue
        q = n - (8 * n + 8) // 9 + 1
        cands = None
        for x in range(lo, p):
            t = toks[x]
            lst = get(t)
            if lst is None:
                if x < q:
                    index[t] = [k]
            else:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
                if x < q:
                    lst.append(k)
        if cands is not None:
            minlen = (4 * n + 4) // 5
            ga = groups[s]
            for c in cands:
                b = big[c]
                lb = len(b)
                if lb < minlen:
                    continue
                inter = len(s & b)
                if 5 * inter >= 4 * (n + lb - inter):
                    for i in ga:
                        for j in groups[b]:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
