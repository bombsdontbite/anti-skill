from itertools import chain, combinations


def near_duplicates(records):
    groups = {}
    get = groups.get
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        g = get(s)
        if g is None:
            groups[s] = [i]
        else:
            g.append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            pairs.extend(combinations(g, 2))
    uniq = [a for a in groups if len(a) > 3]
    uniq.sort(key=len)
    freq = {}
    fget = freq.get
    for t in chain.from_iterable(uniq):
        freq[t] = fget(t, 0) + 1
    order = sorted(freq, key=freq.get)
    rk = dict(zip(order, range(len(order)))).get
    hits = []
    hit = hits.append
    # Distinct sets of at most 8 tokens only pair with a subset one token smaller.
    small = {}
    sget = small.get
    big = {}
    bget = big.get
    for a in uniq:
        la = len(a)
        if la == 4:
            key = (min(a, key=rk), 4)
            lst = sget(key)
            if lst is None:
                small[key] = [a]
            else:
                lst.append(a)
            continue
        minlen = (4 * la + 4) // 5
        prefix = sorted(a, key=rk)[:la - minlen + 1]
        if la <= 8:
            cands = []
            for t in prefix:
                lst = sget((t, la - 1))
                if lst is not None:
                    cands += lst
            key = (prefix[0], la)
            lst = sget(key)
            if lst is None:
                small[key] = [a]
            else:
                lst.append(a)
            if cands:
                for b in set(cands) if len(cands) > 1 else cands:
                    if b < a:
                        hit((a, b))
            if la < 8:
                continue
        lists = []
        for t in prefix:
            lst = bget(t)
            if lst:
                if len(lst[0]) < minlen:
                    k = 1
                    n = len(lst)
                    while k < n and len(lst[k]) < minlen:
                        k += 1
                    del lst[:k]
                lists.append(lst)
        if lists and la > 8:
            need = 4 * la
            for b in (lists[0] if len(lists) == 1 else set(chain.from_iterable(lists))):
                if 9 * len(a & b) >= need + 4 * len(b):
                    hit((a, b))
        for t in prefix[:la - (8 * la + 8) // 9 + 1]:
            lst = bget(t)
            if lst is None:
                big[t] = [a]
            else:
                lst.append(a)
    app = pairs.append
    for a, b in hits:
        ga = groups[a]
        for j in groups[b]:
            for i in ga:
                app((i, j) if i < j else (j, i))
    return pairs
