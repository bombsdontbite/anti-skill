def near_duplicates(records):
    groups = {}
    gget = groups.get
    for i, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = gget(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    if len(groups) < len(records):
        for g in groups.values():
            if len(g) > 1:
                for x in range(len(g) - 1):
                    gx = g[x]
                    for y in g[x + 1:]:
                        pairs.append((gx, y))
    if len(groups) < 2:
        return pairs
    sets = sorted(groups, key=len)
    freq = {}
    fget = freq.get
    for s in sets:
        for t in s:
            freq[t] = fget(t, 0) + 1
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get
    index = {}
    iget = index.get
    for s in sets:
        a = len(s)
        if a < 5:
            t = min(map(rget, s))
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                for b in lst:
                    if 9 * len(s & b) >= 4 * (a + len(b)):
                        gi = groups[s]
                        gj = groups[b]
                        for i in gi:
                            for j in gj:
                                pairs.append((i, j) if i < j else (j, i))
                lst.append(s)
            continue
        else:
            pre = sorted(map(rget, s))[:a - (4 * a + 4) // 5 + 1]
        cands = None
        for t in pre:
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
                lst.append(s)
        if cands:
            for b in cands:
                if 9 * len(s & b) >= 4 * (a + len(b)):
                    gi = groups[s]
                    gj = groups[b]
                    for i in gi:
                        for j in gj:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
