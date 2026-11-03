from collections import Counter
from itertools import chain


def near_duplicates(records):
    groups = {}
    add = groups.setdefault
    for i, s in enumerate(map(frozenset, map(str.split, records))):
        add(s, []).append(i)
    groups.pop(frozenset(), None)
    pairs = []
    for g in groups.values():
        if len(g) > 1:
            for x, gx in enumerate(g):
                for y in g[x + 1:]:
                    pairs.append((gx, y))
    sets = sorted(groups, key=len)
    freq = Counter(chain.from_iterable(sets))
    order = sorted(freq, key=freq.__getitem__)
    rankd = dict(zip(order, range(len(order))))
    rank = rankd.__getitem__
    # tokens ranked below `ones` occur in a single set and can never be shared
    ones = len(order) - sum(1 for _ in filter((1).__lt__, freq.values()))
    index = {}
    get = index.get
    for s in sets:
        n = len(s)
        if n < 5:
            t = min(s, key=rank)
            if rankd[t] < ones:
                continue
            lst = get(t)
            if lst is None:
                index[t] = [s]
                continue
            cands = lst
            minsz = (4 * n + 4) // 5
            lst.append(s)
        else:
            toks = sorted(s, key=rank)
            minsz = (4 * n + 4) // 5
            p = n - minsz + 1
            if rankd[toks[p - 1]] < ones:
                continue
            cands = None
            for t in toks[:p]:
                lst = get(t)
                if lst is not None:
                    if cands is None:
                        cands = set(lst)
                    else:
                        cands.update(lst)
            for t in toks[:n - (8 * n + 8) // 9 + 1]:
                lst = get(t)
                if lst is None:
                    index[t] = [s]
                else:
                    lst.append(s)
            if not cands:
                continue
        gk = None
        for o in cands:
            m = len(o)
            if m < minsz or o is s:
                continue
            inter = len(s & o)
            if 5 * inter >= 4 * (n + m - inter):
                if gk is None:
                    gk = groups[s]
                for b in groups[o]:
                    for a in gk:
                        pairs.append((a, b) if a < b else (b, a))
    return pairs
