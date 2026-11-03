from collections import Counter
from itertools import chain


def near_duplicates(records):
    sets = list(map(frozenset, map(str.split, records)))
    last = dict(zip(sets, range(len(sets))))
    last.pop(frozenset(), None)
    pairs = []
    groups = {}
    dups = set(range(len(sets))).difference(last.values())
    if dups:
        for i in sorted(dups):
            s = sets[i]
            if s:
                g = groups.get(s)
                if g is None:
                    groups[s] = [i]
                else:
                    g.append(i)
        for s, g in groups.items():
            g.append(last[s])
            for a in range(len(g)):
                ga = g[a]
                for b in g[a + 1:]:
                    pairs.append((ga, b))
    uniq = [s for s in last if len(s) > 3]
    freq = Counter(chain.from_iterable(uniq))
    sh = len(freq).bit_length()
    rank = {t: (c << sh) | i for i, (t, c) in enumerate(freq.items())}
    ones = 2 << sh
    key = rank.__getitem__
    uniq.sort(key=len)
    index = {}
    for s in uniq:
        n = len(s)
        if n < 5:
            if n == 4:
                t = min(map(key, s))
                if t >= ones:
                    lst = index.get(t)
                    if lst is None:
                        index[t] = [s]
                    else:
                        lst.append(s)
            continue
        minlen = (4 * n + 4) // 5
        toks = sorted(map(key, s))
        p = n - minlen + 1
        if toks[p - 1] < ones:
            continue
        cands = set()
        for t in toks[:p]:
            if t >= ones:
                lst = index.get(t)
                if lst is not None:
                    cands.update(lst)
        for t in toks[:n - (8 * n + 8) // 9 + 1]:
            if t >= ones:
                lst = index.get(t)
                if lst is None:
                    index[t] = [s]
                else:
                    lst.append(s)
        if cands:
            mx = n if n < 9 else n + 1
            gs = groups.get(s) or (last[s],)
            for y in cands:
                m = len(y)
                if minlen <= m < mx:
                    inter = len(s & y)
                    if 5 * inter >= 4 * (n + m - inter):
                        for a in gs:
                            for b in groups.get(y) or (last[y],):
                                pairs.append((a, b) if a < b else (b, a))
    return pairs
