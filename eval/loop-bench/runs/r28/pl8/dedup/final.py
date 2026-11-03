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
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in range(a + 1, len(g)):
                    pairs.append((ga, g[b]))
    uniq = list(groups)
    freq = {}
    for s in uniq:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    order = sorted(range(len(uniq)), key=lambda k: len(uniq[k]))
    rank = {t: i for i, t in enumerate(sorted(freq, key=lambda t: (freq[t], t)))}
    index = {}
    start = {}
    sizes = []
    sets = []
    ids = []
    rk = rank.__getitem__
    for k in order:
        s = uniq[k]
        n = len(s)
        toks = sorted(s, key=rk)
        minsize = (4 * n + 4) // 5
        pre = n - (4 * n + 4) // 5 + 1
        me = len(sets)
        cands = set()
        for t in toks[:pre]:
            lst = index.get(t)
            if lst:
                st = start[t]
                ln = len(lst)
                while st < ln and sizes[lst[st]] < minsize:
                    st += 1
                start[t] = st
                if st:
                    cands.update(lst[st:])
                else:
                    cands.update(lst)
        if cands:
            mine = groups[s]
            for c in cands:
                m = sizes[c]
                inter = len(s & sets[c])
                if 9 * inter >= 4 * (n + m):
                    for i in mine:
                        for j in ids[c]:
                            pairs.append((i, j) if i < j else (j, i))
        sizes.append(n)
        sets.append(s)
        ids.append(groups[s])
        ipre = n - (8 * n + 8) // 9 + 1
        for t in toks[:ipre]:
            lst = index.get(t)
            if lst is None:
                index[t] = [me]
                start[t] = 0
            else:
                lst.append(me)
    return pairs
