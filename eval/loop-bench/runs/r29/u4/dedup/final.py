def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    first = dict(zip(sets, range(len(sets))))
    pairs = []
    groups = {}
    if len(first) < len(sets):
        for i in sorted(set(range(len(sets))).difference(first.values())):
            s = sets[i]
            if s:
                g = groups.get(s)
                if g is None:
                    groups[s] = [first[s], i]
                else:
                    g.append(i)
        for g in groups.values():
            g.sort()
            pairs.extend((a, b) for k, a in enumerate(g) for b in g[k + 1:])
    first.pop(frozenset(), None)
    uniq = list(first)
    if len(uniq) < 2:
        return pairs

    alltok = set().union(*uniq)
    rank = dict(zip(alltok, range(len(alltok))))
    big = len(alltok)
    for fs in uniq[::4]:
        for t in fs:
            rank[t] += big
    rget = rank.get
    uniq.sort(key=len)
    sizes = list(map(len, uniq))
    index = {}
    found = []
    lo = 0
    minsize = 0
    for x, fs in enumerate(uniq):
        s = sizes[x]
        toks = sorted(map(rget, fs))
        m = (4 * s + 4) // 5
        if m != minsize:
            minsize = m
            while sizes[lo] < m:
                lo += 1
        cands = set()
        for t in toks[:s - m + 1]:
            lst = index.get(t)
            if lst:
                if lst[0] < lo:
                    k = 1
                    n = len(lst)
                    while k < n and lst[k] < lo:
                        k += 1
                    del lst[:k]
                cands.update(lst)
        for y in cands:
            inter = len(fs & uniq[y])
            if 5 * inter >= 4 * (s + sizes[y] - inter):
                found.append((y, x))
        for t in toks[:s - (8 * s + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    if groups:
        for y, x in found:
            fy = uniq[y]
            fx = uniq[x]
            for a in groups.get(fy) or (first[fy],):
                for b in groups.get(fx) or (first[fx],):
                    pairs.append((a, b) if a < b else (b, a))
    else:
        for y, x in found:
            a = first[uniq[y]]
            b = first[uniq[x]]
            pairs.append((a, b) if a < b else (b, a))
    return pairs
