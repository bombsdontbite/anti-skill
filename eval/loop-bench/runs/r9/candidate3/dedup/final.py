from bisect import bisect_left, bisect_right


def near_duplicates(records):
    groups = {}
    for i, r in enumerate(records):
        s = frozenset(r.split())
        if s:
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    for g in groups.values():
        k = len(g)
        if k > 1:
            for a in range(k):
                ga = g[a]
                for b in range(a + 1, k):
                    pairs.append((ga, g[b]))
    if len(groups) < 2:
        return pairs
    sets = sorted(groups, key=len)
    sizes = list(map(len, sets))
    m = len(sets)
    if m * m <= 2 * sum(sizes):
        # few distinct sets for their total size: pairwise beats building an index
        for x in range(m):
            sx = sets[x]
            n = sizes[x]
            ls = (4 * n + 4) // 5
            for y in range(bisect_left(sizes, ls), x):
                sy = sets[y]
                if 9 * len(sx & sy) >= 4 * (n + sizes[y]):
                    for i in groups[sx]:
                        for j in groups[sy]:
                            pairs.append((i, j) if i < j else (j, i))
        return pairs
    freq = {}
    get = freq.get
    for s in sets:
        for t in s:
            freq[t] = get(t, 0) + 1
    rank = {t: r for r, t in enumerate(sorted(freq, key=get))}
    key = rank.get
    # index[t][j] = (sizes, sets) of the sets whose j-th token in rank order is t, by size
    index = [None] * len(rank)
    for sx in sets:
        n = len(sx)
        srt = sorted(map(key, sx))
        cands = set()
        for i in range(n - (4 * n + 4) // 5 + 1):
            lj = index[srt[i]]
            if lj is None:
                continue
            hs = (5 * n - 9 * i) // 4
            for j, e in lj.items():
                szl = e[0]
                ls = (4 * n + 9 * j + 4) // 5
                if szl[-1] >= ls and szl[0] <= hs:
                    cands.update(e[1][bisect_left(szl, ls):bisect_right(szl, hs)])
        for j in range(n - (8 * n + 8) // 9 + 1):
            t = srt[j]
            lj = index[t]
            if lj is None:
                index[t] = {j: ([n], [sx])}
                continue
            e = lj.get(j)
            if e is None:
                lj[j] = ([n], [sx])
            else:
                e[0].append(n)
                e[1].append(sx)
        if cands:
            gx = groups[sx]
            for sy in cands:
                if 9 * len(sx & sy) >= 4 * (n + len(sy)):
                    gy = groups[sy]
                    for i in gx:
                        for j in gy:
                            pairs.append((i, j) if i < j else (j, i))
    return pairs
