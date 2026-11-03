from collections import Counter
from itertools import chain, combinations


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    N = len(sets)
    first = dict(zip(reversed(sets), range(N - 1, -1, -1)))
    pairs = []
    append = pairs.append
    dup = {}
    if len(first) != N:
        for i, s in enumerate(sets):
            f = first[s]
            if f != i:
                g = dup.get(f)
                if g is None:
                    dup[f] = [f, i]
                else:
                    g.append(i)
        e = first.pop(frozenset(), None)
        if e is not None:
            dup.pop(e, None)
        for g in dup.values():
            pairs.extend(combinations(g, 2))
    else:
        first.pop(frozenset(), None)
    uniq = sorted(first, key=len)
    freq = Counter(chain.from_iterable(uniq))
    order = sorted(freq, key=freq.__getitem__)
    U = Counter(freq.values())[1]
    rg = dict(zip(order, range(len(order)))).__getitem__
    index = {}
    get = index.get
    for s in uniq:
        n = len(s)
        if n < 5:
            t = min(map(rg, s))
            if t < U:
                continue
            l = get(t)
            if l is None:
                index[t] = [s]
                continue
            cands = l[:]
            l.append(s)
            minlen = n if n > 1 else 1
        else:
            minlen = (4 * n + 4) // 5
            p = n - minlen + 1
            lst = sorted(map(rg, s))
            if lst[p - 1] < U:
                continue
            cands = set()
            for t in lst[:p]:
                if t < U:
                    continue
                l = get(t)
                if l is None:
                    index[t] = [s]
                else:
                    cands.update(l)
                    l.append(s)
        i = first[s]
        for b in cands:
            m = len(b)
            if m < minlen:
                continue
            inter = len(s & b)
            if 5 * inter >= 4 * (n + m - inter):
                j = first[b]
                if dup and (i in dup or j in dup):
                    for x in dup.get(i, (i,)):
                        for y in dup.get(j, (j,)):
                            append((x, y) if x < y else (y, x))
                else:
                    append((j, i) if j < i else (i, j))
    return pairs
