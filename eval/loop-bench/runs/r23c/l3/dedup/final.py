from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    seen = dict.fromkeys(chain.from_iterable(sets))
    rank = dict(zip(seen, range(len(seen), 0, -1)))
    key = rank.__getitem__
    pairs = []
    groups = None
    if len(set(sets)) == len(sets):
        ids = list(range(len(sets)))
    else:
        groups = {}
        ids = []
        for i, s in enumerate(sets):
            if not s:
                continue
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
                ids.append(i)
            else:
                for j in g:
                    pairs.append((j, i))
                g.append(i)
    lens = list(map(len, sets))
    ids.sort(key=lens.__getitem__)
    index = {}
    get = index.get
    for i in ids:
        n = lens[i]
        if n < 5:
            if n:
                t = min(sets[i], key=key)
                lst = get(t)
                if lst is None:
                    index[t] = [i]
                else:
                    lst.append(i)
            continue
        s = sets[i]
        tk = sorted(s, key=key)
        minlen = (4 * n + 4) // 5
        q = n - (8 * n + 8) // 9 + 1
        cands = set()
        for p, t in enumerate(tk[:n - minlen + 1]):
            lst = get(t)
            if lst:
                if lens[lst[0]] < minlen:
                    k = 1
                    while k < len(lst) and lens[lst[k]] < minlen:
                        k += 1
                    del lst[:k]
                cands.update(lst)
                if p < q:
                    lst.append(i)
            elif p < q:
                index[t] = [i]
        cands.discard(i)
        for j in cands:
            b = sets[j]
            inter = len(s & b)
            if 5 * inter >= 4 * (n + lens[j] - inter):
                if groups is None:
                    pairs.append((i, j) if i < j else (j, i))
                else:
                    for x in groups[s]:
                        for y in groups[b]:
                            pairs.append((x, y) if x < y else (y, x))
    return pairs
