from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = [set(r.split()) for r in records]
    freq = Counter(chain.from_iterable(sets))
    ranked = sorted(freq, key=freq.get)
    rget = dict(zip(ranked, range(len(ranked)))).get
    uniq = list(freq.values()).count(1)
    sizes = [len(a) for a in sets]
    top = max(sizes, default=0) + 1
    plen = [n - (-(-4 * n // 5)) + 1 for n in range(top)]
    ilen = [n - (-(-8 * n // 9)) + 1 for n in range(top)]
    index = [None] * len(ranked)
    pairs = []
    for x in sorted(range(len(sets)), key=lambda i: sizes[i]):
        n = sizes[x]
        if n < 5:
            if not n:
                continue
            a = sets[x]
            r = min(map(rget, a))
            if r < uniq:
                continue
            lst = index[r]
            if lst is None:
                index[r] = [x]
                continue
            lo = n - plen[n] + 1
            for y in lst:
                m = sizes[y]
                if m >= lo and 9 * len(a & sets[y]) >= 4 * (n + m):
                    pairs.append((y, x) if y < x else (x, y))
            lst.append(x)
            continue
        p = plen[n]
        toks = sorted(map(rget, sets[x]))
        if toks[p - 1] < uniq:
            continue
        lo = n - p + 1
        cands = None
        for r in toks[:p]:
            lst = index[r]
            if lst:
                if cands is None:
                    cands = set(lst)
                else:
                    cands.update(lst)
        if cands:
            a = sets[x]
            for y in cands:
                m = sizes[y]
                if m >= lo and 9 * len(a & sets[y]) >= 4 * (n + m):
                    pairs.append((y, x) if y < x else (x, y))
        for r in toks[:ilen[n]]:
            lst = index[r]
            if lst is None:
                index[r] = [x]
            else:
                lst.append(x)
    return pairs
