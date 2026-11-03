from collections import Counter


def near_duplicates(records):
    groups = {}
    gget = groups.get
    for idx, r in enumerate(records):
        s = frozenset(r.split())
        g = gget(s)
        if g is None:
            groups[s] = [idx]
        else:
            g.append(idx)
    groups.pop(frozenset(), None)

    pairs = []
    for ids in groups.values():
        k = len(ids)
        if k > 1:
            for p in range(k):
                a = ids[p]
                for q in range(p + 1, k):
                    pairs.append((a, ids[q]))

    keys = sorted(groups, key=len)
    freq = Counter([t for s in keys for t in s])
    rank = {t: i for i, t in enumerate(sorted(freq, key=freq.get))}
    rget = rank.get

    index = {}
    iget = index.get
    sizes = []
    matched = []
    for xi, xs in enumerate(keys):
        n = len(xs)
        toks = sorted(xs, key=rget)
        minsize = (4 * n + 4) // 5
        cands = set()
        for t in toks[:n - minsize + 1]:
            lst = iget(t)
            if lst:
                cands.update(lst)
        for yi in cands:
            m = sizes[yi]
            if m >= minsize and 9 * len(xs & keys[yi]) >= 4 * (n + m):
                matched.append((yi, xi))
        sizes.append(n)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [xi]
            else:
                lst.append(xi)

    for yi, xi in matched:
        for a in groups[keys[yi]]:
            for b in groups[keys[xi]]:
                pairs.append((a, b) if a < b else (b, a))
    return pairs
