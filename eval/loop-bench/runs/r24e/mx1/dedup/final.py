def near_duplicates(records):
    sl = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sl, range(len(sl))))
    last.pop(frozenset(), None)
    pairs = []
    append = pairs.append
    dups = {}
    if len(last) < len(sl):
        for i in sorted(set(range(len(sl))).difference(last.values())):
            s = sl[i]
            if s:
                g = dups.get(s)
                if g is None:
                    dups[s] = [i]
                else:
                    g.append(i)
        for s, g in dups.items():
            g.append(last[s])
            for a in range(len(g) - 1):
                ga = g[a]
                for b in g[a + 1:]:
                    append((ga, b))

    def emit(s, o):
        gx = dups.get(s) or (last[s],)
        gy = dups.get(o) or (last[o],)
        for a in gx:
            for b in gy:
                append((a, b) if a < b else (b, a))

    # Distinct sets of sizes m <= n <= 8 match only when m = n - 1 and the smaller is a subset,
    # so sets under 4 have no partner and sizes 5..8 only look up their one-token deletions,
    # found through sums of token hashes; a collision between those sums falls back to frozensets.
    uniq = sorted([s for s in last if len(s) > 3], key=len)
    lens = list(map(len, uniq))
    i5 = lens.count(4)
    i8 = i5 + lens.count(5) + lens.count(6) + lens.count(7)
    i9 = i8 + lens.count(8)
    small = uniq[:i9]
    hs = list(map(sum, map(map, [hash] * i9, small)))
    byh = dict(zip(hs, small))
    if len(byh) == len(small):
        hkeys = byh.keys()
        for x, hx in zip(small[i5:], hs[i5:]):
            subs = [hx - h for h in map(hash, x)]
            if not hkeys.isdisjoint(subs):
                for v in subs:
                    y = byh.get(v)
                    if y is not None and y < x and 5 * len(y) >= 4 * len(x):
                        emit(x, y)
    else:
        keys = last.keys()
        for x in small[i5:]:
            for y in keys & map(x.difference, zip(x)):
                emit(x, y)
    large = uniq[i8:]
    freq = {}
    fget = freq.get
    for s in large:
        for t in s:
            freq[t] = fget(t, 0) + 1
    key = dict(zip(sorted(freq, key=fget), range(len(freq)))).get
    index = {}
    get = index.get
    for s in large:
        n = len(s)
        if n == 8:
            t = min(s, key=key)
            lst = get(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
            continue
        ranked = sorted(s, key=key)
        q = n - (8 * n + 8) // 9 + 1
        cands = set()
        for t in ranked[:q]:
            lst = get(t)
            if lst is None:
                index[t] = [s]
            else:
                cands.update(lst)
                lst.append(s)
        for lst in map(get, ranked[q:n - (4 * n + 4) // 5 + 1]):
            if lst:
                cands.update(lst)
        lo = 4 * n
        for o in cands:
            m = len(o)
            if 5 * m >= lo and 9 * len(s & o) >= 4 * (n + m):
                emit(s, o)
    return pairs
