from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sets, range(len(sets))))
    last.pop(frozenset(), None)
    pairs = []
    groups = {}
    if len(last) < len(sets):
        for i, s in enumerate(sets):
            j = last.get(s)
            if j is not None and j != i:
                g = groups.get(s)
                if g is None:
                    groups[s] = [i, j]
                else:
                    g.insert(-1, i)
        for g in groups.values():
            pairs.extend([(g[a], g[b]) for a in range(len(g)) for b in range(a + 1, len(g))])
    uniq = sorted(last, key=len)
    # Common words tend to be seen first, so later-seen words rank as rarer.
    order = dict.fromkeys(chain.from_iterable(last))
    rk = dict(zip(order, range(len(order), 0, -1))).get
    index = {}
    iget = index.get
    for s in uniq:
        n = len(s)
        minsz = (4 * n + 4) // 5
        if n <= 4:
            t = min(map(rk, s))
            cands = iget(t)
            toks = (t,)
        else:
            toks = sorted(map(rk, s))
            p = n - minsz + 1
            cands = set()
            for t in toks[:p]:
                lst = iget(t)
                if lst:
                    cands.update(lst)
        if cands:
            for sy in cands:
                m = len(sy)
                if m >= minsz:
                    if 9 * len(s & sy) >= 4 * (n + m):
                        gx = groups.get(s)
                        gy = groups.get(sy)
                        if gx is None and gy is None:
                            i = last[s]
                            j = last[sy]
                            pairs.append((i, j) if i < j else (j, i))
                        else:
                            for i in gx or (last[s],):
                                for j in gy or (last[sy],):
                                    pairs.append((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [s]
            else:
                lst.append(s)
    return pairs
