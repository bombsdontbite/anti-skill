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
    big = []
    sums = {}
    mid = []
    for s, g in groups.items():
        if len(g) > 1:
            for a in range(len(g)):
                for b in range(a + 1, len(g)):
                    pairs.append((g[a], g[b]))
        n = len(s)
        if n >= 4:
            if n <= 8:
                hl = list(map(hash, s))
                h = sum(hl)
                if n < 8:
                    l = sums.get(h)
                    if l is None:
                        sums[h] = [s]
                    else:
                        l.append(s)
                if n >= 5:
                    mid.append((s, h, hl))
            if n >= 8:
                big.append(s)
    # with 8 tokens or fewer, the only distinct matches are s minus one token;
    # find them by the sum of token hashes, then check
    for s, h, hl in mid:
        n1 = len(s) - 1
        for x in hl:
            l = sums.get(h - x)
            if l is not None:
                for a in l:
                    if len(a) == n1 and a < s:
                        for i in groups[s]:
                            for j in groups[a]:
                                pairs.append((i, j) if i < j else (j, i))
    if not big:
        return pairs
    freq = {}
    for s in big:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    rank = dict(zip(sorted(freq, key=freq.get), range(len(freq))))
    rk = rank.get
    big.sort(key=len)
    index = {}
    for s in big:
        n = len(s)
        minlen = (4 * n + 4) // 5
        toks = sorted(s, key=rk)
        cand = set()
        if n > 8:
            for t in toks[:n - minlen + 1]:
                lst = index.get(t)
                if lst is not None:
                    cand.update(lst)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
        if cand:
            gx = groups[s]
            for o in cand:
                m = len(o)
                if m >= minlen:
                    inter = len(s & o)
                    if 5 * inter >= 4 * (n + m - inter):
                        for i in gx:
                            for j in groups[o]:
                                pairs.append((i, j) if i < j else (j, i))
    return pairs
