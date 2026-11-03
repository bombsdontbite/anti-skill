from itertools import chain


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
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in range(x + 1, len(g)):
                    pairs.append((gx, g[y]))
    uniq = sorted(groups, key=len)
    # Rare tokens go first. Tokens seen late are probably rare; tokens common in a
    # sample go last, so that a common token first seen late cannot flood the index.
    order = list(dict.fromkeys(chain.from_iterable(groups)))
    rank = dict(zip(order, range(len(order), 0, -1)))
    freq = {}
    fget = freq.get
    for s in uniq[::8]:
        for t in s:
            freq[t] = fget(t, 0) + 1
    if freq:
        floor = max(3, 4 * sum(freq.values()) // len(freq))
        step = len(order) + 1
        for t, c in freq.items():
            if c >= floor:
                rank[t] += c * step
    rget = rank.__getitem__
    sizes = list(map(len, uniq))
    lo = 0
    last = 0
    index = {}
    iget = index.get
    for k, s in enumerate(uniq):
        n = len(s)
        if n < 5:
            # Among distinct sets, one this small pairs only with a larger one.
            t = min(s, key=rget)
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
            continue
        toks = sorted(s, key=rget)
        minsz = (4 * n + 4) // 5
        if n != last:
            last = n
            while sizes[lo] < minsz:
                lo += 1
            kmin = lo
        cands = None
        for t in toks[:n - minsz + 1]:
            lst = iget(t)
            if lst is not None:
                if lst[0] < kmin:
                    i = 1
                    L = len(lst)
                    while i < L and lst[i] < kmin:
                        i += 1
                    if i == L:
                        del index[t]
                        continue
                    del lst[:i]
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
        if cands is not None:
            gk = groups[s]
            for c in cands:
                o = uniq[c]
                if 9 * len(s & o) >= 4 * (n + len(o)):
                    go = groups[o]
                    for a in gk:
                        for b in go:
                            pairs.append((a, b) if a < b else (b, a))
    return pairs
