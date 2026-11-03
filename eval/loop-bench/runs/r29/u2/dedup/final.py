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
    sets = []
    for s, g in groups.items():
        sets.append(s)
        n = len(g)
        if n > 1:
            for x in range(n):
                gx = g[x]
                for y in range(x + 1, n):
                    pairs.append((gx, g[y]))
    if len(sets) < 2:
        return pairs
    freq = {}
    for s in sets:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    sets.sort(key=len)
    index = {}
    iget = index.get
    sizes = []
    for k, s in enumerate(sets):
        a = len(s)
        sizes.append(a)
        toks = sorted(map(rget, s))
        minsz = (4 * a + 4) // 5
        p = a - minsz + 1
        cands = set()
        for t in toks[:p]:
            lst = iget(t)
            if lst:
                cands.update(lst)
        for c in cands:
            b = sizes[c]
            if b >= minsz:
                o = sets[c]
                if 9 * len(s & o) >= 4 * (a + b):
                    gk = groups[s]
                    gc = groups[o]
                    for u in gk:
                        for v in gc:
                            pairs.append((u, v) if u < v else (v, u))
        for t in toks[:a - (8 * a + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
    return pairs
