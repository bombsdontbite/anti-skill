def near_duplicates(records):
    allsets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(allsets, range(len(allsets))))
    last.pop(frozenset(), None)
    pairs = []
    extra = {}
    if len(last) < len(allsets):
        lget = last.get
        for i in [i for i, s in enumerate(allsets) if lget(s, i) != i]:
            s = allsets[i]
            g = extra.get(s)
            if g is None:
                extra[s] = [i]
            else:
                g.append(i)
        for s, g in extra.items():
            g.append(last[s])
            pairs.extend((g[x], g[y]) for x in range(len(g)) for y in range(x + 1, len(g)))
    sets = sorted(last, key=len)
    sizes = [5 * len(s) for s in sets]
    freq = {}
    fget = freq.get
    for s in sets[::3]:
        for t in s:
            freq[t] = fget(t, 0) + 1
    order = list(set().union(*sets) - freq.keys())
    order += sorted(freq, key=fget)
    rget = dict(zip(order, range(len(order)))).get
    index = {}
    iget = index.get
    k = -1
    for s in sets:
        k += 1
        n = len(s)
        lim = 4 * n
        if n < 5:
            t = min(s, key=rget)
            lst = iget(t)
            if lst is None:
                index[t] = [k]
                continue
            if sizes[lst[0]] < lim:
                j = 1
                while j < len(lst) and sizes[lst[j]] < lim:
                    j += 1
                del lst[:j]
            cand = lst
        else:
            tk = sorted(s, key=rget)
            cand = set()
            for t in tk[:n - (4 * n + 4) // 5 + 1]:
                lst = iget(t)
                if lst:
                    if sizes[lst[0]] < lim:
                        j = 1
                        while j < len(lst) and sizes[lst[j]] < lim:
                            j += 1
                        del lst[:j]
                    cand.update(lst)
        for m in cand:
            b = sets[m]
            inter = len(s & b)
            if 5 * inter >= 4 * (n + len(b) - inter):
                if extra and (s in extra or b in extra):
                    ga = extra[s] if s in extra else [last[s]]
                    gb = extra[b] if b in extra else [last[b]]
                    for i in ga:
                        for j in gb:
                            pairs.append((i, j) if i < j else (j, i))
                else:
                    i = last[s]
                    j = last[b]
                    pairs.append((i, j) if i < j else (j, i))
        if n < 5:
            cand.append(k)
            continue
        for t in tk[:n - (8 * n + 8) // 9 + 1]:
            lst = iget(t)
            if lst is None:
                index[t] = [k]
            else:
                lst.append(k)
    return pairs
