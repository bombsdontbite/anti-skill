from itertools import chain, combinations


def near_duplicates(records):
    groups = {}
    gget = groups.get
    for i, r in enumerate(records):
        s = frozenset(r.split())
        g = gget(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    # sets of 3 or fewer tokens only match identical sets
    keys = sorted([s for s in groups if len(s) > 3], key=len)
    # order: rare tokens by string, then tokens frequent in a sample by frequency
    freq = {}
    fget = freq.get
    for t in chain.from_iterable(keys[::8]):
        freq[t] = fget(t, 0) + 1
    common = sorted([t for t, c in freq.items() if c > 1], key=freq.get)
    rank = dict(zip(common, range(len(common))))
    rget = rank.get
    common = frozenset(common)
    top = len(keys[-1]) + 1 if keys else 1
    probe = [n + 1 - (4 * n + 4) // 5 for n in range(top)]
    store = [n + 1 - (8 * n + 8) // 9 for n in range(top)]
    index = {}
    iget = index.get
    for x, sx in enumerate(keys):
        n = len(sx)
        p = probe[n]
        pre = sorted(sx - common)
        if len(pre) < p:
            pre += sorted(sx & common, key=rget)
        if p == 1:
            l = iget(pre[0])
            if l is None:
                index[pre[0]] = [x]
                continue
            cands = l
        else:
            del pre[p:]
            lists = [l for l in map(iget, pre) if l]
            cands = set().union(*lists) if len(lists) > 1 else lists[0] if lists else ()
        if cands:
            minsize = n + 1 - p
            for y in cands:
                sy = keys[y]
                m = len(sy)
                if m >= minsize and 9 * len(sx & sy) >= 4 * (n + m):
                    for i in groups[sx]:
                        for j in groups[sy]:
                            pairs.append((i, j) if i < j else (j, i))
        if store[n] == 1:
            t = pre[0]
            l = iget(t)
            if l is None:
                index[t] = [x]
            else:
                l.append(x)
        else:
            for t in pre[:store[n]]:
                l = iget(t)
                if l is None:
                    index[t] = [x]
                else:
                    l.append(x)
    return pairs
