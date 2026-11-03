from bisect import bisect_left
from collections import Counter
from itertools import chain


def near_duplicates(records):
    lists = list(map(str.split, records))
    freq = Counter(chain.from_iterable(lists))
    # any fixed total order on tokens is correct; rare-first keeps the prefixes selective
    key = dict(zip(sorted(freq, key=freq.__getitem__), range(len(freq)))).__getitem__
    groups = {}
    for i, l in enumerate(lists):
        if l:
            s = frozenset(map(key, l))
            g = groups.get(s)
            if g is None:
                groups[s] = [i]
            else:
                g.append(i)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x in range(len(g)):
                gx = g[x]
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    # distinct sets of up to 3 tokens are never 80 % alike with anything
    sets = sorted([s for s in groups if len(s) > 3], key=len)
    n = len(sets)
    if n < 2:
        return pairs
    lens = list(map(len, sets))
    index = {}
    get = index.get
    k = 0
    while k < n:
        a = lens[k]
        end = bisect_left(lens, a + 1, k)
        p = a - (4 * a + 4) // 5 + 1
        q = a - (8 * a + 8) // 9 + 1
        lo = bisect_left(lens, (4 * a + 4) // 5, 0, k)
        m = 4 * a
        for k in range(k, end):
            s = sets[k]
            toks = sorted(s)
            cands = set()
            for t in toks[:q]:
                lst = get(t)
                if lst is None:
                    index[t] = [k]
                else:
                    cands.update(lst[bisect_left(lst, lo):] if lst[0] < lo else lst)
                    lst.append(k)
            for t in toks[q:p]:
                lst = get(t)
                if lst is not None:
                    cands.update(lst[bisect_left(lst, lo):] if lst[0] < lo else lst)
            for c in cands:
                b = sets[c]
                if 9 * len(s & b) >= m + 4 * len(b):
                    gk = groups[s]
                    for j in groups[b]:
                        for i in gk:
                            pairs.append((i, j) if i < j else (j, i))
        k = end
    return pairs
