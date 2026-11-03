from collections import Counter


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
    sets = list(groups)
    ids = list(groups.values())
    for g in ids:
        n = len(g)
        if n > 1:
            for a in range(n):
                ga = g[a]
                for b in range(a + 1, n):
                    pairs.append((ga, g[b]))
    freq = Counter()
    for s in sets:
        freq.update(s)
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.get))}
    rg = rank.get
    toks = [sorted(map(rg, s)) for s in sets]
    order = sorted(range(len(sets)), key=lambda k: len(toks[k]))
    index = {}
    ig = index.get
    for k in order:
        tk = toks[k]
        n = len(tk)
        minlen = (4 * n + 4) // 5
        seen = set()
        for t in tk[:n - minlen + 1]:
            lst = ig(t)
            if lst:
                seen.update(lst)
        if seen:
            s = sets[k]
            for c in seen:
                o = sets[c]
                lo = len(o)
                if lo < minlen:
                    continue
                inter = len(s & o)
                if 5 * inter >= 4 * (n + lo - inter):
                    for x in ids[k]:
                        for y in ids[c]:
                            pairs.append((x, y) if x < y else (y, x))
        for t in tk[:n - (8 * n + 8) // 9 + 1]:
            lst = ig(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
    return pairs
