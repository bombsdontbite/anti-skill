from bisect import bisect_left


def near_duplicates(records):
    groups = {}
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = groups.get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    add = pairs.append
    big = []
    gget = groups.get
    for s, g in groups.items():
        if len(g) > 1:
            pairs.extend([(a, b) for k, a in enumerate(g) for b in g[k + 1:]])
        n = len(s)
        if n < 5:
            continue
        if n >= 8:
            big.append(s)
            if n > 8:
                continue
        # 9|A&B| >= 4(|A|+|B|): for |A| <= 8 the only smaller match is A minus one word
        diff = s.difference
        for w in s:
            gt = gget(diff((w,)))
            if gt is not None:
                for a in g:
                    for b in gt:
                        add((a, b) if a < b else (b, a))
    if not big:
        return pairs
    big.sort(key=len)
    freq = {}
    fget = freq.get
    for s in big:
        for w in s:
            freq[w] = fget(w, 0) + 1
    # stable sort: ties keep insertion order, so this is one total order for every set
    order = sorted(freq, key=fget)
    rank = {w: k for k, w in enumerate(order)}
    get = rank.get
    # ranks below `single` belong to tokens of one set only; they can never match
    single = bisect_left([freq[w] for w in order], 2)
    sizes = list(map(len, big))
    # ids are in size order, so the size filter 5m >= 4n is a lower bound on the id
    index = {}
    for x, s in enumerate(big):
        n = sizes[x]
        minid = bisect_left(sizes, (4 * n + 4) // 5)
        toks = sorted(map(get, s))
        probe = n - (4 * n + 4) // 5 + 1
        lo = bisect_left(toks, single, 0, probe)
        if lo == probe:
            continue
        # an indexed set only needs its mid-prefix: overlap >= ceil(8n/9) against larger sets
        idx = n - (8 * n + 8) // 9 + 1
        cands = set()
        for w in toks[lo:idx]:
            lst = index.get(w)
            if lst is None:
                index[w] = [x]
            else:
                cands.update(lst[bisect_left(lst, minid):])
                lst.append(x)
        for w in toks[max(lo, idx):probe]:
            lst = index.get(w)
            if lst is not None:
                cands.update(lst[bisect_left(lst, minid):])
        for y in cands:
            t = big[y]
            m = sizes[y]
            inter = len(s & t)
            if 5 * inter >= 4 * (n + m - inter):
                gs, gt = groups[s], groups[t]
                for a in gs:
                    for b in gt:
                        add((a, b) if a < b else (b, a))
    return pairs
