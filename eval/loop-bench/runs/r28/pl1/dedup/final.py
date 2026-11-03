def near_duplicates(records):
    groups = {}
    for idx, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [idx]
            else:
                g.append(idx)
    sets = list(groups)
    sets.sort(key=len)
    members = [groups[s] for s in sets]

    freq = {}
    for s in sets:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    order = sorted(freq, key=freq.__getitem__)
    rank = {t: k for k, t in enumerate(order)}

    index = {}
    pairs = []
    for x, s in enumerate(sets):
        n = len(s)
        toks = sorted(s, key=rank.__getitem__)
        minsize = (4 * n + 4) // 5
        cands = set()
        for t in toks[:n - minsize + 1]:
            lst = index.get(t)
            if lst is not None:
                cands.update(lst)
        if cands:
            for y in cands:
                b = sets[y]
                m = len(b)
                if m < minsize:
                    continue
                inter = len(s & b)
                if 5 * inter >= 4 * (n + m - inter):
                    for i in members[x]:
                        for j in members[y]:
                            pairs.append((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
        g = members[x]
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in range(a + 1, len(g)):
                    pairs.append((ga, g[b]))
    return pairs
