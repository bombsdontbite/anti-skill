from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    n = len(sets)
    last = dict(zip(sets, range(n)))
    pairs = []
    groups = None
    if len(last) < n:
        # identical sets: group their indices
        groups = {}
        for i, j in enumerate(map(last.get, sets)):
            if i != j:
                g = groups.get(j)
                if g is None:
                    groups[j] = [i, j]
                else:
                    g.insert(-1, i)
        empty = last.get(frozenset())
        groups.pop(empty, None)
        for g in groups.values():
            k = len(g)
            pairs.extend([(g[x], g[y]) for x in range(k) for y in range(x + 1, k)])
    last.pop(frozenset(), None)
    # sets of up to 3 tokens only match an identical set
    big = [s for s in last if len(s) > 3]
    if len(big) < 2:
        return pairs
    big.sort(key=len)
    # common tokens tend to show up early, so late first sightings rank first
    seen = dict.fromkeys(chain.from_iterable(big))
    nt = len(seen)
    rk = dict(zip(seen, range(nt - 1, -1, -1))).get
    index = [None] * nt
    starts = [0] * nt
    sizes = [None] * nt
    found = []
    app = found.append
    u = 0
    for s in big:
        a = len(s)
        if a > 4:
            toks = sorted(map(rk, s))
            keep = a - (8 * a + 8) // 9 + 1
            minb = (4 * a + 4) // 5
            cands = set()
            k = 0
            for t in toks[:a - minb + 1]:
                lst = index[t]
                if lst is None:
                    if k < keep:
                        index[t] = [u]
                        sizes[t] = [a]
                else:
                    st = starts[t]
                    sz = sizes[t]
                    m = len(lst)
                    if st < m and sz[st] < minb:
                        while st < m and sz[st] < minb:
                            st += 1
                        starts[t] = st
                        cands.update(lst[st:])
                    elif st:
                        cands.update(lst[st:])
                    else:
                        cands.update(lst)
                    if k < keep:
                        lst.append(u)
                        sz.append(a)
                k += 1
            for v in cands:
                b = big[v]
                if 9 * len(s & b) >= 4 * (a + len(b)):
                    app((last[s], last[b]))
        else:
            t = min(map(rk, s))
            lst = index[t]
            if lst is None:
                index[t] = [u]
                sizes[t] = [a]
            else:
                lst.append(u)
                sizes[t].append(a)
        u += 1
    if groups is None:
        pairs.extend([(i, j) if i < j else (j, i) for i, j in found])
    else:
        for i, j in found:
            gu = groups.get(i) or (i,)
            gv = groups.get(j) or (j,)
            for x in gu:
                for y in gv:
                    pairs.append((x, y) if x < y else (y, x))
    return pairs
