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
    for g in groups.values():
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in range(a + 1, len(g)):
                    pairs.append((ga, g[b]))
    keys = sorted(groups, key=len)
    freq = {}
    fg = freq.get
    for s in keys:
        for t in s:
            freq[t] = fg(t, 0) + 1
    rank = {t: k for k, t in enumerate(sorted(freq, key=freq.get))}
    sets = []
    sizes = []
    index = {}
    starts = {}
    for x, s in enumerate(keys):
        n = len(s)
        toks = sorted([rank[t] for t in s])
        minsize = (4 * n + 4) // 5
        seen = set()
        for t in toks[:n - minsize + 1]:
            lst = index.get(t)
            if lst is None:
                continue
            st = starts[t]
            while st < len(lst) and sizes[lst[st]] < minsize:
                st += 1
            starts[t] = st
            for k in range(st, len(lst)):
                y = lst[k]
                if y in seen:
                    continue
                seen.add(y)
                m = sizes[y]
                if 9 * len(s & sets[y]) >= 4 * (n + m):
                    gx = groups[s]
                    gy = groups[keys[y]]
                    for a in gx:
                        for b in gy:
                            pairs.append((a, b) if a < b else (b, a))
        sets.append(s)
        sizes.append(n)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
                starts[t] = 0
            else:
                lst.append(x)
    return pairs
