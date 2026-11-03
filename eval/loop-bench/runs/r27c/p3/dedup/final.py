def near_duplicates(records):
    S = list(map(frozenset, map(str.split, records)))
    d = dict(zip(S, range(len(S))))
    empty = frozenset()
    d.pop(empty, None)
    pairs = []
    multi = None
    if len(d) + S.count(empty) < len(S):
        multi = {}
        for i, s in enumerate(S):
            if s:
                r = d[s]
                if r != i:
                    g = multi.get(r)
                    if g is None:
                        multi[r] = [i]
                    else:
                        g.append(i)
        for r, g in multi.items():
            g.append(r)
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    get_d = d.get
    for s, a in d.items():
        if 4 < len(s) < 9:
            for t in s:
                b = get_d(s.difference((t,)))
                if b is not None:
                    if multi is None:
                        pairs.append((a, b) if a < b else (b, a))
                    else:
                        for x in multi.get(a) or (a,):
                            for y in multi.get(b) or (b,):
                                pairs.append((x, y) if x < y else (y, x))
    big = [x for x in d.items() if len(x[0]) > 7]
    if len(big) < 2:
        return pairs
    sets = [x[0] for x in big]
    reps = [x[1] for x in big]
    freq = {}
    for s in sets:
        for t in s:
            freq[t] = freq.get(t, 0) + 1
    rank = {t: r for r, t in enumerate(sorted(freq, key=freq.__getitem__))}
    rk = rank.__getitem__
    sizes = list(map(len, sets))
    order = sorted(range(len(sets)), key=sizes.__getitem__)
    W = sizes[order[-1]] + 1
    index = {}
    get = index.get
    for k in order:
        n = sizes[k]
        s = sets[k]
        cands = None
        if n < 9:
            key = min(map(rk, s)) * W + n
            lst = get(key)
            if lst is None:
                index[key] = [k]
            else:
                lst.append(k)
            continue
        else:
            toks = sorted(map(rk, s))
            for m in range((4 * n + 4) // 5, n + 1 if n > 8 else n):
                for t in toks[:n - (4 * (n + m) + 8) // 9 + 1]:
                    lst = get(t * W + m)
                    if lst is not None:
                        if cands is None:
                            cands = set(lst)
                        else:
                            cands.update(lst)
            for t in toks[:n - (8 * n + 8) // 9 + 1]:
                key = t * W + n
                lst = get(key)
                if lst is None:
                    index[key] = [k]
                else:
                    lst.append(k)
        if cands:
            a = reps[k]
            for c in cands:
                if 9 * len(s & sets[c]) >= 4 * (n + sizes[c]):
                    b = reps[c]
                    if multi is None:
                        pairs.append((a, b) if a < b else (b, a))
                    else:
                        for x in multi.get(a) or (a,):
                            for y in multi.get(b) or (b,):
                                pairs.append((x, y) if x < y else (y, x))
    return pairs
