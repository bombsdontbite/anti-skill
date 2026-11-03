def near_duplicates(records):
    groups = {}
    gg = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = gg(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    keys = sorted(groups, key=len)
    gl = [groups[k] for k in keys]
    for g in gl:
        if len(g) > 1:
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    freq = {}
    fg = freq.get
    for k in keys:
        for t in k:
            freq[t] = fg(t, 0) + 1
    order = sorted(freq, key=fg)
    rank = {t: r for r, t in enumerate(order)}
    rg = rank.get
    # tokens ranked below n1 occur in a single key and can never produce a candidate
    n1 = 0
    for t in order:
        if freq[t] > 1:
            break
        n1 += 1
    index = {}
    ig = index.get
    sizes = [len(k) for k in keys]
    top = sizes[-1] + 1 if sizes else 1
    minsz = [(4 * n + 4) // 5 for n in range(top)]
    plen = [n - minsz[n] + 1 for n in range(top)]
    qlen = [n - (8 * n + 8) // 9 + 1 for n in range(top)]
    masks = [0] * len(keys)
    # bit masks pay off for large sets, as long as the shared-token vocabulary keeps them short
    big = 12 if len(order) - n1 <= 8192 else top + 1
    hi = len(order) - 1
    for x, k in enumerate(keys):
        n = sizes[x]
        if n < 5:
            # earlier keys are no larger, and distinct sets of at most 4 tokens never reach 0.8
            t = min(map(rg, k))
            if t >= n1:
                lst = ig(t)
                if lst is None:
                    index[t] = [x]
                else:
                    lst.append(x)
            continue
        else:
            ranks = sorted(map(rg, k))
            if n >= big:
                mask = 0
                for t in ranks:
                    if t >= n1:
                        mask |= 1 << (hi - t)
                masks[x] = mask
            p = plen[n]
            if ranks[p - 1] < n1:
                continue
            q = qlen[n]
            cands = None
            for pos in range(p):
                t = ranks[pos]
                if t < n1:
                    continue
                lst = ig(t)
                if lst is None:
                    if pos < q:
                        index[t] = [x]
                else:
                    if cands is None:
                        cands = set(lst)
                    else:
                        cands.update(lst)
                    if pos < q:
                        lst.append(x)
        if cands is None:
            continue
        minsize = minsz[n]
        if minsize >= big:
            for y in cands:
                m = sizes[y]
                if m < minsize:
                    continue
                inter = (mask & masks[y]).bit_count()
                if 5 * inter >= 4 * (n + m - inter):
                    gy = gl[y]
                    for i in gl[x]:
                        for j in gy:
                            pairs.append((i, j) if i < j else (j, i))
            continue
        for y in cands:
            m = sizes[y]
            if m < minsize:
                continue
            inter = len(k & keys[y])
            if 5 * inter >= 4 * (n + m - inter):
                gy = gl[y]
                for i in gl[x]:
                    for j in gy:
                        pairs.append((i, j) if i < j else (j, i))
    return pairs
