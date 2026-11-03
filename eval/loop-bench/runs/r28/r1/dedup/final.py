from itertools import chain


def near_duplicates(records):
    groups = {}
    setdefault = groups.setdefault
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        setdefault(s, []).append(i)
    groups.pop(frozenset(), None)
    pairs = []
    append = pairs.append
    for g in groups.values():
        n = len(g)
        if n > 1:
            for x in range(n):
                gx = g[x]
                for y in range(x + 1, n):
                    append((gx, g[y]))
    freq = {}
    fget = freq.get
    for t in chain.from_iterable(groups):
        freq[t] = fget(t, 0) + 1
    # rarest first; tokens seen in one set only get ranks below nsing
    rank = dict(zip(sorted(freq, key=fget), range(len(freq))))
    rget = rank.get
    nsing = list(freq.values()).count(1)
    index = {}
    iget = index.get
    for a in sorted(groups, key=len):
        la = len(a)
        minlen = (4 * la + 4) // 5
        p = la - minlen + 1
        if p == 1:
            t = min(map(rget, a))
            if t < nsing:
                continue
            lst = iget(t)
            if lst is None:
                index[t] = [a]
                continue
            cands = lst[:]
            lst.append(a)
        else:
            toks = sorted(map(rget, a))[:p]
            if toks[-1] < nsing:
                continue
            cands = set()
            for t in toks:
                if t >= nsing:
                    lst = iget(t)
                    if lst is None:
                        index[t] = [a]
                    else:
                        cands.update(lst)
                        lst.append(a)
        for b in cands:
            lb = len(b)
            if lb >= minlen:
                inter = len(a & b)
                if 5 * inter >= 4 * (la + lb - inter):
                    for i in groups[a]:
                        for j in groups[b]:
                            append((i, j) if i < j else (j, i))
    return pairs
