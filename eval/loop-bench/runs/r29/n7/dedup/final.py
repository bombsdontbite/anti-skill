def near_duplicates(records):
    fs = list(map(frozenset, map(str.split, records)))
    last = dict(zip(fs, range(len(fs))))
    last.pop(frozenset(), None)
    pairs = []
    append = pairs.append
    extra = {}
    if len(last) + (frozenset() in fs) < len(fs):
        for i, t in enumerate(fs):
            if t and last[t] != i:
                g = extra.get(t)
                if g is None:
                    extra[t] = [i, last[t]]
                else:
                    g.insert(-1, i)
        for g in extra.values():
            k = len(g)
            for x in range(k):
                gx = g[x]
                for y in range(x + 1, k):
                    append((gx, g[y]))
    keys = [k for k in last if len(k) > 3]
    keys.sort(key=len)
    freq = {}
    get = freq.get
    for s in keys:
        for w in s:
            freq[w] = get(w, 0) + 1
    rk = {w: k for k, w in enumerate(sorted(freq, key=freq.__getitem__))}.__getitem__
    index = {}
    iget = index.get
    for xi, a in enumerate(keys):
        n = len(a)
        minm = (4 * n + 4) // 5
        if n < 5:
            w0 = min(a, key=rk)
            cands = iget(w0)
        else:
            toks = sorted(a, key=rk)
            w0 = toks[0]
            cands = set(iget(w0, ()))
            for w in toks[1:n - minm + 1]:
                lst = iget(w)
                if lst is not None:
                    cands.update(lst)
        if cands:
            for yi in cands:
                b = keys[yi]
                m = len(b)
                if m >= minm and 9 * len(a & b) >= 4 * (n + m):
                    if a in extra or b in extra:
                        for p in extra.get(a) or (last[a],):
                            for q in extra.get(b) or (last[b],):
                                append((p, q) if p < q else (q, p))
                    else:
                        p = last[a]; q = last[b]
                        append((p, q) if p < q else (q, p))
        if n < 9:
            if freq[w0] > 1:
                lst = iget(w0)
                if lst is None:
                    index[w0] = [xi]
                else:
                    lst.append(xi)
        else:
            for w in toks[:n - (8 * n + 8) // 9 + 1]:
                if freq[w] > 1:
                    lst = iget(w)
                    if lst is None:
                        index[w] = [xi]
                    else:
                        lst.append(xi)
    return pairs
