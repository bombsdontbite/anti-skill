from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    first = dict(zip(reversed(sets), range(len(sets) - 1, -1, -1)))
    first.pop(frozenset(), None)
    pairs = []
    extra = {}
    if len(first) + (frozenset() in sets and sets.count(frozenset())) != len(sets):
        for i, s in enumerate(sets):
            if s:
                f = first[s]
                if f != i:
                    g = extra.get(f)
                    if g is None:
                        extra[f] = [f, i]
                    else:
                        g.append(i)
        for g in extra.values():
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    # Distinct sets of fewer than four tokens can never reach 0.8.
    big = [s for s in first if len(s) > 3]
    if len(big) < 2:
        return pairs
    # Rare tokens first. Late first appearance is a cheap proxy for rarity; with a small
    # vocabulary it is too coarse, so count instead.
    allt = list(chain.from_iterable(big))
    rank = dict(zip(reversed(allt), range(1 - len(allt), 1)))
    if 20 * len(rank) < len(allt):
        freq = {}
        fget = freq.get
        for t in allt:
            freq[t] = fget(t, 0) + 1
        rank = {t: k for k, t in enumerate(sorted(freq, key=fget))}
    get = rank.get
    big.sort(key=len)
    index = {}
    iget = index.get
    for s in big:
        n = len(s)
        if n == 4:
            t = min(map(get, s))
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
            continue
        m = (4 * n + 4) // 5
        toks = sorted(map(get, s))
        cands = None
        for t in toks[:n - m + 1]:
            lst = iget(t)
            if lst:
                if len(lst[0]) < m:
                    k = 1
                    while k < len(lst) and len(lst[k]) < m:
                        k += 1
                    del lst[:k]
                    if not lst:
                        continue
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
        if cands:
            need = 4 * n
            for b, inter in zip(cands, map(len, map(s.intersection, cands))):
                if 9 * inter >= need + 4 * len(b):
                    i = first[s]
                    j = first[b]
                    gi = extra.get(i)
                    gj = extra.get(j)
                    if gi is None and gj is None:
                        pairs.append((i, j) if i < j else (j, i))
                    else:
                        for i in gi or (i,):
                            for j in gj or (j,):
                                pairs.append((i, j) if i < j else (j, i))
        if n < 9:
            t = toks[0]
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
        else:
            for t in toks[:n - (8 * n + 8) // 9 + 1]:
                lst = iget(t)
                if lst is None:
                    index[t] = [s]
                else:
                    lst.append(s)
    return pairs
