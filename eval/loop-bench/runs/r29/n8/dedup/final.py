from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    nrec = len(sets)
    # last write wins, so each distinct set maps to its first record
    first = dict(zip(reversed(sets), range(nrec - 1, -1, -1)))
    first.pop(frozenset(), None)
    pairs = []
    add = pairs.append
    members = {}
    if len(first) < nrec:
        for i, s in enumerate(sets):
            f = first.get(s)
            if f is not None and f != i:
                g = members.get(f)
                if g is None:
                    members[f] = [f, i]
                else:
                    g.append(i)
        for g in members.values():
            pairs.extend([(g[k], j) for k in range(len(g)) for j in g[k + 1:]])
    cnt = Counter(chain.from_iterable(first))
    rank = dict(zip(sorted(cnt, key=cnt.__getitem__), range(len(cnt))))
    key = rank.__getitem__
    mget = members.get
    index = {}
    get = index.get
    lens = list(map(len, sets))
    for x in sorted(first.values(), key=lens.__getitem__):
        a = sets[x]
        n = lens[x]
        toks = sorted(a, key=key)
        minsz = (4 * n + 4) // 5
        p = n - minsz + 1
        if p == 1:
            t = toks[0]
            seen = get(t)
            if seen is None:
                index[t] = [x]
                continue
        else:
            seen = set()
            for t in toks[:p]:
                lst = get(t)
                if lst:
                    seen.update(lst)
        for y in seen:
            m = lens[y]
            if m >= minsz and 9 * len(a & sets[y]) >= 4 * (n + m):
                gx = mget(x)
                gy = mget(y)
                if gx is None and gy is None:
                    add((x, y) if x < y else (y, x))
                else:
                    for i in gx or (x,):
                        for j in gy or (y,):
                            add((i, j) if i < j else (j, i))
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = get(t)
            if lst is None:
                index[t] = [x]
            else:
                lst.append(x)
    return pairs
