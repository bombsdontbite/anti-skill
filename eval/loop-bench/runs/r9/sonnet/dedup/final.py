from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    freq = Counter(chain.from_iterable(sets))
    rank = dict(zip(sorted(freq, key=freq.__getitem__), range(len(freq))))
    get = rank.__getitem__
    sizes = list(map(len, sets))
    order = sorted(range(len(sets)), key=sizes.__getitem__)
    index = {}
    out = []
    append = out.append
    for i in order:
        n = sizes[i]
        if not n:
            continue
        a = sets[i]
        lim = 4 * n
        cand = set()
        toks = sorted(map(get, a))
        for t in toks[:n - (lim + 4) // 5 + 1]:
            lst = index.get(t)
            if lst is not None:
                cand.update(lst)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            lst = index.get(t)
            if lst is None:
                index[t] = [i]
            else:
                lst.append(i)
        for j in cand:
            m = sizes[j]
            if 5 * m >= lim and 9 * len(a & sets[j]) >= 4 * (n + m):
                append((j, i) if j < i else (i, j))
    return out
