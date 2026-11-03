from bisect import bisect_left


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    where = dict(zip(sets, range(len(sets))))
    empty = frozenset()
    where.pop(empty, None)
    pairs = []
    multi = {}
    if len(where) < len(sets) - sets.count(empty):
        for idx, s in enumerate(sets):
            if s and where[s] != idx:
                g = multi.get(s)
                if g is None:
                    multi[s] = [idx]
                else:
                    g.append(idx)
        for s, g in multi.items():
            g.append(where[s])
            g.sort()
            for a in range(len(g)):
                for b in range(a + 1, len(g)):
                    pairs.append((g[a], g[b]))
    keys = sorted(where, key=len)
    freq = {}
    get = freq.get
    for s in keys:
        for t in s:
            freq[t] = get(t, 0) + 1
    # Order by frequency, ties by first appearance; a token seen once ranks below S.
    v = len(freq)
    rank = {t: c * v + i for i, (t, c) in enumerate(freq.items())}
    S = 2 * v
    rget = rank.get
    plan = {}
    # A set of size m sits under (t, m, c) for every partner prefix length c covering t.
    spots = {}
    index = {}
    setd = index.setdefault
    look = index.get
    for s in keys:
        n = len(s)
        p = plan.get(n)
        if p is None:
            p = []
            for m in range((4 * n + 4) // 5, n + 1):
                a = (4 * (n + m) + 8) // 9
                if a < m or (a == m and m < n):
                    p.append((m, n - a + 1, m - a + 1))
            cs = set()
            for k in range(n, (5 * n) // 4 + 1):
                a = (4 * (n + k) + 8) // 9
                if a < n or (a == n and n < k):
                    cs.add(n - a + 1)
            plan[n] = p
            spots[n] = cs = sorted(cs)
            width = n - (4 * n + 4) // 5 + 1
        rs = sorted(map(rget, s))
        if rs[width - 1] < S:
            continue
        single = bisect_left(rs, S, 0, width)
        cand = None
        for m, pp, pc in p:
            if pp <= single:
                continue
            for t in rs[single:pp]:
                lst = look((t, m, pc))
                if lst is not None:
                    if cand is None:
                        cand = set(lst)
                    else:
                        cand.update(lst)
        cs = spots[n]
        for j in range(single, width):
            t = rs[j]
            for c in cs:
                if c > j:
                    setd((t, n, c), []).append(s)
        if cand:
            for o in cand:
                inter = len(s & o)
                if 9 * inter >= 4 * (n + len(o)):
                    if multi and (s in multi or o in multi):
                        for i in multi.get(o) or (where[o],):
                            for j in multi.get(s) or (where[s],):
                                pairs.append((i, j) if i < j else (j, i))
                    else:
                        i = where[o]
                        j = where[s]
                        pairs.append((i, j) if i < j else (j, i))
    return pairs
