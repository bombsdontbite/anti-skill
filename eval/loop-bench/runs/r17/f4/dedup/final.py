from itertools import chain, count, repeat


def near_duplicates(records):
    freq = {}
    fget = freq.get
    for t in chain.from_iterable(map(str.split, records[::16])):
        freq[t] = fget(t, 0) + 1
    ids = dict(zip(sorted(freq, key=freq.__getitem__), count()))
    sets = list(map(frozenset, map(map, repeat(ids.setdefault), map(str.split, records), repeat(count(-1, -1)))))
    pairs = []
    add = pairs.append
    first = dict(zip(sets, range(len(sets))))
    empty = frozenset()
    first.pop(empty, None)
    dups = {}
    if len(first) + sets.count(empty) < len(sets):
        for i, s in enumerate(sets):
            if s:
                f = first[s]
                if f != i:
                    g = dups.get(f)
                    if g is None:
                        dups[f] = [i, f]
                    else:
                        g.insert(-1, i)
        for g in dups.values():
            for x in range(1, len(g)):
                gx = g[x]
                for y in g[:x]:
                    add((y, gx))
    found = []
    hit = found.append
    keys = sorted(first, key=len)
    lens = list(map(len, keys))
    n = len(keys)
    lo = lens.count(1) + lens.count(2) + lens.count(3)
    bysize = {}
    big = {}
    bget = big.get
    while lo < n:
        a = lens[lo]
        hi = lo + lens.count(a)
        bucket = keys[lo:hi]
        lo = hi
        if a < 9:
            tl = list(map(sorted, bucket))
            prev = bysize.get(a - 1)
            if prev:
                pget = prev.get
                for s, toks in zip(bucket, tl):
                    l1 = pget(toks[0])
                    if l1 is not None:
                        for c in l1:
                            if c < s:
                                hit((s, c))
                    l2 = pget(toks[1])
                    if l2 is not None:
                        for c in l2:
                            if c < s:
                                hit((s, c))
            index = {}
            iget = index.get
            for s, toks in zip(bucket, tl):
                t = toks[0]
                lst = iget(t)
                if lst is None:
                    index[t] = [s]
                else:
                    lst.append(s)
            bysize[a] = index
        elif a < 14:
            tl = list(map(sorted, bucket))
            for b in range((4 * a + 4) // 5, a):
                prev = bysize.get(b)
                if prev:
                    pget = prev.get
                    m = a - b + 1
                    for s, toks in zip(bucket, tl):
                        for t in toks[:m]:
                            lst = pget(t)
                            if lst is not None:
                                for c in lst:
                                    if c < s:
                                        hit((s, c))
            same = {}
            sget = same.get
            index = {}
            iget = index.get
            am1 = a - 1
            for s, toks in zip(bucket, tl):
                t0 = toks[0]
                t1 = toks[1]
                l0 = sget(t0)
                l1 = sget(t1)
                if l0 is None:
                    same[t0] = [s]
                    if l1 is None:
                        same[t1] = [s]
                        cands = ()
                    else:
                        cands = l1[:]
                        l1.append(s)
                else:
                    if l1 is None:
                        cands = l0[:]
                        same[t1] = [s]
                    else:
                        cands = set(l0)
                        cands.update(l1)
                        l1.append(s)
                    l0.append(s)
                for c in cands:
                    if len(s & c) == am1:
                        hit((s, c))
                lst = iget(t0)
                if lst is None:
                    index[t0] = [s]
                else:
                    lst.append(s)
                if a > 11:
                    for t in toks[:2]:
                        lst = bget(t)
                        if lst is None:
                            big[t] = [s]
                        else:
                            lst.append(s)
            bysize[a] = index
        else:
            p = a - (4 * a + 4) // 5 + 1
            q = a - (8 * a + 8) // 9 + 1
            t4 = 4 * a
            minb = (t4 + 4) // 5
            for s in bucket:
                toks = sorted(s)[:p]
                cands = set()
                for k in range(p):
                    t = toks[k]
                    lst = bget(t)
                    if lst is None:
                        if k < q:
                            big[t] = [s]
                    else:
                        cands.update(lst)
                        if k < q:
                            lst.append(s)
                for c in cands:
                    b = len(c)
                    if b >= minb and 9 * len(s & c) >= t4 + 4 * b:
                        hit((s, c))
    if dups:
        for s, c in found:
            i = first[s]
            j = first[c]
            for x in dups.get(i) or (i,):
                for y in dups.get(j) or (j,):
                    add((x, y) if x < y else (y, x))
    else:
        for s, c in found:
            i = first[s]
            j = first[c]
            add((i, j) if i < j else (j, i))
    return pairs
